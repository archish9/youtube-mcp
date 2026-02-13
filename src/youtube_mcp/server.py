import os
import sys
import json
from typing import Any
from datetime import datetime, timedelta
from pathlib import Path
import isodate
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, 
    NoTranscriptFound,
    VideoUnavailable
)
from dotenv import load_dotenv

# Try to load environment variables from multiple locations
def load_env_file():
    """Try to load .env from various possible locations"""
    possible_paths = [
        Path.cwd() / ".env",  # Current working directory
        Path(__file__).parent.parent.parent / ".env",  # Project root
        Path(__file__).parent / ".env",  # Same directory as server.py
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return True
    
    # Fallback: just try to load from cwd
    load_dotenv()
    return False

load_env_file()

# YouTube API client (initialized lazily)
_youtube_client = None

def get_youtube_client():
    """Get or create YouTube API client"""
    global _youtube_client
    if _youtube_client is None:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError(
                "YOUTUBE_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        _youtube_client = build('youtube', 'v3', developerKey=api_key)
    return _youtube_client

# Create MCP server
server = Server("youtube-mcp")

def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from YouTube URL or return ID if already provided"""
    if "youtube.com" in url_or_id or "youtu.be" in url_or_id:
        if "youtu.be/" in url_or_id:
            return url_or_id.split("youtu.be/")[1].split("?")[0]
        elif "watch?v=" in url_or_id:
            return url_or_id.split("watch?v=")[1].split("&")[0]
    return url_or_id

def format_duration(duration: str) -> str:
    """Convert ISO 8601 duration to readable format"""
    try:
        parsed = isodate.parse_duration(duration)
        total_seconds = int(parsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return duration

def format_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)

# --- Video Analytics Helper ---
async def _get_video_data(video_id: str):
    """Fetch current video data for analytics"""
    try:
        request = get_youtube_client().videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        )
        response = request.execute()
        
        if not response.get("items"):
            return None
        
        video = response["items"][0]
        stats = video.get("statistics", {})
        snippet = video["snippet"]
        
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        
        # Calculate engagement metrics
        like_rate = (likes / views * 100) if views > 0 else 0
        comment_rate = (comments / views * 100) if views > 0 else 0
        
        # New weighted score: Likes are more common, so we weight them but scale them
        # 2% like rate + 0.1% comment rate should be a "Good" result (~60-70)
        engagement_score = (like_rate * 20) + (comment_rate * 100)
        
        return {
            "video_id": video_id,
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "channel_id": snippet["channelId"],
            "published_at": snippet["publishedAt"],
            "duration": video["contentDetails"]["duration"],
            "views": views,
            "views_formatted": format_number(views),
            "likes": likes,
            "likes_formatted": format_number(likes),
            "comments": comments,
            "comments_formatted": format_number(comments),
            "like_rate": round(like_rate, 2),
            "comment_rate": round(comment_rate, 3),
            "engagement_score": round(engagement_score, 2),
            "thumbnail": snippet["thumbnails"]["high"]["url"],
            "url": f"https://youtube.com/watch?v={video_id}"
        }
    except Exception as e:
        return None

def _calculate_performance_rating(like_rate: float, comment_rate: float) -> dict:
    """Calculate performance rating based on engagement"""
    if like_rate >= 5:
        like_rating = "Excellent"
    elif like_rate >= 3:
        like_rating = "Good"
    elif like_rate >= 1:
        like_rating = "Average"
    else:
        like_rating = "Below Average"
    
    if comment_rate >= 0.5:
        comment_rating = "High Engagement"
    elif comment_rate >= 0.1:
        comment_rating = "Moderate Engagement"
    else:
        comment_rating = "Low Engagement"
    
    return {
        "like_rating": like_rating,
        "comment_rating": comment_rating
    }
# -----------------------------


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available YouTube tools."""
    return [
        types.Tool(
            name="get_video_info",
            description=(
                "Retrieves comprehensive metadata for a specific YouTube video.\n"
                "Use this tool when you need details like title, description, view count, like count, comment count, "
                "duration, publication date, channel information, and tags.\n"
                "Returns a JSON object containing the video's snippet, statistics, and content details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "The unique YouTube video ID (e.g., 'dQw4w9WgXcQ') or the full YouTube URL (e.g., 'https://youtube.com/watch?v=dQw4w9WgXcQ')."
                    }
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_video_transcript",
            description=(
                "Fetches the full transcript/captions for a YouTube video.\n"
                "Use this tool to read the spoken content of a video for summarization, analysis, or information extraction.\n"
                "Returns a list of transcript segments, each with a timestamp (start time), duration, and text.\n"
                "Note: Returns an error if transcripts are disabled or not available in the requested language."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "The unique YouTube video ID or full URL."
                    },
                    "language": {
                        "type": "string",
                        "description": "The preferred ISO 639-1 language code for the transcript (e.g., 'en' for English, 'es' for Spanish, 'fr' for French). Defaults to 'en'.",
                        "default": "en"
                    }
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_video_comments",
            description=(
                "Retrieves top-level comments for a specific YouTube video.\n"
                "Use this tool to analyze audience sentiment, gather feedback, or see what viewers are discussing.\n"
                "Returns a list of comments with author name, text, like count, published date, and reply count.\n"
                "Can retrieve comments sorted by relevance (default) or date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "The unique YouTube video ID or full URL."
                    },
                    "max_results": {
                        "type": "number",
                        "description": "The maximum number of comments to retrieve. Accepts values between 1 and 100. Defaults to 20.",
                        "default": 20
                    },
                    "order": {
                        "type": "string",
                        "description": "The order to sort comments by. Options: 'relevance' (top comments) or 'time' (newest first). Defaults to 'relevance'.",
                        "enum": ["time", "relevance"],
                        "default": "relevance"
                    }
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="search_videos",
            description=(
                "Searches for YouTube videos matching a specific query.\n"
                "Use this tool to find videos on a topic, by a specific creator, or matching keywords.\n"
                "Returns a list of matching videos including video ID, title, description, channel name, and publication date.\n"
                "Supports sorting by relevance, date, view count, and rating."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (keywords, topic, or channel name)."
                    },
                    "max_results": {
                        "type": "number",
                        "description": "The maximum number of search results to return. Accepts values between 1 and 50. Defaults to 10.",
                        "default": 10
                    },
                    "order": {
                        "type": "string",
                        "description": "The criteria to sort search results by. Options: 'date' (newest), 'rating' (highest rated), 'relevance' (default), 'title' (alphabetical), 'viewCount' (most viewed).",
                        "enum": ["date", "rating", "relevance", "title", "viewCount"],
                        "default": "relevance"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_channel_info",
            description=(
                "Retrieves detailed information about a YouTube channel.\n"
                "Use this tool to get channel statistics (subscribers, total views, video count), description, branding details, and uploads playlist ID.\n"
                "This is useful for analyzing a creator's profile and reach."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The YouTube channel ID (e.g., 'UC_x5XG1OV2P6uZZ5FSM9Ttw') or channel URL (e.g., 'https://youtube.com/channel/...'). handles @username URLs if possible."
                    }
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="get_channel_videos",
            description=(
                "Retrieves a list of videos uploaded by a specific YouTube channel.\n"
                "Use this tool to see a channel's recent content or most popular videos.\n"
                "Returns video details including ID, title, description, and publication date.\n"
                "Supports sorting by date (default), view count, and rating."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The YouTube channel ID."
                    },
                    "max_results": {
                        "type": "number",
                        "description": "The maximum number of videos to retrieve. Accepts values between 1 and 50. Defaults to 10.",
                        "default": 10
                    },
                    "order": {
                        "type": "string",
                        "description": "The order to sort videos by. Options: 'date' (newest), 'rating', 'relevance', 'title', 'videoCount' (for channels), 'viewCount'. Defaults to 'date'.",
                        "enum": ["date", "rating", "relevance", "title", "videoCount", "viewCount"],
                        "default": "date"
                    }
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="get_trending_videos",
            description=(
                "Retrieves a list of currently trending videos in a specific region.\n"
                "Use this tool to discover popular content and current trends on YouTube.\n"
                "Can be filtered by specific video categories (e.g., Music, Gaming, News).\n"
                "Returns video metadata and statistics for the top trending videos."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "The ISO 3166-1 alpha-2 country code for the region (e.g., 'US', 'GB', 'IN', 'JP'). Defaults to 'US'.",
                        "default": "US"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "The video category ID to filter by (e.g., '10' for Music, '20' for Gaming). Defaults to '0' (all categories).",
                        "default": "0"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "The maximum number of trending videos to retrieve. Accepts values between 1 and 50. Defaults to 10.",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_playlist_info",
            description=(
                "Retrieves information about a YouTube playlist and the videos within it.\n"
                "Use this tool to get details about a playlist (title, description, channel) and a list of its video items.\n"
                "Useful for processing curated lists of videos or series."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "The YouTube playlist ID."
                    },
                    "max_results": {
                        "type": "number",
                        "description": "The maximum number of playlist items to retrieve. Accepts values between 1 and 50. Defaults to 20.",
                        "default": 20
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        types.Tool(
            name="get_video_analytics",
            description=(
                "Calculates detailed engagement metrics for a specific video.\n"
                "Use this tool to get a deeper analysis than standard metadata. Returns views, likes, comments, "
                "plus calculated 'like rate' (likes/views) and 'comment rate' (comments/views).\n"
                "Also provides a weighted 'engagement score' to evaluate overall performance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="analyze_video_engagement",
            description=(
                "Analyzes the quality of audience engagement for a video.\n"
                "Use this tool to interpret engagement metrics. It classifies engagement as 'Excellent', 'Good', "
                "'Average', etc., based on industry benchmarks for like-to-view and comment-to-view ratios.\n"
                "Returns a qualitative interpretation of quantitative metrics."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_video_performance_score",
            description=(
                "Calculates a comprehensive performance score (0-100) and letter grade (A-F) for a video.\n"
                "Use this tool for a high-level summary of how well a video is performing relative to engagement benchmarks.\n"
                "Returns the score, grade, summary text, and the underlying metrics used for calculation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="compare_videos",
            description=(
                "Compares up to 10 videos side-by-side on key performance metrics.\n"
                "Use this tool to benchmark videos against each other. It ranks them by engagement score and highlights "
                "the best performer in views, engagement, and like rate.\n"
                "Returns a comparative table and highlights."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of video IDs or URLs to compare (minimum 2, maximum 10)."
                    }
                },
                "required": ["video_ids"]
            }
        ),
        types.Tool(
            name="analyze_video_potential",
            description=(
                "Analyzes a video's potential and content quality signals.\n"
                "Use this tool to identify strengths (e.g., 'Viral reach', 'High retention signals') and weaknesses "
                "(e.g., 'Low interaction').\n"
                "Returns a list of positive quality signals, areas for improvement, and an overall assessment."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="compare_channels",
            description=(
                "Compares up to 5 YouTube channels side-by-side.\n"
                "Use this tool to benchmark creators. Comparies subscribers, total views, video count, and average views per video.\n"
                "Returns a dataset suitable for competitive analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of channel IDs to compare (minimum 2, maximum 5)."
                    }
                },
                "required": ["channel_ids"]
            }
        ),
        types.Tool(
            name="analyze_content_strategy",
            description=(
                "Analyzes a channel's posting habits and content strategy.\n"
                "Use this tool to determine how frequently a channel uploads (e.g., 'Daily', 'Weekly') and consistency.\n"
                "Returns calculated metrics on posting frequency, estimated videos per month, and average views."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "The YouTube channel ID."}
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="benchmark_performance",
            description=(
                "Benchmarks a target channel against a set of competitors.\n"
                "Use this tool to see where a channel stands in its niche. Ranks the target channel by subscribers "
                "and engagement against the provided competitors.\n"
                "Returns the target's rank and comparative data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "target_channel_id": {"type": "string", "description": "The ID of the channel to benchmark."},
                    "competitor_channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of competitor channel IDs to compare against."
                    }
                },
                "required": ["target_channel_id", "competitor_channel_ids"]
            }
        ),
        types.Tool(
            name="identify_competitive_advantages",
            description=(
                "Identifies relative strengths and weaknesses of a channel compared to competitors.\n"
                "Use this tool to find unique selling points (e.g., 'Strong view-to-subscriber ratio') or gaps.\n"
                "Returns a list of advantages and weaknesses based on statistical comparison."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "The ID of the channel to analyze."},
                    "comparison_channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of channel IDs to compare against."
                    }
                },
                "required": ["channel_id", "comparison_channel_ids"]
            }
        ),
        types.Tool(
            name="track_market_share",
            description=(
                "Calculates the 'market share' of viewership and subscribers among a group of channels.\n"
                "Use this tool to see dominance within a specific niche. Shows what percentage of total views/subs "
                "each channel owns within the provided group.\n"
                "Returns percentage shares for each channel."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of YouTube channel IDs representing the 'market'."
                    }
                },
                "required": ["channel_ids"]
            }
        ),
        # --- Report Generation Tools ---
        types.Tool(
            name="generate_channel_report",
            description=(
                "Generates a comprehensive performance report for a YouTube channel over a specific period.\n"
                "Use this tool to create a summary of channel activity. Includes aggregate metrics (total views, likes), "
                "top performing videos, and individual video details for the period.\n"
                "Returns a structured report suitable for presentation or analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "The YouTube channel ID."},
                    "period_days": {
                        "type": "number",
                        "description": "The number of days to look back (e.g., 7 for weekly, 30 for monthly). Defaults to 7.",
                        "default": 7
                    },
                    "include_videos": {
                        "type": "boolean",
                        "description": "Whether to include detailed data for each video in the report. Defaults to True.",
                        "default": True
                    }
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="generate_video_report",
            description=(
                "Generates a detailed deep-dive report for a specific video.\n"
                "Use this tool for an in-depth look at a single video. Includes all metadata, engagement analysis, "
                "performance scoring, quality signals, and improvement suggestions.\n"
                "Returns a complete profile of the video's performance."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."}
                },
                "required": ["video_id"]
            }
        ),
        # --- New Tools ---
        types.Tool(
            name="get_related_videos",
            description=(
                "Retrieves a list of videos matching or related to a specific video.\n"
                "Use this tool to find what YouTube recommends next to a given video, useful for understanding content clusters.\n"
                "Returns a list of related video summaries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."},
                    "max_results": {"type": "number", "default": 10, "description": "Maximum number of related videos to return (1-50)."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_channel_playlists",
            description=(
                "Retrieves a list of playlists created by a specific channel.\n"
                "Use this tool to explore how a channel organizes its content.\n"
                "Returns playlist details including ID, title, and description."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "The YouTube channel ID."},
                    "max_results": {"type": "number", "default": 10, "description": "Maximum number of playlists to return (1-50)."}
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="search_channels",
            description=(
                "Searches for YouTube channels matching a query.\n"
                "Use this tool to find creators by name or topic.\n"
                "Returns a list of matching channels with subscriber counts and video counts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query (channel name or topic)."},
                    "max_results": {"type": "number", "default": 10, "description": "Maximum number of results (1-50)."},
                    "order": {
                        "type": "string", 
                        "description": "Sort order: 'date', 'rating', 'relevance', 'title', 'videoCount', 'viewCount'. Defaults to 'relevance'.",
                        "enum": ["date", "rating", "relevance", "title", "videoCount", "viewCount"],
                        "default": "relevance"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_video_categories",
            description=(
                "Retrieves the list of video categories available in a specific region.\n"
                "Use this tool to get valid Category IDs for filtering searches or trending videos.\n"
                "Returns a map of Category IDs to Category Names."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {"type": "string", "default": "US", "description": "ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB')."}
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_comment_replies",
            description=(
                "Retrieves replies to a specific top-level comment.\n"
                "Use this tool to dive deeper into a specific conversation thread in the comments.\n"
                "Returns a list of reply comments."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "comment_id": {"type": "string", "description": "The parent comment ID."},
                    "max_results": {"type": "number", "default": 20, "description": "Maximum number of replies to return (1-100)."}
                },
                "required": ["comment_id"]
            }
        ),
        types.Tool(
            name="get_live_stream_info",
            description=(
                "Retrieves real-time information about a live stream.\n"
                "Use this tool to check if a video is currently live, scheduled, or ended, and get live viewer counts.\n"
                "Returns status, scheduled start/end times, and concurrent viewer count if live."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL of the live stream."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="calculate_engagement_rate",
            description=(
                "Calculates raw engagement rates for a video.\n"
                "Use this tool to get the mathematical ratios of likes/views and comments/views without qualitative analysis.\n"
                "Returns percentages."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "The YouTube video ID or URL."}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_most_liked_video",
            description=(
                "Finds the most liked video for a channel or search query.\n"
                "Use this tool to identify the most popular content by audience approval (likes).\n"
                "Returns the single video with the highest like count from the search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or channel name."},
                    "channel_id": {"type": "string", "description": "Optional: Specific YouTube channel ID to restrict search to."}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_most_viewed_video",
            description=(
                "Finds the most viewed video for a channel or search query.\n"
                "Use this tool to identify the most viral or widely watched content.\n"
                "Returns the single video with the highest view count from the search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or channel name."},
                    "channel_id": {"type": "string", "description": "Optional: Specific YouTube channel ID to restrict search to."}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    try:
        if name == "get_video_info":
            video_id = extract_video_id(arguments.get("video_id"))
            
            # Get video details
            request = get_youtube_client().videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return [types.TextContent(
                    type="text",
                    text=f"Video not found: {video_id}"
                )]
            
            video = response["items"][0]
            snippet = video["snippet"]
            statistics = video.get("statistics", {})
            content_details = video["contentDetails"]
            
            info = {
                "video_id": video_id,
                "title": snippet["title"],
                "description": snippet["description"],
                "channel": {
                    "name": snippet["channelTitle"],
                    "id": snippet["channelId"]
                },
                "published_at": snippet["publishedAt"],
                "duration": format_duration(content_details["duration"]),
                "duration_raw": content_details["duration"],
                "statistics": {
                    "views": int(statistics.get("viewCount", 0)),
                    "views_formatted": format_number(int(statistics.get("viewCount", 0))),
                    "likes": int(statistics.get("likeCount", 0)),
                    "likes_formatted": format_number(int(statistics.get("likeCount", 0))),
                    "comments": int(statistics.get("commentCount", 0)),
                    "comments_formatted": format_number(int(statistics.get("commentCount", 0)))
                },
                "tags": snippet.get("tags", []),
                "category_id": snippet["categoryId"],
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "url": f"https://youtube.com/watch?v={video_id}"
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(info, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_video_transcript":
            video_id = extract_video_id(arguments.get("video_id"))
            language = arguments.get("language", "en")
            
            try:
                # Create API instance (new API in v1.x)
                ytt_api = YouTubeTranscriptApi()
                
                # Fetch transcript (new API uses .fetch() instead of .get_transcript())
                fetched_transcript = ytt_api.fetch(video_id)
                
                # Format transcript
                formatted_transcript = []
                full_text = []
                
                for snippet in fetched_transcript:
                    timestamp = snippet.start
                    minutes = int(timestamp // 60)
                    seconds = int(timestamp % 60)
                    time_str = f"{minutes:02d}:{seconds:02d}"
                    
                    formatted_transcript.append({
                        "timestamp": time_str,
                        "timestamp_seconds": snippet.start,
                        "duration": snippet.duration,
                        "text": snippet.text
                    })
                    
                    full_text.append(snippet.text)
                
                result = {
                    "video_id": video_id,
                    "language": fetched_transcript.language,
                    "language_code": fetched_transcript.language_code,
                    "is_generated": fetched_transcript.is_generated,
                    "transcript": formatted_transcript,
                    "full_text": " ".join(full_text)
                }
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
                
            except TranscriptsDisabled:
                return [types.TextContent(
                    type="text",
                    text=f"Transcripts are disabled for this video: {video_id}"
                )]
            except NoTranscriptFound:
                return [types.TextContent(
                    type="text",
                    text=f"No transcript found for language '{language}' in video: {video_id}"
                )]
            except VideoUnavailable:
                return [types.TextContent(
                    type="text",
                    text=f"Video is unavailable: {video_id}"
                )]
        
        elif name == "get_video_comments":
            video_id = extract_video_id(arguments.get("video_id"))
            max_results = min(arguments.get("max_results", 20), 100)
            order = arguments.get("order", "relevance")
            
            request = get_youtube_client().commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                order=order,
                textFormat="plainText"
            )
            response = request.execute()
            
            comments = []
            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "id": item["id"],
                    "author": comment["authorDisplayName"],
                    "text": comment["textDisplay"],
                    "likes": comment["likeCount"],
                    "published_at": comment["publishedAt"],
                    "reply_count": item["snippet"]["totalReplyCount"]
                })
            
            result = {
                "video_id": video_id,
                "total_comments": len(comments),
                "comments": comments
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "search_videos":
            query = arguments.get("query")
            max_results = min(arguments.get("max_results", 10), 50)
            order = arguments.get("order", "relevance")
            
            request = get_youtube_client().search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order=order
            )
            response = request.execute()
            
            videos = []
            for item in response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "channel": snippet["channelTitle"],
                    "channel_id": snippet["channelId"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail": snippet["thumbnails"]["high"]["url"],
                    "url": f"https://youtube.com/watch?v={item['id']['videoId']}"
                })
            
            result = {
                "query": query,
                "total_results": len(videos),
                "videos": videos
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_channel_info":
            channel_id = arguments.get("channel_id")
            
            # Extract channel ID from URL if needed
            if "youtube.com" in channel_id:
                if "/channel/" in channel_id:
                    channel_id = channel_id.split("/channel/")[1].split("/")[0]
                elif "/@" in channel_id:
                    # Handle @username format
                    username = channel_id.split("/@")[1].split("/")[0]
                    search_request = get_youtube_client().search().list(
                        part="snippet",
                        q=username,
                        type="channel",
                        maxResults=1
                    )
                    search_response = search_request.execute()
                    if search_response.get("items"):
                        channel_id = search_response["items"][0]["snippet"]["channelId"]
            
            request = get_youtube_client().channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return [types.TextContent(
                    type="text",
                    text=f"Channel not found: {channel_id}"
                )]
            
            channel = response["items"][0]
            snippet = channel["snippet"]
            statistics = channel["statistics"]
            
            info = {
                "channel_id": channel_id,
                "title": snippet["title"],
                "description": snippet["description"],
                "custom_url": snippet.get("customUrl", ""),
                "published_at": snippet["publishedAt"],
                "statistics": {
                    "subscribers": int(statistics.get("subscriberCount", 0)),
                    "subscribers_formatted": format_number(int(statistics.get("subscriberCount", 0))),
                    "total_views": int(statistics.get("viewCount", 0)),
                    "total_views_formatted": format_number(int(statistics.get("viewCount", 0))),
                    "video_count": int(statistics.get("videoCount", 0))
                },
                "thumbnail": snippet["thumbnails"]["high"]["url"],
                "country": snippet.get("country", "Unknown"),
                "url": f"https://youtube.com/channel/{channel_id}"
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(info, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_channel_videos":
            channel_id = arguments.get("channel_id")
            max_results = min(arguments.get("max_results", 10), 50)
            order = arguments.get("order", "date")
            
            request = get_youtube_client().search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                order=order,
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail": snippet["thumbnails"]["high"]["url"],
                    "url": f"https://youtube.com/watch?v={item['id']['videoId']}"
                })
            
            result = {
                "channel_id": channel_id,
                "total_videos": len(videos),
                "videos": videos
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_trending_videos":
            region_code = arguments.get("region_code", "US")
            category_id = arguments.get("category_id", "0")
            max_results = min(arguments.get("max_results", 10), 50)
            
            request = get_youtube_client().videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                videoCategoryId=category_id if category_id != "0" else None,
                maxResults=max_results
            )
            response = request.execute()
            
            videos = []
            for item in response.get("items", []):
                snippet = item["snippet"]
                statistics = item.get("statistics", {})
                
                videos.append({
                    "video_id": item["id"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "channel": snippet["channelTitle"],
                    "channel_id": snippet["channelId"],
                    "published_at": snippet["publishedAt"],
                    "views": int(statistics.get("viewCount", 0)),
                    "views_formatted": format_number(int(statistics.get("viewCount", 0))),
                    "likes": int(statistics.get("likeCount", 0)),
                    "thumbnail": snippet["thumbnails"]["high"]["url"],
                    "url": f"https://youtube.com/watch?v={item['id']}"
                })
            
            result = {
                "region": region_code,
                "category": category_id,
                "total_videos": len(videos),
                "videos": videos
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_playlist_info":
            playlist_id = arguments.get("playlist_id")
            max_results = min(arguments.get("max_results", 20), 50)
            
            # Get playlist details
            playlist_request = get_youtube_client().playlists().list(
                part="snippet,contentDetails",
                id=playlist_id
            )
            playlist_response = playlist_request.execute()
            
            if not playlist_response.get("items"):
                return [types.TextContent(
                    type="text",
                    text=f"Playlist not found: {playlist_id}"
                )]
            
            playlist = playlist_response["items"][0]
            playlist_snippet = playlist["snippet"]
            
            # Get playlist items
            items_request = get_youtube_client().playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=max_results
            )
            items_response = items_request.execute()
            
            videos = []
            for item in items_response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": snippet["resourceId"]["videoId"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "channel": snippet["channelTitle"],
                    "published_at": snippet["publishedAt"],
                    "position": snippet["position"],
                    "thumbnail": snippet["thumbnails"]["high"]["url"],
                    "url": f"https://youtube.com/watch?v={snippet['resourceId']['videoId']}"
                })
            
            result = {
                "playlist_id": playlist_id,
                "title": playlist_snippet["title"],
                "description": playlist_snippet["description"],
                "channel": playlist_snippet["channelTitle"],
                "channel_id": playlist_snippet["channelId"],
                "total_videos": playlist["contentDetails"]["itemCount"],
                "videos_retrieved": len(videos),
                "videos": videos
            }
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False)
            )]
        
        elif name == "get_video_analytics":
            video_id = extract_video_id(arguments.get("video_id"))
            data = await _get_video_data(video_id)
            
            if not data:
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            return [types.TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "analyze_video_engagement":
            video_id = extract_video_id(arguments.get("video_id"))
            data = await _get_video_data(video_id)
            
            if not data:
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            rating = _calculate_performance_rating(data["like_rate"], data["comment_rate"])
            
            result = {
                "video_id": video_id,
                "title": data["title"],
                "views": data["views_formatted"],
                "engagement_analysis": {
                    "like_rate": f"{data['like_rate']}%",
                    "like_rating": rating["like_rating"],
                    "comment_rate": f"{data['comment_rate']}%",
                    "comment_rating": rating["comment_rating"],
                    "engagement_score": data["engagement_score"]
                },
                "interpretation": f"This video has {rating['like_rating'].lower()} like engagement and {rating['comment_rating'].lower()}."
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "get_video_performance_score":
            video_id = extract_video_id(arguments.get("video_id"))
            data = await _get_video_data(video_id)
            
            if not data:
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            # Calculate performance score (0-100)
            score = min(data["engagement_score"] * 10, 100)
            
            if score >= 80:
                grade = "A"
                summary = "Exceptional performance. This video resonates very well with the audience."
            elif score >= 60:
                grade = "B"
                summary = "Good performance. Above average engagement from viewers."
            elif score >= 40:
                grade = "C"
                summary = "Average performance. Typical engagement levels."
            elif score >= 20:
                grade = "D"
                summary = "Below average. Consider improving content quality or targeting."
            else:
                grade = "F"
                summary = "Poor performance. May need significant changes to content strategy."
            
            result = {
                "video_id": video_id,
                "title": data["title"],
                "performance_score": round(score, 1),
                "grade": grade,
                "summary": summary,
                "metrics": {
                    "views": data["views_formatted"],
                    "likes": data["likes_formatted"],
                    "comments": data["comments_formatted"],
                    "like_rate": f"{data['like_rate']}%",
                    "comment_rate": f"{data['comment_rate']}%"
                }
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "compare_videos":
            video_ids = arguments.get("video_ids", [])
            
            if len(video_ids) < 2:
                return [types.TextContent(type="text", text="Error: At least 2 videos required for comparison")]
            
            videos_data = []
            for vid in video_ids[:10]:  # Limit to 10 videos
                video_id = extract_video_id(vid)
                data = await _get_video_data(video_id)
                if data:
                    videos_data.append(data)
            
            if len(videos_data) < 2:
                return [types.TextContent(type="text", text="Error: Could not fetch data for enough videos")]
            
            # Sort by engagement score
            videos_data.sort(key=lambda x: x["engagement_score"], reverse=True)
            
            # Find best performers
            best_engagement = videos_data[0]
            best_views = max(videos_data, key=lambda x: x["views"])
            best_likes = max(videos_data, key=lambda x: x["like_rate"])
            
            result = {
                "videos_compared": len(videos_data),
                "ranking_by_engagement": [
                    {
                        "rank": i + 1,
                        "title": v["title"],
                        "video_id": v["video_id"],
                        "views": v["views_formatted"],
                        "engagement_score": v["engagement_score"]
                    }
                    for i, v in enumerate(videos_data)
                ],
                "highlights": {
                    "best_engagement": {"title": best_engagement["title"], "score": best_engagement["engagement_score"]},
                    "most_views": {"title": best_views["title"], "views": best_views["views_formatted"]},
                    "best_like_rate": {"title": best_likes["title"], "like_rate": f"{best_likes['like_rate']}%"}
                }
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "analyze_video_potential":
            video_id = extract_video_id(arguments.get("video_id"))
            data = await _get_video_data(video_id)
            
            if not data:
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            # Analyze content quality signals
            signals = []
            concerns = []
            
            if data["like_rate"] >= 5:
                signals.append("High like-to-view ratio indicates strong content resonance")
            elif data["like_rate"] < 1:
                concerns.append("Low like-to-view ratio suggests content may need improvement")
            
            if data["comment_rate"] >= 0.5:
                signals.append("High comment rate shows active audience engagement")
            elif data["comment_rate"] < 0.05:
                concerns.append("Low comment rate - consider adding calls to action")
            
            if data["views"] > 1000000:
                signals.append("Viral reach - video has achieved significant visibility")
            elif data["views"] > 100000:
                signals.append("Strong reach - video performing well")
            elif data["views"] < 1000:
                concerns.append("Limited reach - may need promotion or SEO optimization")
            
            result = {
                "video_id": video_id,
                "title": data["title"],
                "channel": data["channel"],
                "current_metrics": {
                    "views": data["views_formatted"],
                    "likes": data["likes_formatted"],
                    "comments": data["comments_formatted"],
                    "engagement_score": data["engagement_score"]
                },
                "quality_signals": signals if signals else ["No strong positive signals detected"],
                "areas_for_improvement": concerns if concerns else ["No major concerns identified"],
                "overall_assessment": "Strong" if len(signals) > len(concerns) else "Needs Improvement" if len(concerns) > len(signals) else "Average"
            }
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


        elif name == "compare_channels":
            channel_ids = arguments.get("channel_ids", [])
            if len(channel_ids) < 2:
                return [types.TextContent(type="text", text="Error: At least 2 channels required for comparison")]
            
            channels_data = []
            for channel_id in channel_ids[:5]:  # Limit to 5 channels
                try:
                    request = get_youtube_client().channels().list(
                        part="snippet,statistics",
                        id=channel_id
                    )
                    response = request.execute()
                    if response.get("items"):
                        channel = response["items"][0]
                        snippet = channel["snippet"]
                        stats = channel["statistics"]
                        
                        channels_data.append({
                            "channel_id": channel_id,
                            "title": snippet["title"],
                            "subscribers": int(stats.get("subscriberCount", 0)),
                            "total_views": int(stats.get("viewCount", 0)),
                            "video_count": int(stats.get("videoCount", 0)),
                            "country": snippet.get("country", "Unknown"),
                            "avg_views_per_video": int(stats.get("viewCount", 0)) // max(int(stats.get("videoCount", 1)), 1)
                        })
                except:
                    continue
            
            return [types.TextContent(type="text", text=json.dumps({"channels": channels_data}, indent=2, ensure_ascii=False))]

        elif name == "analyze_content_strategy":
            channel_id = arguments.get("channel_id")
            
            # Get channel info
            channel_request = get_youtube_client().channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            channel_response = channel_request.execute()
            if not channel_response.get("items"):
                return [types.TextContent(type="text", text=f"Channel not found: {channel_id}")]
            
            channel = channel_response["items"][0]
            stats = channel["statistics"]
            
            # Get recent videos
            videos_request = get_youtube_client().search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                order="date",
                maxResults=20
            )
            videos_response = videos_request.execute()
            
            video_count = int(stats.get("videoCount", 0))
            videos_per_month = video_count / 12 if video_count > 0 else 0
            
            if videos_per_month > 60:
                frequency = "Daily+ (Multiple per day)"
            elif videos_per_month > 30:
                frequency = "Daily"
            elif videos_per_month > 12:
                frequency = "Weekly (2-3x)"
            elif videos_per_month > 4:
                frequency = "Weekly"
            else:
                frequency = "Monthly"
            
            strategy = {
                "channel_id": channel_id,
                "title": channel["snippet"]["title"],
                "total_videos": video_count,
                "estimated_videos_per_month": round(videos_per_month, 1),
                "posting_frequency": frequency,
                "recent_videos_count": len(videos_response.get("items", [])),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "avg_views_per_video": int(stats.get("viewCount", 0)) // max(video_count, 1)
            }
            
            return [types.TextContent(type="text", text=json.dumps(strategy, indent=2, ensure_ascii=False))]

        elif name == "benchmark_performance":
            target_id = arguments.get("target_channel_id")
            competitor_ids = arguments.get("competitor_channel_ids", [])
            
            all_ids = [target_id] + competitor_ids
            channels_data = []
            
            for channel_id in all_ids:
                try:
                    request = get_youtube_client().channels().list(
                        part="snippet,statistics",
                        id=channel_id
                    )
                    response = request.execute()
                    if response.get("items"):
                        channel = response["items"][0]
                        snippet = channel["snippet"]
                        stats = channel["statistics"]
                        
                        subs = int(stats.get("subscriberCount", 0))
                        views = int(stats.get("viewCount", 0))
                        videos = int(stats.get("videoCount", 1))
                        
                        channels_data.append({
                            "channel_id": channel_id,
                            "title": snippet["title"],
                            "is_target": channel_id == target_id,
                            "subscribers": subs,
                            "total_views": views,
                            "video_count": videos,
                            "avg_views_per_video": views // videos,
                            "engagement_score": (views / max(subs, 1)) * 100
                        })
                except:
                    continue
            
            # Calculate rankings
            target_data = next((c for c in channels_data if c["is_target"]), None)
            if target_data:
                sorted_by_subs = sorted(channels_data, key=lambda x: x["subscribers"], reverse=True)
                sorted_by_engagement = sorted(channels_data, key=lambda x: x["engagement_score"], reverse=True)
                
                target_data["rank_by_subscribers"] = sorted_by_subs.index(target_data) + 1
                target_data["rank_by_engagement"] = sorted_by_engagement.index(target_data) + 1
            
            return [types.TextContent(type="text", text=json.dumps({
                "target": target_data,
                "competitors": [c for c in channels_data if not c["is_target"]],
                "total_channels": len(channels_data)
            }, indent=2, ensure_ascii=False))]

        elif name == "identify_competitive_advantages":
            channel_id = arguments.get("channel_id")
            comparison_ids = arguments.get("comparison_channel_ids", [])
            
            all_ids = [channel_id] + comparison_ids
            channels_data = []
            
            for cid in all_ids:
                try:
                    request = get_youtube_client().channels().list(
                        part="snippet,statistics",
                        id=cid
                    )
                    response = request.execute()
                    if response.get("items"):
                        channel = response["items"][0]
                        stats = channel["statistics"]
                        
                        subs = int(stats.get("subscriberCount", 0))
                        views = int(stats.get("viewCount", 0))
                        videos = int(stats.get("videoCount", 1))
                        
                        channels_data.append({
                            "channel_id": cid,
                            "title": channel["snippet"]["title"],
                            "is_target": cid == channel_id,
                            "subscribers": subs,
                            "total_views": views,
                            "video_count": videos,
                            "avg_views_per_video": views // videos,
                            "view_to_sub_ratio": (views / max(subs, 1))
                        })
                except:
                    continue
            
            target = next((c for c in channels_data if c["is_target"]), None)
            if not target:
                return [types.TextContent(type="text", text="Target channel not found")]
            
            advantages = []
            weaknesses = []
            
            # Compare metrics
            avg_subs = sum(c["subscribers"] for c in channels_data) / len(channels_data)
            avg_views_per_video = sum(c["avg_views_per_video"] for c in channels_data) / len(channels_data)
            avg_ratio = sum(c["view_to_sub_ratio"] for c in channels_data) / len(channels_data)
            
            if target["subscribers"] > avg_subs:
                advantages.append("Above average subscriber count")
            else:
                weaknesses.append("Below average subscriber count")
            
            if target["avg_views_per_video"] > avg_views_per_video:
                advantages.append("Above average views per video")
            else:
                weaknesses.append("Below average views per video")
            
            if target["view_to_sub_ratio"] > avg_ratio:
                advantages.append("Strong view-to-subscriber ratio")
            else:
                weaknesses.append("Weak view-to-subscriber ratio")
            
            return [types.TextContent(type="text", text=json.dumps({
                "channel": target["title"],
                "advantages": advantages,
                "weaknesses": weaknesses,
                "metrics": target
            }, indent=2, ensure_ascii=False))]

        elif name == "track_market_share":
            channel_ids = arguments.get("channel_ids", [])
            
            channels_data = []
            total_subs = 0
            total_views = 0
            
            for channel_id in channel_ids:
                try:
                    request = get_youtube_client().channels().list(
                        part="snippet,statistics",
                        id=channel_id
                    )
                    response = request.execute()
                    if response.get("items"):
                        channel = response["items"][0]
                        stats = channel["statistics"]
                        
                        subs = int(stats.get("subscriberCount", 0))
                        views = int(stats.get("viewCount", 0))
                        
                        channels_data.append({
                            "channel_id": channel_id,
                            "title": channel["snippet"]["title"],
                            "subscribers": subs,
                            "total_views": views
                        })
                        
                        total_subs += subs
                        total_views += views
                except:
                    continue
            
            # Calculate market share
            for channel in channels_data:
                channel["subscriber_share_percent"] = (channel["subscribers"] / max(total_subs, 1)) * 100
                channel["view_share_percent"] = (channel["total_views"] / max(total_views, 1)) * 100
            
            return [types.TextContent(type="text", text=json.dumps({
                "total_subscribers": total_subs,
                "total_views": total_views,
                "channels": channels_data
            }, indent=2, ensure_ascii=False))]

        # --- Report Generation Handlers ---
        elif name == "generate_channel_report":
            channel_id = arguments.get("channel_id")
            period_days = int(arguments.get("period_days", 7))
            include_videos = arguments.get("include_videos", True)
            
            # Get channel info
            channel_request = get_youtube_client().channels().list(
                part="snippet,statistics",
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response.get("items"):
                return [types.TextContent(type="text", text=f"Channel not found: {channel_id}")]
            
            channel = channel_response["items"][0]
            channel_stats = channel["statistics"]
            
            # Get recent videos
            videos_request = get_youtube_client().search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                order="date",
                maxResults=50,
                publishedAfter=(datetime.now() - timedelta(days=period_days)).isoformat() + "Z"
            )
            videos_response = videos_request.execute()
            
            video_ids = [item["id"]["videoId"] for item in videos_response.get("items", [])]
            
            # Get video details
            videos_data = []
            if video_ids:
                details_request = get_youtube_client().videos().list(
                    part="snippet,statistics,contentDetails",
                    id=",".join(video_ids[:50])
                )
                details_response = details_request.execute()
                
                for video in details_response.get("items", []):
                    stats = video["statistics"]
                    views = int(stats.get("viewCount", 0))
                    likes = int(stats.get("likeCount", 0))
                    comments = int(stats.get("commentCount", 0))
                    
                    like_rate = (likes / views * 100) if views > 0 else 0
                    
                    videos_data.append({
                        "video_id": video["id"],
                        "title": video["snippet"]["title"],
                        "published_at": video["snippet"]["publishedAt"],
                        "views": views,
                        "views_formatted": format_number(views),
                        "likes": likes,
                        "likes_formatted": format_number(likes),
                        "comments": comments,
                        "comments_formatted": format_number(comments),
                        "like_rate": round(like_rate, 2),
                        "duration": format_duration(video["contentDetails"]["duration"]),
                        "url": f"https://youtube.com/watch?v={video['id']}"
                    })
            
            # Calculate aggregate metrics
            total_views = sum(v["views"] for v in videos_data)
            total_likes = sum(v["likes"] for v in videos_data)
            total_comments = sum(v["comments"] for v in videos_data)
            
            avg_views = total_views / len(videos_data) if videos_data else 0
            avg_likes = total_likes / len(videos_data) if videos_data else 0
            avg_like_rate = (total_likes / total_views * 100) if total_views > 0 else 0
            
            # Get top performers
            top_by_views = sorted(videos_data, key=lambda x: x["views"], reverse=True)[:3]
            top_by_engagement = sorted(videos_data, key=lambda x: x["like_rate"], reverse=True)[:3]
            
            report = {
                "report_type": "channel_performance",
                "generated_at": datetime.now().isoformat(),
                "period_days": period_days,
                "channel": {
                    "id": channel_id,
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"][:200] + "..." if len(channel["snippet"]["description"]) > 200 else channel["snippet"]["description"],
                    "subscribers": int(channel_stats.get("subscriberCount", 0)),
                    "subscribers_formatted": format_number(int(channel_stats.get("subscriberCount", 0))),
                    "total_views": int(channel_stats.get("viewCount", 0)),
                    "total_views_formatted": format_number(int(channel_stats.get("viewCount", 0))),
                    "total_videos": int(channel_stats.get("videoCount", 0)),
                    "thumbnail": channel["snippet"]["thumbnails"]["high"]["url"],
                    "url": f"https://youtube.com/channel/{channel_id}"
                },
                "period_summary": {
                    "videos_published": len(videos_data),
                    "total_views": total_views,
                    "total_views_formatted": format_number(total_views),
                    "total_likes": total_likes,
                    "total_likes_formatted": format_number(total_likes),
                    "total_comments": total_comments,
                    "total_comments_formatted": format_number(total_comments),
                    "avg_views_per_video": int(avg_views),
                    "avg_views_formatted": format_number(int(avg_views)),
                    "avg_likes_per_video": int(avg_likes),
                    "avg_like_rate": round(avg_like_rate, 2)
                },
                "top_performers": {
                    "by_views": [{"title": v["title"], "views": v["views_formatted"], "url": v["url"]} for v in top_by_views],
                    "by_engagement": [{"title": v["title"], "like_rate": f"{v['like_rate']}%", "url": v["url"]} for v in top_by_engagement]
                }
            }
            
            if include_videos:
                report["videos"] = videos_data
            
            return [types.TextContent(type="text", text=json.dumps(report, indent=2, ensure_ascii=False))]

        elif name == "generate_video_report":
            video_id = extract_video_id(arguments.get("video_id"))
            
            # Get video details
            request = get_youtube_client().videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            video = response["items"][0]
            snippet = video["snippet"]
            stats = video["statistics"]
            content = video["contentDetails"]
            
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            like_rate = (likes / views * 100) if views > 0 else 0
            comment_rate = (comments / views * 100) if views > 0 else 0
            
            # Use improved engagement score formula
            score = (like_rate * 20) + (comment_rate * 100)
            score = min(score, 100)
            score = round(score, 1)
            
            if score >= 80:
                grade = "A"
            elif score >= 60:
                grade = "B"
            elif score >= 40:
                grade = "C"
            elif score >= 20:
                grade = "D"
            else:
                grade = "F"
            
            # Recalculate rating for consistency
            rating = _calculate_performance_rating(like_rate, comment_rate)
            
            # Quality signals
            signals = []
            concerns = []
            
            if like_rate >= 4:
                signals.append("Excellent like-to-view ratio")
            elif like_rate >= 2:
                signals.append("Strong audience resonance (Good like rate)")
            elif like_rate < 0.5:
                concerns.append("Low like-to-view ratio")
            
            if comment_rate >= 0.2:
                signals.append("High audience engagement in comments")
            elif comment_rate < 0.01:
                concerns.append("Low comment engagement")
            
            if views > 500000:
                signals.append("Viral reach achieved")
            elif views > 50000:
                signals.append("Strong video reach")
            elif views < 500:
                concerns.append("Limited reach")
            
            report = {
                "report_type": "video_performance",
                "generated_at": datetime.now().isoformat(),
                "video": {
                    "id": video_id,
                    "title": snippet["title"],
                    "description": snippet["description"][:300] + "..." if len(snippet["description"]) > 300 else snippet["description"],
                    "channel": snippet["channelTitle"],
                    "channel_id": snippet["channelId"],
                    "published_at": snippet["publishedAt"],
                    "duration": format_duration(content["duration"]),
                    "thumbnail": snippet["thumbnails"]["high"]["url"],
                    "url": f"https://youtube.com/watch?v={video_id}"
                },
                "metrics": {
                    "views": views,
                    "views_formatted": format_number(views),
                    "likes": likes,
                    "likes_formatted": format_number(likes),
                    "comments": comments,
                    "comments_formatted": format_number(comments),
                    "like_rate": round(like_rate, 2),
                    "comment_rate": round(comment_rate, 3),
                    "engagement_score": round(score, 2)
                },
                "performance": {
                    "score": round(score, 1),
                    "grade": grade,
                    "like_rating": rating["like_rating"],
                    "comment_rating": rating["comment_rating"]
                },
                "analysis": {
                    "quality_signals": signals if signals else ["No strong signals detected"],
                    "areas_for_improvement": concerns if concerns else ["No major concerns"],
                    "overall_assessment": "Strong" if len(signals) > len(concerns) else "Needs Improvement" if len(concerns) > len(signals) else "Average"
                }
            }
            
            return [types.TextContent(type="text", text=json.dumps(report, indent=2, ensure_ascii=False))]

        elif name == "get_related_videos":
            video_id = extract_video_id(arguments.get("video_id"))
            max_results = min(arguments.get("max_results", 10), 50)
            
            try:
                # 1. Get video details to find title (Fallback since relatedToVideoId is deprecated)
                video_request = get_youtube_client().videos().list(
                    part="snippet",
                    id=video_id
                )
                video_response = video_request.execute()
                
                if not video_response.get("items"):
                    return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
                
                snippet = video_response["items"][0]["snippet"]
                title = snippet["title"]
                
                # 2. Search using title
                search_query = title
                
                request = get_youtube_client().search().list(
                    part="snippet",
                    q=search_query,
                    type="video",
                    maxResults=max_results + 1 # Fetch extra to account for filtering original
                )
                response = request.execute()
                
                videos = []
                for item in response.get("items", []):
                    vid = item["id"]["videoId"]
                    if vid == video_id:
                        continue # Skip original video
                        
                    v_snippet = item["snippet"]
                    videos.append({
                        "video_id": vid,
                        "title": v_snippet["title"],
                        "channel": v_snippet["channelTitle"],
                        "published_at": v_snippet["publishedAt"],
                        "thumbnail": v_snippet["thumbnails"]["high"]["url"],
                        "url": f"https://youtube.com/watch?v={vid}"
                    })
                
                # Limit to max_results after filtering
                videos = videos[:max_results]
                
                result = {
                    "related_to_video_id": video_id,
                    "count": len(videos),
                    "videos": videos,
                    "note": "Native relatedToVideoId is deprecated; results based on title search."
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
                
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error fetching related videos: {str(e)}")]

        elif name == "get_channel_playlists":
            channel_id = arguments.get("channel_id")
            max_results = min(arguments.get("max_results", 10), 50)
            
            request = get_youtube_client().playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=max_results
            )
            response = request.execute()
            
            playlists = []
            for item in response.get("items", []):
                snippet = item["snippet"]
                playlists.append({
                    "playlist_id": item["id"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "item_count": item["contentDetails"]["itemCount"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail": snippet["thumbnails"]["high"]["url"] if "high" in snippet["thumbnails"] else ""
                })
            
            result = {
                "channel_id": channel_id,
                "count": len(playlists),
                "playlists": playlists
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "search_channels":
            query = arguments.get("query")
            max_results = min(arguments.get("max_results", 10), 50)
            order = arguments.get("order", "relevance")
            
            request = get_youtube_client().search().list(
                part="snippet",
                q=query,
                type="channel",
                maxResults=max_results,
                order=order
            )
            response = request.execute()
            
            channels = []
            for item in response.get("items", []):
                snippet = item["snippet"]
                channels.append({
                    "channel_id": item["snippet"]["channelId"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail": snippet["thumbnails"]["high"]["url"] if "high" in snippet["thumbnails"] else ""
                })
            
            result = {
                "query": query,
                "count": len(channels),
                "channels": channels
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "get_video_categories":
            region_code = arguments.get("region_code", "US")
            
            request = get_youtube_client().videoCategories().list(
                part="snippet",
                regionCode=region_code
            )
            response = request.execute()
            
            categories = []
            for item in response.get("items", []):
                categories.append({
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "assignable": item["snippet"]["assignable"]
                })
            
            result = {
                "region_code": region_code,
                "count": len(categories),
                "categories": categories
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "get_comment_replies":
            comment_id = arguments.get("comment_id")
            max_results = min(arguments.get("max_results", 20), 100)
            
            request = get_youtube_client().comments().list(
                part="snippet",
                parentId=comment_id,
                maxResults=max_results
            )
            try:
                response = request.execute()
                replies = []
                for item in response.get("items", []):
                    snippet = item["snippet"]
                    replies.append({
                        "comment_id": item["id"],
                        "author": snippet["authorDisplayName"],
                        "text": snippet["textDisplay"],
                        "likes": snippet["likeCount"],
                        "published_at": snippet["publishedAt"]
                    })
                
                result = {
                    "parent_comment_id": comment_id,
                    "count": len(replies),
                    "replies": replies
                }
                return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error fetching replies: {str(e)}")]

        elif name == "get_live_stream_info":
            video_id = extract_video_id(arguments.get("video_id"))
            
            request = get_youtube_client().videos().list(
                part="snippet,liveStreamingDetails,statistics",
                id=video_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            video = response["items"][0]
            snippet = video["snippet"]
            live_details = video.get("liveStreamingDetails", {})
            stats = video.get("statistics", {})
            
            is_live = snippet.get("liveBroadcastContent") == "live"
            
            result = {
                "video_id": video_id,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "live_status": snippet.get("liveBroadcastContent"),
                "is_live_now": is_live,
                "concurrent_viewers": int(live_details.get("concurrentViewers", 0)) if is_live else 0,
                "scheduled_start_time": live_details.get("scheduledStartTime"),
                "actual_start_time": live_details.get("actualStartTime"),
                "actual_end_time": live_details.get("actualEndTime"),
                "chat_id": live_details.get("activeLiveChatId")
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "calculate_engagement_rate":
            video_id = extract_video_id(arguments.get("video_id"))
            data = await _get_video_data(video_id)
            if not data:
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            like_rate = data["like_rate"]
            comment_rate = data["comment_rate"]
            engagement_score = like_rate * 0.6 + comment_rate * 0.4
            
            result = {
                "video_id": video_id,
                "title": data["title"],
                "views": int(data["views"]),
                "likes": int(data["likes"]),
                "comments": int(data["comments"]),
                "like_rate_percent": round(like_rate, 2),
                "comment_rate_percent": round(comment_rate, 2),
                "engagement_score": round(engagement_score, 1),
                "formula": "like_rate * 0.6 + comment_rate * 0.4"
            }
            return [types.TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name in ["get_most_liked_video", "get_most_viewed_video"]:
            query = arguments.get("query")
            channel_id = arguments.get("channel_id")
            
            # 1. Resolve channel ID if not provided
            if not channel_id:
                channel_search = get_youtube_client().search().list(
                    part="snippet",
                    q=query,
                    type="channel",
                    maxResults=1
                ).execute()
                
                if channel_search.get("items"):
                    channel_id = channel_search["items"][0]["id"]["channelId"]
            
            # 2. Search for videos
            search_params = {
                "part": "snippet",
                "type": "video",
                "maxResults": 50,
                "order": "viewCount"
            }
            if channel_id:
                search_params["channelId"] = channel_id
            else:
                search_params["q"] = query
            
            search_results = get_youtube_client().search().list(**search_params).execute()
            video_ids = [item["id"]["videoId"] for item in search_results.get("items", [])]
            
            if not video_ids:
                return [types.TextContent(type="text", text=f"No videos found for: {query}")]
            
            # 3. Get statistics for videos
            video_details = get_youtube_client().videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(video_ids)
            ).execute()
            
            videos = []
            for item in video_details.get("items", []):
                stats = item["statistics"]
                snippet = item["snippet"]
                videos.append({
                    "video_id": item["id"],
                    "title": snippet["title"],
                    "channel": snippet["channelTitle"],
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "published_at": snippet["publishedAt"],
                    "duration": format_duration(item["contentDetails"]["duration"]),
                    "url": f"https://youtube.com/watch?v={item['id']}"
                })
            
            # 4. Sort
            if name == "get_most_liked_video":
                videos.sort(key=lambda x: x["likes"], reverse=True)
            else:
                videos.sort(key=lambda x: x["views"], reverse=True)
            
            if not videos:
                return [types.TextContent(type="text", text="Could not retrieve video statistics")]
            
            return [types.TextContent(type="text", text=json.dumps(videos[0], indent=2, ensure_ascii=False))]

        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="youtube-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

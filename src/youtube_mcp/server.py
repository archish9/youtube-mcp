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
        engagement_score = (like_rate * 0.7) + (comment_rate * 0.3 * 10)  # Weighted score
        
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
            description="Get detailed metadata about a YouTube video including title, description, views, likes, duration, and channel info",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID or full URL (e.g., 'dQw4w9WgXcQ' or 'https://youtube.com/watch?v=dQw4w9WgXcQ')"
                    }
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_video_transcript",
            description="Get the transcript/captions of a YouTube video. Returns timestamped text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID or full URL"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (e.g., 'en', 'es', 'fr'). Default: 'en'",
                        "default": "en"
                    }
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_video_comments",
            description="Get top comments from a YouTube video",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "YouTube video ID or full URL"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of comments to retrieve (1-100)",
                        "default": 20
                    },
                    "order": {
                        "type": "string",
                        "description": "Order comments by: time, relevance",
                        "enum": ["time", "relevance"],
                        "default": "relevance"
                    }
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="search_videos",
            description="Search for YouTube videos by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order: date, rating, relevance, title, viewCount",
                        "enum": ["date", "rating", "relevance", "title", "viewCount"],
                        "default": "relevance"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_channel_info",
            description="Get information about a YouTube channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "YouTube channel ID or channel URL"
                    }
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="get_channel_videos",
            description="Get recent videos from a YouTube channel",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "YouTube channel ID"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of videos (1-50)",
                        "default": 10
                    }
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="get_trending_videos",
            description="Get trending videos in a specific region",
            inputSchema={
                "type": "object",
                "properties": {
                    "region_code": {
                        "type": "string",
                        "description": "ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB', 'IN')",
                        "default": "US"
                    },
                    "category_id": {
                        "type": "string",
                        "description": "Video category ID (e.g., '10' for Music, '20' for Gaming)",
                        "default": "0"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_playlist_info",
            description="Get information about a YouTube playlist and its videos",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "YouTube playlist ID"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of videos to retrieve (1-50)",
                        "default": 20
                    }
                },
                "required": ["playlist_id"]
            }
        ),
        types.Tool(
            name="get_video_analytics",
            description="Get current video metrics with engagement analysis (views, likes, comments, engagement rates).",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID or URL"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="analyze_video_engagement",
            description="Analyze a video's engagement quality based on like-to-view and comment-to-view ratios.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID or URL"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="get_video_performance_score",
            description="Calculate a performance score for a video based on current engagement metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID or URL"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="compare_videos",
            description="Compare multiple videos side-by-side with metrics and engagement analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of video IDs to compare (2-10 videos)"
                    }
                },
                "required": ["video_ids"]
            }
        ),
        types.Tool(
            name="analyze_video_potential",
            description="Analyze a video's content quality signals and audience resonance based on current metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID or URL"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="compare_channels",
            description="Compare multiple YouTube channels side-by-side with detailed metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of YouTube channel IDs to compare (2-5 channels)"
                    }
                },
                "required": ["channel_ids"]
            }
        ),
        types.Tool(
            name="analyze_content_strategy",
            description="Analyze content strategy of a channel (posting frequency, video types, engagement patterns).",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "YouTube channel ID"}
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="benchmark_performance",
            description="Benchmark a channel's performance against competitors.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target_channel_id": {"type": "string", "description": "Target channel ID to benchmark"},
                    "competitor_channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of competitor channel IDs"
                    }
                },
                "required": ["target_channel_id", "competitor_channel_ids"]
            }
        ),
        types.Tool(
            name="identify_competitive_advantages",
            description="Identify competitive advantages and weaknesses of a channel compared to others.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "YouTube channel ID"},
                    "comparison_channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of channel IDs to compare against"
                    }
                },
                "required": ["channel_id", "comparison_channel_ids"]
            }
        ),
        types.Tool(
            name="track_market_share",
            description="Track market share and audience distribution across multiple channels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of YouTube channel IDs"
                    }
                },
                "required": ["channel_ids"]
            }
        ),
        # --- Report Generation Tools ---
        types.Tool(
            name="generate_channel_report",
            description="Generate a comprehensive performance report for a YouTube channel including metrics, top videos, and engagement analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string", "description": "YouTube channel ID"},
                    "period_days": {
                        "type": "number",
                        "description": "Report period in days (7, 30, or 90)",
                        "default": 7
                    },
                    "include_videos": {
                        "type": "boolean",
                        "description": "Include individual video details",
                        "default": True
                    }
                },
                "required": ["channel_id"]
            }
        ),
        types.Tool(
            name="generate_video_report",
            description="Generate a detailed performance report for a specific YouTube video including engagement analysis and metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID or URL"}
                },
                "required": ["video_id"]
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
                text=json.dumps(info, indent=2)
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
                    text=json.dumps(result, indent=2)
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
                text=json.dumps(result, indent=2)
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
                text=json.dumps(result, indent=2)
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
                text=json.dumps(info, indent=2)
            )]
        
        elif name == "get_channel_videos":
            channel_id = arguments.get("channel_id")
            max_results = min(arguments.get("max_results", 10), 50)
            
            request = get_youtube_client().search().list(
                part="snippet",
                channelId=channel_id,
                type="video",
                order="date",
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
                text=json.dumps(result, indent=2)
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
                text=json.dumps(result, indent=2)
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
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_video_analytics":
            video_id = extract_video_id(arguments.get("video_id"))
            data = await _get_video_data(video_id)
            
            if not data:
                return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
            
            return [types.TextContent(type="text", text=json.dumps(data, indent=2))]

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
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

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
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

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
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

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
            
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


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
            
            return [types.TextContent(type="text", text=json.dumps({"channels": channels_data}, indent=2))]

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
            
            return [types.TextContent(type="text", text=json.dumps(strategy, indent=2))]

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
            }, indent=2))]

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
            }, indent=2))]

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
            }, indent=2))]

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
            
            return [types.TextContent(type="text", text=json.dumps(report, indent=2))]

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
            engagement_score = (like_rate * 0.7) + (comment_rate * 0.3 * 10)
            
            # Performance rating
            rating = _calculate_performance_rating(like_rate, comment_rate)
            
            # Performance score
            score = min(engagement_score * 10, 100)
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
            
            # Quality signals
            signals = []
            concerns = []
            
            if like_rate >= 5:
                signals.append("Excellent like-to-view ratio")
            elif like_rate < 1:
                concerns.append("Low like-to-view ratio")
            
            if comment_rate >= 0.5:
                signals.append("High audience engagement in comments")
            elif comment_rate < 0.05:
                concerns.append("Low comment engagement")
            
            if views > 1000000:
                signals.append("Viral reach achieved")
            elif views > 100000:
                signals.append("Strong video reach")
            elif views < 1000:
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
                    "engagement_score": round(engagement_score, 2)
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
            
            return [types.TextContent(type="text", text=json.dumps(report, indent=2))]

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

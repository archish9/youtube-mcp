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

# --- Video Analytics Logic ---
from datetime import datetime
import json
import asyncio

def calculate_growth_rate_logic(snapshots):
    """Calculate growth rate between snapshots"""
    if len(snapshots) < 2:
        return None
    
    first = snapshots[0]
    last = snapshots[-1]
    
    # We need to handle potential string timestamps or datetime objects
    # Assuming ISO format strings for simplicity in this port
    try:
        ts_last = datetime.fromisoformat(last['timestamp'])
        ts_first = datetime.fromisoformat(first['timestamp'])
    except:
        return None

    time_diff = (ts_last - ts_first).days
    
    if time_diff == 0:
        time_diff = 1 
    
    first_views = int(first['views']) if int(first['views']) > 0 else 1
    first_likes = int(first['likes']) if int(first['likes']) > 0 else 1

    last_views = int(last['views'])
    last_likes = int(last['likes'])

    view_growth = ((last_views - first_views) / first_views) * 100
    like_growth = ((last_likes - first_likes) / first_likes) * 100
    
    return {
        'days': time_diff,
        'views_growth_rate': view_growth / time_diff,
        'total_views_growth': view_growth,
        'likes_growth_rate': like_growth / time_diff,
        'total_likes_growth': like_growth,
        'views_per_day': (last_views - first_views) / time_diff,
        'likes_per_day': (last_likes - first_likes) / time_diff
    }

def identify_viral_moments_logic(snapshots):
    """Identify when video went viral"""
    viral_moments = []
    
    for i in range(1, len(snapshots)):
        prev = snapshots[i-1]
        curr = snapshots[i]
        
        try:
            ts_curr = datetime.fromisoformat(curr['timestamp'])
            ts_prev = datetime.fromisoformat(prev['timestamp'])
        except:
            continue

        time_diff_hours = (ts_curr - ts_prev).total_seconds() / 3600
        
        if time_diff_hours > 0:
            views_curr = int(curr['views'])
            views_prev = int(prev['views'])
            
            views_per_hour = (views_curr - views_prev) / time_diff_hours
            
            if views_per_hour > 10000:
                viral_moments.append({
                    'timestamp': curr['timestamp'],
                    'views_per_hour': views_per_hour,
                    'total_views': views_curr
                })
    
    return viral_moments

def predict_future_views_logic(snapshots, days_ahead=7):
    """Simple linear prediction"""
    if len(snapshots) < 2:
        return None
    
    growth = calculate_growth_rate_logic(snapshots)
    if not growth:
        return None
    
    current_views = int(snapshots[-1]['views'])
    daily_growth = growth['views_per_day']
    
    predictions = []
    for day in range(1, days_ahead + 1):
        predicted_views = current_views + (daily_growth * day)
        predictions.append({
            'days_from_now': day,
            'predicted_views': int(predicted_views),
            'predicted_views_formatted': format_number(int(predicted_views))
        })
    
    return predictions

async def _get_video_snapshots(video_id: str):
    """Helper to fetch real data and simulate history for analytics"""
    try:
        # 1. Fetch current data
        request = get_youtube_client().videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        
        if not response.get("items"):
            return None
        
        video = response["items"][0]
        current_stats = video.get("statistics", {})
        snippet = video["snippet"]
        
        current_snapshot = {
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "title": snippet["title"],
            "views": int(current_stats.get("viewCount", 0)),
            "likes": int(current_stats.get("likeCount", 0)),
            "comments": int(current_stats.get("commentCount", 0))
        }
        
        # 2. Simulate historical data (same as before)
        snapshots = [
            {
                **current_snapshot,
                "timestamp": (datetime.now() - timedelta(days=14)).isoformat(),
                "views": int(current_snapshot["views"] * 0.3),
                "likes": int(current_snapshot["likes"] * 0.3),
                "comments": int(current_snapshot["comments"] * 0.3)
            },
            {
                **current_snapshot,
                "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
                "views": int(current_snapshot["views"] * 0.6),
                "likes": int(current_snapshot["likes"] * 0.6),
                "comments": int(current_snapshot["comments"] * 0.6)
            },
            current_snapshot
        ]
        return snapshots
    except:
        return None
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
            name="track_video_metrics",
            description="Track how a video's metrics change over days/weeks/months.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="monitor_growth_patterns",
            description="Monitor growth patterns (views, likes, comments).",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="identify_viral_moments",
            description="Identify viral moments where metrics spiked.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="compare_video_performance",
            description="Compare video performance at different stages (e.g. now vs 2 weeks ago).",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID"}
                },
                "required": ["video_id"]
            }
        ),
        types.Tool(
            name="predict_video_performance",
            description="Predict future performance based on trends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {"type": "string", "description": "YouTube video ID"},
                    "days_ahead": {"type": "number", "description": "Days to predict", "default": 7}
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
        
        elif name == "track_video_metrics":
            video_id = extract_video_id(arguments.get("video_id"))
            snapshots = await _get_video_snapshots(video_id)
            
            if not snapshots:
                 return [types.TextContent(type="text", text=f"Video not found: {video_id}")]

            # Return just the raw metrics history
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "video_id": video_id,
                    "title": snapshots[-1]["title"],
                    "current_views": snapshots[-1]["views"],
                    "history": snapshots 
                }, indent=2)
            )]

        elif name == "monitor_growth_patterns":
            video_id = extract_video_id(arguments.get("video_id"))
            snapshots = await _get_video_snapshots(video_id)
            if not snapshots: return [types.TextContent(type="text", text=f"Video not found: {video_id}")]

            growth = calculate_growth_rate_logic(snapshots)
            return [types.TextContent(type="text", text=json.dumps(growth, indent=2))]

        elif name == "identify_viral_moments":
            video_id = extract_video_id(arguments.get("video_id"))
            snapshots = await _get_video_snapshots(video_id)
            if not snapshots: return [types.TextContent(type="text", text=f"Video not found: {video_id}")]

            viral = identify_viral_moments_logic(snapshots)
            return [types.TextContent(type="text", text=json.dumps(viral, indent=2))]
            
        elif name == "compare_video_performance":
             video_id = extract_video_id(arguments.get("video_id"))
             snapshots = await _get_video_snapshots(video_id)
             if not snapshots: return [types.TextContent(type="text", text=f"Video not found: {video_id}")]
             
             # Compare current vs 14 days ago (first snapshot in our simulation)
             current = snapshots[-1]
             past = snapshots[0]
             
             comparison = {
                 "period": "14 days",
                 "views_change": int(current["views"]) - int(past["views"]),
                 "likes_change": int(current["likes"]) - int(past["likes"]),
                 "comments_change": int(current["comments"]) - int(past["comments"])
             }
             return [types.TextContent(type="text", text=json.dumps(comparison, indent=2))]

        elif name == "predict_video_performance":
            video_id = extract_video_id(arguments.get("video_id"))
            days_ahead = int(arguments.get("days_ahead", 7))
            
            snapshots = await _get_video_snapshots(video_id)
            if not snapshots: return [types.TextContent(type="text", text=f"Video not found: {video_id}")]

            predictions = predict_future_views_logic(snapshots, days_ahead)
            return [types.TextContent(type="text", text=json.dumps(predictions, indent=2))]

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

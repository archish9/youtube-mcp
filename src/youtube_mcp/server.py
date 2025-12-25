import os
import sys
import json
from typing import Any
from datetime import datetime
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

"""
YouTube MCP Demo Client
Demonstrates all available tools with practical examples

Usage:
    python demo_client.py          # Run all demos
    python demo_client.py video    # Run specific demo
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Fix Windows encoding for Unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

# Determine the correct Python executable
# Prefer venv Python if it exists, otherwise use sys.executable
venv_python = project_root / "venv" / "Scripts" / "python.exe"
if not venv_python.exists():
    venv_python = project_root / "venv" / "bin" / "python"  # Linux/Mac
if venv_python.exists():
    python_executable = str(venv_python)
else:
    python_executable = sys.executable

# Server configuration - run server.py directly
server_script = project_root / "src" / "youtube_mcp" / "server.py"
SERVER_PARAMS = StdioServerParameters(
    command=python_executable,
    args=[str(server_script)],
    cwd=str(project_root),
    env={
        **os.environ,
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY", ""),
        "PYTHONPATH": str(project_root / "src")
    }
)


async def demo_video_info():
    """Demo: Get video information"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("=" * 70)
            print("DEMO: Get Video Information")
            print("=" * 70)
            
            # Example 1: Using video ID
            result = await session.call_tool(
                "get_video_info",
                arguments={"video_id": "dQw4w9WgXcQ"}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Channel: {data['channel']['name']}")
            print(f"Views: {data['statistics']['views_formatted']}")
            print(f"Likes: {data['statistics']['likes_formatted']}")
            print(f"Duration: {data['duration']}")
            print(f"Published: {data['published_at']}")
            
            # Example 2: Using full URL
            print("\n" + "-" * 70)
            result = await session.call_tool(
                "get_video_info",
                arguments={"video_id": "https://www.youtube.com/watch?v=9bZkp7q19f0"}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Channel: {data['channel']['name']}")
            print(f"Views: {data['statistics']['views_formatted']}")


async def demo_video_transcript():
    """Demo: Get video transcript"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Get Video Transcript")
            print("=" * 70)
            
            # Get transcript
            result = await session.call_tool(
                "get_video_transcript",
                arguments={
                    "video_id": "dQw4w9WgXcQ",
                    "language": "en"
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo ID: {data['video_id']}")
            print(f"Language: {data['language']}")
            print(f"\nFirst 5 transcript entries:")
            
            for i, entry in enumerate(data['transcript'][:5]):
                print(f"\n[{entry['timestamp']}] {entry['text']}")
            
            print(f"\n\nFull text (first 500 chars):")
            print(data['full_text'][:500] + "...")


async def demo_video_comments():
    """Demo: Get video comments"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Get Video Comments")
            print("=" * 70)
            
            # Get comments
            result = await session.call_tool(
                "get_video_comments",
                arguments={
                    "video_id": "dQw4w9WgXcQ",
                    "max_results": 10,
                    "order": "relevance"
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nTotal comments retrieved: {data['total_comments']}")
            print("\nTop 5 comments:")
            
            for i, comment in enumerate(data['comments'][:5], 1):
                print(f"\n{i}. {comment['author']}")
                print(f"   Likes: {comment['likes']} | Replies: {comment['reply_count']}")
                text_preview = comment['text'][:100] + "..." if len(comment['text']) > 100 else comment['text']
                print(f"   {text_preview}")


async def demo_search_videos():
    """Demo: Search for videos"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Search Videos")
            print("=" * 70)
            
            # Search for Python tutorials
            result = await session.call_tool(
                "search_videos",
                arguments={
                    "query": "python tutorial for beginners",
                    "max_results": 5,
                    "order": "viewCount"
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nSearch query: {data['query']}")
            print(f"Results found: {data['total_results']}")
            print("\nTop 5 videos:")
            
            for i, video in enumerate(data['videos'], 1):
                print(f"\n{i}. {video['title']}")
                print(f"   Channel: {video['channel']}")
                print(f"   URL: {video['url']}")


async def demo_channel_info():
    """Demo: Get channel information"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Get Channel Info")
            print("=" * 70)
            
            # Get channel info
            result = await session.call_tool(
                "get_channel_info",
                arguments={"channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA"}  # MrBeast
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nChannel: {data['title']}")
            print(f"Subscribers: {data['statistics']['subscribers_formatted']}")
            print(f"Total Views: {data['statistics']['total_views_formatted']}")
            print(f"Video Count: {data['statistics']['video_count']}")
            print(f"Country: {data['country']}")
            print(f"URL: {data['url']}")


async def demo_channel_videos():
    """Demo: Get channel videos"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Get Channel Videos")
            print("=" * 70)
            
            # Get recent videos
            result = await session.call_tool(
                "get_channel_videos",
                arguments={
                    "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
                    "max_results": 5
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nChannel ID: {data['channel_id']}")
            print(f"Videos retrieved: {data['total_videos']}")
            print("\nRecent videos:")
            
            for i, video in enumerate(data['videos'], 1):
                print(f"\n{i}. {video['title']}")
                print(f"   Published: {video['published_at']}")
                print(f"   URL: {video['url']}")


async def demo_trending_videos():
    """Demo: Get trending videos"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Get Trending Videos")
            print("=" * 70)
            
            # Get trending videos in US
            result = await session.call_tool(
                "get_trending_videos",
                arguments={
                    "region_code": "US",
                    "max_results": 5
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nRegion: {data['region']}")
            print(f"Videos found: {data['total_videos']}")
            print("\nTop 5 trending:")
            
            for i, video in enumerate(data['videos'], 1):
                print(f"\n{i}. {video['title']}")
                print(f"   Channel: {video['channel']}")
                print(f"   Views: {video['views_formatted']}")
                print(f"   Likes: {video['likes']}")


async def demo_playlist_info():
    """Demo: Get playlist information"""
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "=" * 70)
            print("DEMO: Get Playlist Info")
            print("=" * 70)
            
            # Get playlist info
            result = await session.call_tool(
                "get_playlist_info",
                arguments={
                    "playlist_id": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
                    "max_results": 5
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nPlaylist: {data['title']}")
            print(f"Channel: {data['channel']}")
            print(f"Total Videos: {data['total_videos']}")
            print(f"Videos Retrieved: {data['videos_retrieved']}")
            print("\nFirst 5 videos:")
            
            for i, video in enumerate(data['videos'][:5], 1):
                print(f"\n{i}. {video['title']}")
                print(f"   Position: {video['position']}")
                print(f"   URL: {video['url']}")


async def run_all_demos():
    """Run all demonstrations"""
    demos = [
        ("Video Information", demo_video_info),
        ("Video Transcript", demo_video_transcript),
        ("Video Comments", demo_video_comments),
        ("Search Videos", demo_search_videos),
        ("Channel Info", demo_channel_info),
        ("Channel Videos", demo_channel_videos),
        ("Trending Videos", demo_trending_videos),
        ("Playlist Info", demo_playlist_info),
    ]
    
    for name, demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(2)  # Rate limiting
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
    
    print("\n" + "=" * 70)
    print("[DONE] All demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    demo_map = {
        "video": demo_video_info,
        "transcript": demo_video_transcript,
        "comments": demo_video_comments,
        "search": demo_search_videos,
        "channel": demo_channel_info,
        "videos": demo_channel_videos,
        "trending": demo_trending_videos,
        "playlist": demo_playlist_info,
    }
    
    if len(sys.argv) > 1:
        # Run specific demo
        demo_name = sys.argv[1]
        if demo_name in demo_map:
            print(f"Running demo: {demo_name}")
            asyncio.run(demo_map[demo_name]())
        else:
            print(f"Unknown demo: {demo_name}")
            print(f"Available: {', '.join(demo_map.keys())}")
    else:
        # Run all demos
        asyncio.run(run_all_demos())

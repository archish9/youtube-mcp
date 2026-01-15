"""
Advanced Features Individual Examples
Test each advanced tool individually with command-line arguments

Usage:
    python test_advanced.py channels [query]
    python test_advanced.py playlists [channel_id]
    python test_advanced.py related [video_id]
    python test_advanced.py categories [region]
    python test_advanced.py replies [comment_id]
    python test_advanced.py live [video_id]
    python test_advanced.py most_liked [query]
    python test_advanced.py most_viewed [query]
    python test_advanced.py all [video_id]
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
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
load_dotenv(project_root / ".env")

# Determine the correct Python executable
venv_python = project_root / "venv" / "Scripts" / "python.exe"
if not venv_python.exists():
    venv_python = project_root / "venv" / "bin" / "python"
if venv_python.exists():
    python_executable = str(venv_python)
else:
    python_executable = sys.executable

# Server configuration
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

DEFAULT_VIDEO_ID = "dQw4w9WgXcQ"  # Rick Roll

async def test_search_channels(query="Google Developers"):
    print("=" * 70)
    print(f"Testing: search_channels (Query: {query})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "search_channels", 
                arguments={"query": query, "max_results": 2}
            )
            print(result.content[0].text)

async def test_channel_playlists(channel_id="UC_x5XG1OV2P6uZZ5FSM9Ttw"): # Google Developers
    print("=" * 70)
    print(f"Testing: get_channel_playlists (Channel: {channel_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_channel_playlists", 
                arguments={"channel_id": channel_id, "max_results": 2}
            )
            print(result.content[0].text)

async def test_related_videos(video_id=DEFAULT_VIDEO_ID):
    print("=" * 70)
    print(f"Testing: get_related_videos (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_related_videos", 
                arguments={"video_id": video_id, "max_results": 2}
            )
            print(result.content[0].text)

async def test_video_categories(region="US"):
    print("=" * 70)
    print(f"Testing: get_video_categories (Region: {region})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_video_categories", 
                arguments={"region_code": region}
            )
            # Truncate output for readability
            data = json.loads(result.content[0].text)
            print(f"Total Categories: {data.get('count', 0)}")
            if data.get('categories'):
                print(f"First Category: {data['categories'][0]}")

async def test_comment_replies(comment_id=None):
    if not comment_id:
        print("No comment_id provided. Fetching a comment from default video first...")
        # Helper to get a comment ID
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool("get_video_comments", arguments={"video_id": DEFAULT_VIDEO_ID, "max_results": 1})
                data = json.loads(res.content[0].text)
                if data.get("comments"):
                    comment_id = data["comments"][0]["id"]
                    print(f"Using Comment ID: {comment_id}")
                else:
                    print("Could not find a comment to test replies.")
                    return

    print("=" * 70)
    print(f"Testing: get_comment_replies (Comment: {comment_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_comment_replies", 
                arguments={"comment_id": comment_id, "max_results": 2}
            )
            print(result.content[0].text)

async def test_live_stream_info(video_id=DEFAULT_VIDEO_ID):
    print("=" * 70)
    print(f"Testing: get_live_stream_info (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_live_stream_info", 
                arguments={"video_id": video_id}
            )
            print(result.content[0].text)

async def test_most_liked(query="Google Developers"):
    print("=" * 70)
    print(f"Testing: get_most_liked_video (Query: {query})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_most_liked_video", 
                arguments={"query": query}
            )
            print(result.content[0].text)

async def test_most_viewed(query="Google Developers"):
    print("=" * 70)
    print(f"Testing: get_most_viewed_video (Query: {query})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_most_viewed_video", 
                arguments={"query": query}
            )
            print(result.content[0].text)

async def run_all_tests(video_id=DEFAULT_VIDEO_ID):
    """Run all tests sequentially"""
    await test_search_channels()
    print()
    await test_channel_playlists()
    print()
    await test_related_videos(video_id)
    print()
    await test_video_categories()
    print()
    await test_comment_replies()
    print()
    await test_live_stream_info(video_id)
    print()
    await test_most_liked("Keka HR")
    print()
    await test_most_viewed("Keka HR")

if __name__ == "__main__":
    command = "all"
    arg = DEFAULT_VIDEO_ID
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    
    if len(sys.argv) > 2:
        arg = sys.argv[2]
    
    test_map = {
        "channels": lambda: test_search_channels(arg if len(sys.argv) > 2 else "Google Developers"),
        "playlists": lambda: test_channel_playlists(arg if len(sys.argv) > 2 else "UC_x5XG1OV2P6uZZ5FSM9Ttw"),
        "related": lambda: test_related_videos(arg),
        "categories": lambda: test_video_categories(arg if len(sys.argv) > 2 else "US"),
        "replies": lambda: test_comment_replies(arg if len(sys.argv) > 2 else None),
        "live": lambda: test_live_stream_info(arg),
        "most_liked": lambda: test_most_liked(arg if len(sys.argv) > 2 else "Google Developers"),
        "most_viewed": lambda: test_most_viewed(arg if len(sys.argv) > 2 else "Google Developers"),
        "all": lambda: run_all_tests(arg)
    }
    
    if command in test_map:
        asyncio.run(test_map[command]())
    else:
        print(f"Unknown command: {command}")
        print("Available commands: channels, playlists, related, categories, replies, live, most_liked, most_viewed, all")

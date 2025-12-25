"""
YouTube MCP Individual Examples
Test each tool individually with command-line arguments

Usage:
    python individual_examples.py search
    python individual_examples.py video
    python individual_examples.py transcript
    python individual_examples.py comments
    python individual_examples.py channel
    python individual_examples.py videos
    python individual_examples.py trending
    python individual_examples.py playlist
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


async def test_search():
    """Test search_videos tool"""
    print("=" * 70)
    print("Testing: search_videos")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
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


async def test_video_info():
    """Test get_video_info tool"""
    print("=" * 70)
    print("Testing: get_video_info")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Using a popular video
            result = await session.call_tool(
                "get_video_info",
                arguments={"video_id": "dQw4w9WgXcQ"}
            )
            
            # Get raw response
            raw_text = result.content[0].text
            
            # Check if it's an error message
            if raw_text.startswith("Error:"):
                print(f"\n[ERROR] {raw_text}")
                return
            
            try:
                data = json.loads(raw_text)
                print(f"\nVideo: {data['title']}")
                print(f"Channel: {data['channel']['name']}")
                print(f"Views: {data['statistics']['views_formatted']}")
                print(f"Likes: {data['statistics']['likes_formatted']}")
                print(f"Duration: {data['duration']}")
                print(f"Published: {data['published_at']}")
            except json.JSONDecodeError:
                print(f"\n[ERROR] Failed to parse response as JSON:")
                print(f"Raw response: {raw_text[:500]}")


async def test_transcript():
    """Test get_video_transcript tool"""
    print("=" * 70)
    print("Testing: get_video_transcript")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_video_transcript",
                arguments={
                    "video_id": "dQw4w9WgXcQ",
                    "language": "en"
                }
            )
            
            raw_text = result.content[0].text
            
            # Check if it's an error message
            if raw_text.startswith("Error:") or raw_text.startswith("Transcripts are disabled") or raw_text.startswith("No transcript found"):
                print(f"\n[INFO] {raw_text}")
                return
            
            try:
                data = json.loads(raw_text)
                print(f"\nVideo ID: {data['video_id']}")
                print(f"Language: {data['language']}")
                print(f"\nFirst 5 transcript entries:")
                
                for i, entry in enumerate(data['transcript'][:5]):
                    print(f"\n[{entry['timestamp']}] {entry['text']}")
                
                print(f"\n\nFull text (first 300 chars):")
                print(data['full_text'][:300] + "...")
            except json.JSONDecodeError:
                print(f"\n[ERROR] Failed to parse response as JSON:")
                print(f"Raw response: {raw_text[:500]}")


async def test_comments():
    """Test get_video_comments tool"""
    print("=" * 70)
    print("Testing: get_video_comments")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_video_comments",
                arguments={
                    "video_id": "dQw4w9WgXcQ",
                    "max_results": 5,
                    "order": "relevance"
                }
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nTotal comments retrieved: {data['total_comments']}")
            print("\nTop comments:")
            
            for i, comment in enumerate(data['comments'], 1):
                print(f"\n{i}. {comment['author']}")
                print(f"   Likes: {comment['likes']} | Replies: {comment['reply_count']}")
                text_preview = comment['text'][:100] + "..." if len(comment['text']) > 100 else comment['text']
                print(f"   {text_preview}")


async def test_channel_info():
    """Test get_channel_info tool"""
    print("=" * 70)
    print("Testing: get_channel_info")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # MrBeast channel ID
            result = await session.call_tool(
                "get_channel_info",
                arguments={"channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA"}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nChannel: {data['title']}")
            print(f"Subscribers: {data['statistics']['subscribers_formatted']}")
            print(f"Total Views: {data['statistics']['total_views_formatted']}")
            print(f"Video Count: {data['statistics']['video_count']}")
            print(f"Country: {data['country']}")
            print(f"URL: {data['url']}")


async def test_channel_videos():
    """Test get_channel_videos tool"""
    print("=" * 70)
    print("Testing: get_channel_videos")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
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


async def test_trending():
    """Test get_trending_videos tool"""
    print("=" * 70)
    print("Testing: get_trending_videos")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
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


async def test_playlist():
    """Test get_playlist_info tool"""
    print("=" * 70)
    print("Testing: get_playlist_info")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # A popular public playlist
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


async def run_all_tests():
    """Run all tests"""
    import traceback
    
    tests = [
        ("search", test_search),
        ("video", test_video_info),
        ("transcript", test_transcript),
        ("comments", test_comments),
        ("channel", test_channel_info),
        ("videos", test_channel_videos),
        ("trending", test_trending),
        ("playlist", test_playlist),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            await asyncio.sleep(1)  # Rate limiting
            print("\n[OK] Test passed\n")
            passed += 1
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
            traceback.print_exc()
            print()
            failed += 1
    
    print("=" * 70)
    print(f"[DONE] Tests completed: {passed} passed, {failed} failed")
    print("=" * 70)


if __name__ == "__main__":
    test_map = {
        "search": test_search,
        "video": test_video_info,
        "transcript": test_transcript,
        "comments": test_comments,
        "channel": test_channel_info,
        "videos": test_channel_videos,
        "trending": test_trending,
        "playlist": test_playlist,
        "all": run_all_tests,
    }
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name in test_map:
            print(f"Running test: {test_name}")
            asyncio.run(test_map[test_name]())
        else:
            print(f"Unknown test: {test_name}")
            print(f"Available: {', '.join(test_map.keys())}")
    else:
        print("Usage: python individual_examples.py <test_name>")
        print(f"Available tests: {', '.join(test_map.keys())}")
        print("\nRunning all tests...")
        asyncio.run(run_all_tests())

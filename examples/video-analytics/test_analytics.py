"""
Video Analytics Individual Examples
Test each analytics tool individually with command-line arguments

Usage:
    python test_analytics.py analytics [video_id]
    python test_analytics.py engagement [video_id]
    python test_analytics.py score [video_id]
    python test_analytics.py compare [video_id1] [video_id2] ...
    python test_analytics.py potential [video_id]
    python test_analytics.py all [video_id]
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


async def test_get_analytics(video_id=DEFAULT_VIDEO_ID):
    """Test get_video_analytics tool"""
    print("=" * 70)
    print(f"Testing: get_video_analytics (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_video_analytics", 
                arguments={"video_id": video_id}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Channel: {data['channel']}")
            print(f"Views: {data['views_formatted']}")
            print(f"Likes: {data['likes_formatted']}")
            print(f"Comments: {data['comments_formatted']}")
            print(f"Like Rate: {data['like_rate']}%")
            print(f"Comment Rate: {data['comment_rate']}%")
            print(f"Engagement Score: {data['engagement_score']}")


async def test_analyze_engagement(video_id=DEFAULT_VIDEO_ID):
    """Test analyze_video_engagement tool"""
    print("=" * 70)
    print(f"Testing: analyze_video_engagement (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "analyze_video_engagement", 
                arguments={"video_id": video_id}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Views: {data['views']}")
            print("\nEngagement Analysis:")
            analysis = data['engagement_analysis']
            print(f"  Like Rate: {analysis['like_rate']} ({analysis['like_rating']})")
            print(f"  Comment Rate: {analysis['comment_rate']} ({analysis['comment_rating']})")
            print(f"  Engagement Score: {analysis['engagement_score']}")
            print(f"\nInterpretation: {data['interpretation']}")


async def test_performance_score(video_id=DEFAULT_VIDEO_ID):
    """Test get_video_performance_score tool"""
    print("=" * 70)
    print(f"Testing: get_video_performance_score (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "get_video_performance_score", 
                arguments={"video_id": video_id}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Performance Score: {data['performance_score']}/100")
            print(f"Grade: {data['grade']}")
            print(f"Summary: {data['summary']}")
            print("\nMetrics:")
            for key, value in data['metrics'].items():
                print(f"  {key}: {value}")


async def test_compare_videos(video_ids=None):
    """Test compare_videos tool"""
    if video_ids is None or len(video_ids) < 2:
        # Default: compare two popular videos
        video_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0"]  # Rick Roll vs Gangnam Style
    
    print("=" * 70)
    print(f"Testing: compare_videos ({len(video_ids)} videos)")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "compare_videos", 
                arguments={"video_ids": video_ids}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideos Compared: {data['videos_compared']}")
            print("\nRanking by Engagement:")
            for video in data['ranking_by_engagement']:
                print(f"  #{video['rank']}: {video['title'][:40]}...")
                print(f"       Views: {video['views']}, Score: {video['engagement_score']}")
            
            print("\nHighlights:")
            h = data['highlights']
            print(f"  Best Engagement: {h['best_engagement']['title'][:30]}... (Score: {h['best_engagement']['score']})")
            print(f"  Most Views: {h['most_views']['title'][:30]}... ({h['most_views']['views']})")
            print(f"  Best Like Rate: {h['best_like_rate']['title'][:30]}... ({h['best_like_rate']['like_rate']})")


async def test_analyze_potential(video_id=DEFAULT_VIDEO_ID):
    """Test analyze_video_potential tool"""
    print("=" * 70)
    print(f"Testing: analyze_video_potential (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "analyze_video_potential", 
                arguments={"video_id": video_id}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Channel: {data['channel']}")
            print(f"\nCurrent Metrics:")
            for key, value in data['current_metrics'].items():
                print(f"  {key}: {value}")
            
            print(f"\nQuality Signals:")
            for signal in data['quality_signals']:
                print(f"  + {signal}")
            
            print(f"\nAreas for Improvement:")
            for concern in data['areas_for_improvement']:
                print(f"  - {concern}")
            
            print(f"\nOverall Assessment: {data['overall_assessment']}")


async def run_all_tests(video_id=DEFAULT_VIDEO_ID):
    """Run all tests sequentially"""
    tests = [
        (test_get_analytics, [video_id]),
        (test_analyze_engagement, [video_id]),
        (test_performance_score, [video_id]),
        (test_compare_videos, [[video_id, "9bZkp7q19f0"]]),  # Compare with Gangnam Style
        (test_analyze_potential, [video_id])
    ]
    
    for test_func, args in tests:
        await test_func(*args)
        await asyncio.sleep(1)  # Rate limiting
        print()  # Spacer


if __name__ == "__main__":
    # Simple argument parsing
    command = "all"
    video_id = DEFAULT_VIDEO_ID
    video_ids = []
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    
    if len(sys.argv) > 2:
        video_id = sys.argv[2]
        # For compare, collect all remaining args as video IDs
        if command == "compare":
            video_ids = sys.argv[2:]
    
    test_map = {
        "analytics": lambda: test_get_analytics(video_id),
        "engagement": lambda: test_analyze_engagement(video_id),
        "score": lambda: test_performance_score(video_id),
        "compare": lambda: test_compare_videos(video_ids if video_ids else None),
        "potential": lambda: test_analyze_potential(video_id),
        "all": lambda: run_all_tests(video_id)
    }
    
    if command in test_map:
        asyncio.run(test_map[command]())
    else:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(test_map.keys())}")
        print("\nUsage:")
        print("  python test_analytics.py analytics [video_id]")
        print("  python test_analytics.py engagement [video_id]")
        print("  python test_analytics.py score [video_id]")
        print("  python test_analytics.py compare [video_id1] [video_id2] ...")
        print("  python test_analytics.py potential [video_id]")
        print("  python test_analytics.py all [video_id]")

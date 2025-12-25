"""
Video Analytics Individual Examples
Test each analytics tool individually with command-line arguments

Usage:
    python test_analytics.py metrics [video_id]
    python test_analytics.py growth [video_id]
    python test_analytics.py viral [video_id]
    python test_analytics.py compare [video_id]
    python test_analytics.py predict [video_id]
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

async def test_track_metrics(video_id=DEFAULT_VIDEO_ID):
    """Test track_video_metrics tool"""
    print("=" * 70)
    print(f"Testing: track_video_metrics (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "track_video_metrics", 
                arguments={"video_id": video_id}
            )
            
            data = json.loads(result.content[0].text)
            print(f"\nVideo: {data['title']}")
            print(f"Current Views: {data['current_views']}")
            print(f"History Points: {len(data['history'])}")


async def test_monitor_growth(video_id=DEFAULT_VIDEO_ID):
    """Test monitor_growth_patterns tool"""
    print("=" * 70)
    print(f"Testing: monitor_growth_patterns (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "monitor_growth_patterns", 
                arguments={"video_id": video_id}
            )
            
            growth = json.loads(result.content[0].text)
            if growth:
                print(f"\nTime Period: {growth['days']} days")
                print(f"Daily Growth Rate: {growth['views_growth_rate']:.2f}%")
                print(f"Total Views Growth: {growth['total_views_growth']:.1f}%")
                print(f"Avg Views Per Day: {int(growth['views_per_day'])}")


async def test_viral_moments(video_id=DEFAULT_VIDEO_ID):
    """Test identify_viral_moments tool"""
    print("=" * 70)
    print(f"Testing: identify_viral_moments (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "identify_viral_moments", 
                arguments={"video_id": video_id}
            )
            
            viral = json.loads(result.content[0].text)
            print(f"\nViral Moments Detected: {len(viral)}")
            for i, moment in enumerate(viral, 1):
                print(f"   {i}. {moment['timestamp']} ({int(moment['views_per_hour'])} views/hr)")


async def test_compare_performance(video_id=DEFAULT_VIDEO_ID):
    """Test compare_video_performance tool"""
    print("=" * 70)
    print(f"Testing: compare_video_performance (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "compare_video_performance", 
                arguments={"video_id": video_id}
            )
            
            comp = json.loads(result.content[0].text)
            print(f"\nComparison Period: {comp['period']}")
            print(f"Views Change: {comp['views_change']:+}")
            print(f"Likes Change: {comp['likes_change']:+}")
            print(f"Comments Change: {comp['comments_change']:+}")


async def test_predictions(video_id=DEFAULT_VIDEO_ID):
    """Test predict_video_performance tool"""
    print("=" * 70)
    print(f"Testing: predict_video_performance (Video: {video_id})")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "predict_video_performance", 
                arguments={"video_id": video_id, "days_ahead": 3}
            )
            
            predictions = json.loads(result.content[0].text)
            print("\nPredictions (Next 3 Days):")
            for pred in predictions:
                print(f"   Day +{pred['days_from_now']}: {pred['predicted_views_formatted']} views")


async def run_all_tests(video_id=DEFAULT_VIDEO_ID):
    """Run all tests sequentially"""
    tests = [
        test_track_metrics,
        test_monitor_growth,
        test_viral_moments,
        test_compare_performance,
        test_predictions
    ]
    
    for test_func in tests:
        await test_func(video_id)
        await asyncio.sleep(1)  # Rate limiting
        print()  # Spacer


if __name__ == "__main__":
    test_map = {
        "metrics": test_track_metrics,
        "growth": test_monitor_growth,
        "viral": test_viral_moments,
        "compare": test_compare_performance,
        "predict": test_predictions,
        "all": run_all_tests
    }
    
    # Simple argument parsing
    test_name = "all"
    video_id = DEFAULT_VIDEO_ID
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
    
    if len(sys.argv) > 2:
        video_id = sys.argv[2]
        
    if test_name in test_map:
        asyncio.run(test_map[test_name](video_id))
    else:
        print(f"Unknown command: {test_name}")
        print(f"Available commands: {', '.join(test_map.keys())}")
        print("Usage: python test_analytics.py <command> [video_id]")

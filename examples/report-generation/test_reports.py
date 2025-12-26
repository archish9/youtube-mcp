"""
Report Generation Individual Examples
Test each report generation tool individually with command-line arguments

Usage:
    python test_reports.py channel [channel_id] [period_days]
    python test_reports.py video [video_id]
    python test_reports.py all
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

DEFAULT_CHANNEL_ID = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # MrBeast
DEFAULT_VIDEO_ID = "dQw4w9WgXcQ"  # Rick Roll


async def test_channel_report(channel_id=DEFAULT_CHANNEL_ID, period_days=7):
    """Test generate_channel_report tool"""
    print("=" * 70)
    print(f"Testing: generate_channel_report")
    print(f"Channel: {channel_id}")
    print(f"Period: {period_days} days")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "generate_channel_report", 
                arguments={
                    "channel_id": channel_id,
                    "period_days": period_days,
                    "include_videos": True
                }
            )
            
            report = json.loads(result.content[0].text)
            
            print(f"\n{'='*60}")
            print(f"CHANNEL PERFORMANCE REPORT")
            print(f"{'='*60}")
            print(f"\nGenerated: {report['generated_at']}")
            print(f"Period: Last {report['period_days']} days")
            
            channel = report['channel']
            print(f"\n--- CHANNEL OVERVIEW ---")
            print(f"Channel: {channel['title']}")
            print(f"Subscribers: {channel['subscribers_formatted']}")
            print(f"Total Views: {channel['total_views_formatted']}")
            print(f"Total Videos: {channel['total_videos']}")
            
            summary = report['period_summary']
            print(f"\n--- PERIOD SUMMARY ---")
            print(f"Videos Published: {summary['videos_published']}")
            print(f"Total Views: {summary['total_views_formatted']}")
            print(f"Total Likes: {summary['total_likes_formatted']}")
            print(f"Avg Views per Video: {summary['avg_views_formatted']}")
            print(f"Avg Like Rate: {summary['avg_like_rate']}%")
            
            print(f"\n--- TOP PERFORMERS ---")
            print("By Views:")
            for i, v in enumerate(report['top_performers']['by_views'], 1):
                print(f"  {i}. {v['title'][:50]}... ({v['views']})")
            
            print("\nBy Engagement:")
            for i, v in enumerate(report['top_performers']['by_engagement'], 1):
                print(f"  {i}. {v['title'][:50]}... ({v['like_rate']})")
            
            if 'videos' in report:
                print(f"\n--- ALL VIDEOS ({len(report['videos'])}) ---")
                for i, v in enumerate(report['videos'][:5], 1):
                    print(f"\n{i}. {v['title'][:60]}...")
                    print(f"   Views: {v['views_formatted']} | Likes: {v['likes_formatted']} | Rate: {v['like_rate']}%")
                
                if len(report['videos']) > 5:
                    print(f"\n   ... and {len(report['videos']) - 5} more videos")


async def test_video_report(video_id=DEFAULT_VIDEO_ID):
    """Test generate_video_report tool"""
    print("=" * 70)
    print(f"Testing: generate_video_report")
    print(f"Video: {video_id}")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "generate_video_report", 
                arguments={"video_id": video_id}
            )
            
            report = json.loads(result.content[0].text)
            
            print(f"\n{'='*60}")
            print(f"VIDEO PERFORMANCE REPORT")
            print(f"{'='*60}")
            print(f"\nGenerated: {report['generated_at']}")
            
            video = report['video']
            print(f"\n--- VIDEO INFO ---")
            print(f"Title: {video['title']}")
            print(f"Channel: {video['channel']}")
            print(f"Published: {video['published_at']}")
            print(f"Duration: {video['duration']}")
            print(f"URL: {video['url']}")
            
            metrics = report['metrics']
            print(f"\n--- METRICS ---")
            print(f"Views: {metrics['views_formatted']}")
            print(f"Likes: {metrics['likes_formatted']}")
            print(f"Comments: {metrics['comments_formatted']}")
            print(f"Like Rate: {metrics['like_rate']}%")
            print(f"Comment Rate: {metrics['comment_rate']}%")
            print(f"Engagement Score: {metrics['engagement_score']}")
            
            performance = report['performance']
            print(f"\n--- PERFORMANCE ---")
            print(f"Score: {performance['score']}/100")
            print(f"Grade: {performance['grade']}")
            print(f"Like Rating: {performance['like_rating']}")
            print(f"Comment Rating: {performance['comment_rating']}")
            
            analysis = report['analysis']
            print(f"\n--- ANALYSIS ---")
            print(f"Overall Assessment: {analysis['overall_assessment']}")
            print("\nQuality Signals:")
            for signal in analysis['quality_signals']:
                print(f"  + {signal}")
            print("\nAreas for Improvement:")
            for concern in analysis['areas_for_improvement']:
                print(f"  - {concern}")


async def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "=" * 70)
    print("RUNNING ALL REPORT GENERATION TESTS")
    print("=" * 70 + "\n")
    
    await test_channel_report()
    await asyncio.sleep(1)
    print("\n")
    
    await test_video_report()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    command = "all"
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
    
    if command == "channel":
        channel_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CHANNEL_ID
        period_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        asyncio.run(test_channel_report(channel_id, period_days))
    elif command == "video":
        video_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_VIDEO_ID
        asyncio.run(test_video_report(video_id))
    elif command == "all":
        asyncio.run(run_all_tests())
    else:
        print(f"Unknown command: {command}")
        print("\nUsage:")
        print("  python test_reports.py channel [channel_id] [period_days]")
        print("  python test_reports.py video [video_id]")
        print("  python test_reports.py all")
        print("\nExamples:")
        print("  python test_reports.py channel UCX6OQ3DkcsbYNE6H8uQQuVA 30")
        print("  python test_reports.py video dQw4w9WgXcQ")

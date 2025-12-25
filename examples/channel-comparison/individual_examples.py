"""
Channel Comparison Tools - Individual Examples
Test each tool individually with command-line arguments

Usage:
    python individual_examples.py compare
    python individual_examples.py strategy
    python individual_examples.py benchmark
    python individual_examples.py advantages
    python individual_examples.py market
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

# Example channel IDs
DEFAULT_CHANNELS = [
    "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
    "UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie
]

def format_number(num):
    """Format large numbers"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


async def test_compare():
    """Test compare_channels tool"""
    print("=" * 70)
    print("Testing: compare_channels")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "compare_channels", 
                arguments={"channel_ids": DEFAULT_CHANNELS}
            )
            
            data = json.loads(result.content[0].text)
            channels = data.get("channels", [])
            
            print(f"\nComparing {len(channels)} channels:\n")
            
            for i, channel in enumerate(channels, 1):
                print(f"{i}. {channel['title']}")
                print(f"   Subscribers: {format_number(channel['subscribers'])}")
                print(f"   Total Views: {format_number(channel['total_views'])}")
                print(f"   Videos: {channel['video_count']:,}")
                print(f"   Avg Views/Video: {format_number(channel['avg_views_per_video'])}")
                print(f"   Country: {channel['country']}\n")


async def test_strategy():
    """Test analyze_content_strategy tool"""
    print("=" * 70)
    print("Testing: analyze_content_strategy")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "analyze_content_strategy", 
                arguments={"channel_id": DEFAULT_CHANNELS[0]}
            )
            
            strategy = json.loads(result.content[0].text)
            
            print(f"\nChannel: {strategy['title']}")
            print(f"\nContent Strategy Analysis:")
            print(f"   Total Videos: {strategy['total_videos']:,}")
            print(f"   Posting Frequency: {strategy['posting_frequency']}")
            print(f"   Est. Videos/Month: {strategy['estimated_videos_per_month']}")
            print(f"   Subscribers: {format_number(strategy['subscribers'])}")
            print(f"   Avg Views/Video: {format_number(strategy['avg_views_per_video'])}")


async def test_benchmark():
    """Test benchmark_performance tool"""
    print("=" * 70)
    print("Testing: benchmark_performance")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "benchmark_performance", 
                arguments={
                    "target_channel_id": DEFAULT_CHANNELS[0],
                    "competitor_channel_ids": [DEFAULT_CHANNELS[1]]
                }
            )
            
            data = json.loads(result.content[0].text)
            target = data.get("target")
            competitors = data.get("competitors", [])
            
            print(f"\nTarget Channel: {target['title']}")
            print(f"   Subscribers: {format_number(target['subscribers'])}")
            print(f"   Rank by Subscribers: #{target['rank_by_subscribers']}")
            print(f"   Rank by Engagement: #{target['rank_by_engagement']}")
            print(f"   Engagement Score: {target['engagement_score']:.2f}")
            
            print(f"\nCompetitors ({len(competitors)}):")
            for comp in competitors:
                print(f"   - {comp['title']}")
                print(f"     Subscribers: {format_number(comp['subscribers'])}")
                print(f"     Engagement: {comp['engagement_score']:.2f}")


async def test_advantages():
    """Test identify_competitive_advantages tool"""
    print("=" * 70)
    print("Testing: identify_competitive_advantages")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "identify_competitive_advantages", 
                arguments={
                    "channel_id": DEFAULT_CHANNELS[0],
                    "comparison_channel_ids": [DEFAULT_CHANNELS[1]]
                }
            )
            
            data = json.loads(result.content[0].text)
            
            print(f"\nChannel: {data['channel']}")
            
            print(f"\nCompetitive Advantages:")
            for adv in data['advantages']:
                print(f"   ✓ {adv}")
            
            print(f"\nWeaknesses:")
            for weak in data['weaknesses']:
                print(f"   ✗ {weak}")
            
            print(f"\nKey Metrics:")
            metrics = data['metrics']
            print(f"   Subscribers: {format_number(metrics['subscribers'])}")
            print(f"   Avg Views/Video: {format_number(metrics['avg_views_per_video'])}")
            print(f"   View-to-Sub Ratio: {metrics['view_to_sub_ratio']:.2f}")


async def test_market():
    """Test track_market_share tool"""
    print("=" * 70)
    print("Testing: track_market_share")
    print("=" * 70)

    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "track_market_share", 
                arguments={"channel_ids": DEFAULT_CHANNELS}
            )
            
            data = json.loads(result.content[0].text)
            
            print(f"\nMarket Overview:")
            print(f"   Total Subscribers: {format_number(data['total_subscribers'])}")
            print(f"   Total Views: {format_number(data['total_views'])}")
            
            print(f"\nMarket Share Distribution:")
            for channel in data['channels']:
                print(f"\n   {channel['title']}")
                print(f"      Subscriber Share: {channel['subscriber_share_percent']:.2f}%")
                print(f"      View Share: {channel['view_share_percent']:.2f}%")


async def run_all_tests():
    """Run all tests"""
    import traceback
    
    tests = [
        ("compare", test_compare),
        ("strategy", test_strategy),
        ("benchmark", test_benchmark),
        ("advantages", test_advantages),
        ("market", test_market),
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
        "compare": test_compare,
        "strategy": test_strategy,
        "benchmark": test_benchmark,
        "advantages": test_advantages,
        "market": test_market,
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

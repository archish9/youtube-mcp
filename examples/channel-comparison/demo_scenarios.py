"""
Channel Comparison Demo - Comprehensive Examples
Demonstrates practical usage scenarios for channel comparison tools
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
load_dotenv(project_root / ".env")

# Python executable
venv_python = project_root / "venv" / "Scripts" / "python.exe"
if not venv_python.exists():
    venv_python = project_root / "venv" / "bin" / "python"
python_executable = str(venv_python) if venv_python.exists() else sys.executable

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

def format_number(num):
    """Format large numbers"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


async def scenario_1_compare_top_creators():
    """Scenario 1: Compare top YouTube creators"""
    print("\n" + "=" * 80)
    print("SCENARIO 1: Comparing Top YouTube Creators")
    print("=" * 80)
    print("\nUse Case: You want to analyze the top creators in a niche")
    print("Tool: compare_channels\n")
    
    # Example: Top creators (replace with real channel IDs)
    channels = [
        "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
        "UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie
    ]
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "compare_channels",
                arguments={"channel_ids": channels}
            )
            
            data = json.loads(result.content[0].text)
            
            print("📊 COMPARISON RESULTS:\n")
            for i, channel in enumerate(data["channels"], 1):
                print(f"{i}. {channel['title']}")
                print(f"   📈 Subscribers: {format_number(channel['subscribers'])}")
                print(f"   👁️  Total Views: {format_number(channel['total_views'])}")
                print(f"   🎬 Videos: {channel['video_count']:,}")
                print(f"   ⭐ Avg Views/Video: {format_number(channel['avg_views_per_video'])}")
                print(f"   🌍 Country: {channel['country']}\n")


async def scenario_2_analyze_competitor_strategy():
    """Scenario 2: Analyze a competitor's content strategy"""
    print("\n" + "=" * 80)
    print("SCENARIO 2: Analyzing Competitor Content Strategy")
    print("=" * 80)
    print("\nUse Case: Understand how often a competitor posts and their approach")
    print("Tool: analyze_content_strategy\n")
    
    channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # MrBeast
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "analyze_content_strategy",
                arguments={"channel_id": channel_id}
            )
            
            strategy = json.loads(result.content[0].text)
            
            print(f"📺 Channel: {strategy['title']}\n")
            print("📅 CONTENT STRATEGY:")
            print(f"   Posting Frequency: {strategy['posting_frequency']}")
            print(f"   Videos/Month: {strategy['estimated_videos_per_month']}")
            print(f"   Total Videos: {strategy['total_videos']:,}")
            print(f"\n📊 PERFORMANCE:")
            print(f"   Subscribers: {format_number(strategy['subscribers'])}")
            print(f"   Avg Views/Video: {format_number(strategy['avg_views_per_video'])}")
            
            print(f"\n💡 INSIGHTS:")
            if strategy['estimated_videos_per_month'] > 30:
                print("   ✓ High-frequency posting strategy")
            elif strategy['estimated_videos_per_month'] > 4:
                print("   ✓ Consistent weekly posting")
            else:
                print("   ✓ Quality-focused, less frequent posting")


async def scenario_3_benchmark_your_channel():
    """Scenario 3: Benchmark your channel against competitors"""
    print("\n" + "=" * 80)
    print("SCENARIO 3: Benchmarking Your Channel")
    print("=" * 80)
    print("\nUse Case: See how your channel ranks against competitors")
    print("Tool: benchmark_performance\n")
    
    target = "UCX6OQ3DkcsbYNE6H8uQQuVA"  # Your channel
    competitors = ["UC-lHJZR3Gqxm24_Vd_AJ5Yw"]  # Competitors
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "benchmark_performance",
                arguments={
                    "target_channel_id": target,
                    "competitor_channel_ids": competitors
                }
            )
            
            data = json.loads(result.content[0].text)
            target_data = data["target"]
            
            print(f"🎯 YOUR CHANNEL: {target_data['title']}\n")
            print("📊 RANKINGS:")
            print(f"   Subscriber Rank: #{target_data['rank_by_subscribers']} of {data['total_channels']}")
            print(f"   Engagement Rank: #{target_data['rank_by_engagement']} of {data['total_channels']}")
            
            print(f"\n📈 METRICS:")
            print(f"   Subscribers: {format_number(target_data['subscribers'])}")
            print(f"   Avg Views/Video: {format_number(target_data['avg_views_per_video'])}")
            print(f"   Engagement Score: {target_data['engagement_score']:.2f}")
            
            print(f"\n🏆 COMPETITORS:")
            for comp in data["competitors"]:
                print(f"   • {comp['title']}")
                print(f"     Subs: {format_number(comp['subscribers'])} | Engagement: {comp['engagement_score']:.2f}")


async def scenario_4_find_competitive_edge():
    """Scenario 4: Identify your competitive advantages"""
    print("\n" + "=" * 80)
    print("SCENARIO 4: Finding Your Competitive Edge")
    print("=" * 80)
    print("\nUse Case: Discover what makes your channel unique")
    print("Tool: identify_competitive_advantages\n")
    
    channel = "UCX6OQ3DkcsbYNE6H8uQQuVA"
    comparisons = ["UC-lHJZR3Gqxm24_Vd_AJ5Yw"]
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "identify_competitive_advantages",
                arguments={
                    "channel_id": channel,
                    "comparison_channel_ids": comparisons
                }
            )
            
            data = json.loads(result.content[0].text)
            
            print(f"📺 Channel: {data['channel']}\n")
            
            print("💪 COMPETITIVE ADVANTAGES:")
            if data['advantages']:
                for adv in data['advantages']:
                    print(f"   ✓ {adv}")
            else:
                print("   (None identified)")
            
            print(f"\n⚠️  AREAS FOR IMPROVEMENT:")
            if data['weaknesses']:
                for weak in data['weaknesses']:
                    print(f"   ✗ {weak}")
            else:
                print("   (None identified)")
            
            print(f"\n📊 KEY METRICS:")
            metrics = data['metrics']
            print(f"   Subscribers: {format_number(metrics['subscribers'])}")
            print(f"   Videos: {metrics['video_count']:,}")
            print(f"   Avg Views/Video: {format_number(metrics['avg_views_per_video'])}")


async def scenario_5_market_share_analysis():
    """Scenario 5: Analyze market share in your niche"""
    print("\n" + "=" * 80)
    print("SCENARIO 5: Market Share Analysis")
    print("=" * 80)
    print("\nUse Case: Understand audience distribution in your niche")
    print("Tool: track_market_share\n")
    
    channels = [
        "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
        "UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie
    ]
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "track_market_share",
                arguments={"channel_ids": channels}
            )
            
            data = json.loads(result.content[0].text)
            
            print("🌍 MARKET OVERVIEW:")
            print(f"   Total Subscribers: {format_number(data['total_subscribers'])}")
            print(f"   Total Views: {format_number(data['total_views'])}")
            
            print(f"\n📊 MARKET SHARE DISTRIBUTION:\n")
            
            # Sort by subscriber share
            sorted_channels = sorted(
                data['channels'],
                key=lambda x: x['subscriber_share_percent'],
                reverse=True
            )
            
            for i, channel in enumerate(sorted_channels, 1):
                print(f"{i}. {channel['title']}")
                print(f"   Subscriber Share: {channel['subscriber_share_percent']:.2f}%")
                print(f"   View Share: {channel['view_share_percent']:.2f}%")
                
                # Visual bar
                bar_length = int(channel['subscriber_share_percent'] / 2)
                bar = "█" * bar_length
                print(f"   {bar}\n")


async def run_all_scenarios():
    """Run all demonstration scenarios"""
    print("\n" + "=" * 80)
    print("🎬 CHANNEL COMPARISON TOOLS - COMPLETE DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo shows 5 practical scenarios for using channel comparison tools")
    
    scenarios = [
        scenario_1_compare_top_creators,
        scenario_2_analyze_competitor_strategy,
        scenario_3_benchmark_your_channel,
        scenario_4_find_competitive_edge,
        scenario_5_market_share_analysis
    ]
    
    for scenario in scenarios:
        await scenario()
        await asyncio.sleep(1)  # Rate limiting
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("  1. Replace example channel IDs with your own")
    print("  2. Customize the analysis for your niche")
    print("  3. Use insights to improve your content strategy")
    print()


if __name__ == "__main__":
    asyncio.run(run_all_scenarios())

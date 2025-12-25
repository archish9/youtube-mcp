"""
Quick Test - Channel Comparison Tools
Minimal test to verify setup is working correctly
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Setup
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

venv_python = project_root / "venv" / "Scripts" / "python.exe"
if not venv_python.exists():
    venv_python = project_root / "venv" / "bin" / "python"
python_executable = str(venv_python) if venv_python.exists() else sys.executable

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

# Test channels
TEST_CHANNELS = [
    "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
    "UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie
]


async def quick_test():
    """Quick test of all channel comparison tools"""
    print("=" * 70)
    print("QUICK TEST - Channel Comparison Tools")
    print("=" * 70)
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = [
                ("compare_channels", {"channel_ids": TEST_CHANNELS}),
                ("analyze_content_strategy", {"channel_id": TEST_CHANNELS[0]}),
                ("benchmark_performance", {
                    "target_channel_id": TEST_CHANNELS[0],
                    "competitor_channel_ids": [TEST_CHANNELS[1]]
                }),
                ("identify_competitive_advantages", {
                    "channel_id": TEST_CHANNELS[0],
                    "comparison_channel_ids": [TEST_CHANNELS[1]]
                }),
                ("track_market_share", {"channel_ids": TEST_CHANNELS}),
            ]
            
            for i, (tool_name, args) in enumerate(tools, 1):
                print(f"\n[{i}/5] Testing {tool_name}...", end=" ")
                try:
                    result = await session.call_tool(tool_name, arguments=args)
                    data = json.loads(result.content[0].text)
                    print("✓ PASSED")
                except Exception as e:
                    print(f"✗ FAILED: {e}")
            
            print("\n" + "=" * 70)
            print("✅ Quick test complete!")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(quick_test())

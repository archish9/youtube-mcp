"""
YouTube MCP Quick Test
A minimal test to verify the MCP server is working correctly

Usage:
    python quick_test.py
"""

import asyncio
import json
import os
import sys
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


async def quick_test():
    """Run a quick test of the YouTube MCP server"""
    
    print("=" * 60)
    print("YouTube MCP Quick Test")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        print("\n[ERROR] YOUTUBE_API_KEY not configured!")
        print("Please set your API key in the .env file:")
        print(f"  {project_root / '.env'}")
        print("\nExample: YOUTUBE_API_KEY=AIzaSy...")
        return
    
    print(f"\n[OK] API key configured (ends with ...{api_key[-4:]})")
    
    try:
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                print("[OK] Server connection established")
                
                await session.initialize()
                print("[OK] Session initialized")
                
                # List available tools
                tools = await session.list_tools()
                print(f"\n[OK] Available tools ({len(tools.tools)}):")
                for tool in tools.tools:
                    print(f"    - {tool.name}")
                
                # Quick test: Get video info
                print("\n" + "-" * 60)
                print("Testing get_video_info...")
                
                result = await session.call_tool(
                    "get_video_info",
                    arguments={"video_id": "dQw4w9WgXcQ"}
                )
                
                data = json.loads(result.content[0].text)
                print(f"\n[OK] Video found: {data['title']}")
                print(f"    Channel: {data['channel']['name']}")
                print(f"    Views: {data['statistics']['views_formatted']}")
                
                # Quick test: Search
                print("\n" + "-" * 60)
                print("Testing search_videos...")
                
                result = await session.call_tool(
                    "search_videos",
                    arguments={"query": "python", "max_results": 3}
                )
                
                data = json.loads(result.content[0].text)
                print(f"\n[OK] Search found {data['total_results']} results")
                for video in data['videos']:
                    print(f"    - {video['title'][:50]}...")
                
                print("\n" + "=" * 60)
                print("[SUCCESS] All quick tests passed!")
                print("=" * 60)
                print("\nYour YouTube MCP server is working correctly.")
                print("Try running the full demo: python demo_client.py")
                
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your API key is valid")
        print("2. Ensure YouTube Data API v3 is enabled in Google Cloud Console")
        print("3. Check for any network issues")


if __name__ == "__main__":
    asyncio.run(quick_test())

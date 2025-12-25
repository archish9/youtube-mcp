"""
YouTube MCP Interactive Demo
Interactive command-line interface to test YouTube MCP tools

Usage:
    python interactive_demo.py
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


def print_menu():
    """Print the interactive menu"""
    print("\n" + "=" * 60)
    print("YouTube MCP Interactive Demo")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  1. video <id_or_url>     - Get video information")
    print("  2. transcript <id>       - Get video transcript")
    print("  3. comments <id>         - Get video comments")
    print("  4. search <query>        - Search for videos")
    print("  5. channel <id>          - Get channel info")
    print("  6. channelvideos <id>    - Get channel videos")
    print("  7. trending [region]     - Get trending videos (default: US)")
    print("  8. playlist <id>         - Get playlist info")
    print("  9. help                  - Show this menu")
    print("  0. exit                  - Exit the demo")
    print("\nExample: video dQw4w9WgXcQ")
    print("=" * 60)


async def handle_command(session, command: str, args: list):
    """Handle a user command"""
    try:
        if command == "video":
            if not args:
                print("Usage: video <video_id_or_url>")
                return
            result = await session.call_tool(
                "get_video_info",
                arguments={"video_id": args[0]}
            )
            data = json.loads(result.content[0].text)
            print(f"\nTitle: {data['title']}")
            print(f"Channel: {data['channel']['name']}")
            print(f"Duration: {data['duration']}")
            print(f"Views: {data['statistics']['views_formatted']}")
            print(f"Likes: {data['statistics']['likes_formatted']}")
            print(f"Comments: {data['statistics']['comments_formatted']}")
            print(f"Published: {data['published_at']}")
            print(f"URL: {data['url']}")
        
        elif command == "transcript":
            if not args:
                print("Usage: transcript <video_id>")
                return
            result = await session.call_tool(
                "get_video_transcript",
                arguments={"video_id": args[0], "language": "en"}
            )
            data = json.loads(result.content[0].text)
            print(f"\nTranscript for: {data['video_id']}")
            print(f"Language: {data['language']}")
            print(f"\nFirst 10 entries:")
            for entry in data['transcript'][:10]:
                print(f"[{entry['timestamp']}] {entry['text']}")
            print(f"\n... Total segments: {len(data['transcript'])}")
        
        elif command == "comments":
            if not args:
                print("Usage: comments <video_id>")
                return
            result = await session.call_tool(
                "get_video_comments",
                arguments={"video_id": args[0], "max_results": 10}
            )
            data = json.loads(result.content[0].text)
            print(f"\nComments for video: {data['video_id']}")
            print(f"Retrieved: {data['total_comments']} comments\n")
            for i, comment in enumerate(data['comments'], 1):
                text = comment['text'][:100] + "..." if len(comment['text']) > 100 else comment['text']
                print(f"{i}. {comment['author']} ({comment['likes']} likes)")
                print(f"   {text}\n")
        
        elif command == "search":
            if not args:
                print("Usage: search <query>")
                return
            query = " ".join(args)
            result = await session.call_tool(
                "search_videos",
                arguments={"query": query, "max_results": 10}
            )
            data = json.loads(result.content[0].text)
            print(f"\nSearch results for: {data['query']}")
            print(f"Found: {data['total_results']} results\n")
            for i, video in enumerate(data['videos'], 1):
                print(f"{i}. {video['title']}")
                print(f"   Channel: {video['channel']}")
                print(f"   URL: {video['url']}\n")
        
        elif command == "channel":
            if not args:
                print("Usage: channel <channel_id>")
                return
            result = await session.call_tool(
                "get_channel_info",
                arguments={"channel_id": args[0]}
            )
            data = json.loads(result.content[0].text)
            print(f"\nChannel: {data['title']}")
            print(f"Subscribers: {data['statistics']['subscribers_formatted']}")
            print(f"Total Views: {data['statistics']['total_views_formatted']}")
            print(f"Video Count: {data['statistics']['video_count']}")
            print(f"Country: {data['country']}")
            print(f"URL: {data['url']}")
        
        elif command == "channelvideos":
            if not args:
                print("Usage: channelvideos <channel_id>")
                return
            result = await session.call_tool(
                "get_channel_videos",
                arguments={"channel_id": args[0], "max_results": 10}
            )
            data = json.loads(result.content[0].text)
            print(f"\nRecent videos from channel: {data['channel_id']}")
            print(f"Retrieved: {data['total_videos']} videos\n")
            for i, video in enumerate(data['videos'], 1):
                print(f"{i}. {video['title']}")
                print(f"   Published: {video['published_at']}")
                print(f"   URL: {video['url']}\n")
        
        elif command == "trending":
            region = args[0] if args else "US"
            result = await session.call_tool(
                "get_trending_videos",
                arguments={"region_code": region, "max_results": 10}
            )
            data = json.loads(result.content[0].text)
            print(f"\nTrending videos in {data['region']}")
            print(f"Found: {data['total_videos']} videos\n")
            for i, video in enumerate(data['videos'], 1):
                print(f"{i}. {video['title']}")
                print(f"   Channel: {video['channel']}")
                print(f"   Views: {video['views_formatted']}\n")
        
        elif command == "playlist":
            if not args:
                print("Usage: playlist <playlist_id>")
                return
            result = await session.call_tool(
                "get_playlist_info",
                arguments={"playlist_id": args[0], "max_results": 10}
            )
            data = json.loads(result.content[0].text)
            print(f"\nPlaylist: {data['title']}")
            print(f"Channel: {data['channel']}")
            print(f"Total Videos: {data['total_videos']}")
            print(f"\nFirst {data['videos_retrieved']} videos:\n")
            for i, video in enumerate(data['videos'], 1):
                print(f"{i}. {video['title']}")
                print(f"   URL: {video['url']}\n")
        
        elif command == "help":
            print_menu()
        
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")
    
    except Exception as e:
        print(f"\n[ERROR] {e}")


async def run_interactive():
    """Run the interactive demo"""
    
    # Check API key
    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        print("\n[ERROR] YOUTUBE_API_KEY not configured!")
        print("Please set your API key in the .env file")
        return
    
    print_menu()
    
    try:
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n[OK] Connected to YouTube MCP server")
                
                while True:
                    try:
                        user_input = input("\n> ").strip()
                        
                        if not user_input:
                            continue
                        
                        parts = user_input.split()
                        command = parts[0].lower()
                        args = parts[1:] if len(parts) > 1 else []
                        
                        if command in ["exit", "quit", "0"]:
                            print("Goodbye!")
                            break
                        
                        await handle_command(session, command, args)
                    
                    except KeyboardInterrupt:
                        print("\nGoodbye!")
                        break
                    except EOFError:
                        print("\nGoodbye!")
                        break
    
    except Exception as e:
        print(f"\n[ERROR] Failed to connect: {e}")


if __name__ == "__main__":
    asyncio.run(run_interactive())

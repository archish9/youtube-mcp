# YouTube MCP Server

![YouTube MCP Banner](./resources/header-banner.png)

A powerful [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides AI assistants with comprehensive access to YouTube data — video metadata, transcripts, comments, channel analytics, and competitive analysis.

> 📺 **New to MCP?** Watch our [Introduction to YouTube MCP](./resources/YouTube_MCP__The_AI_Toolkit.mp4) video to learn how it works!

## What is YouTube MCP?

YouTube MCP is an MCP server that enables AI assistants like Claude, Cursor, and other MCP-compatible tools to interact with YouTube data. Instead of manually copying video information, your AI can directly:

- **Fetch video details** — titles, descriptions, view counts, likes, durations
- **Extract transcripts** — get full video transcripts with timestamps
- **Analyze comments** — retrieve and analyze audience feedback
- **Research channels** — explore channel statistics and content strategies
- **Track performance** — monitor video growth, identify viral moments, predict trends
- **Compare competitors** — benchmark channels and track market share

## Who Benefits?

| Audience | Use Cases |
|----------|-----------|
| **Content Creators** | Analyze competitor strategies, track video performance, optimize content |
| **Marketing Teams** | Research influencers, measure campaign ROI, generate reports |
| **Researchers** | Study content trends, analyze audience behavior, gather transcripts |
| **Investors** | Evaluate creator potential, compare channel performance, track growth |
| **Developers** | Build AI-powered YouTube tools, automate data collection |

## Features

### Core Tools (8 tools)
- **Video Info** — Get detailed metadata for any video
- **Transcripts** — Fetch captions in multiple languages
- **Comments** — Retrieve top comments with engagement data
- **Search** — Find videos by keyword
- **Channel Info** — Get channel statistics and details
- **Channel Videos** — List recent uploads
- **Trending** — Discover trending videos by region
- **Playlists** — Access playlist contents

### Video Analytics (5 tools)
- Get video metrics with engagement rates
- Analyze engagement quality
- Calculate performance scores
- Compare multiple videos
- Analyze content quality signals

### Channel Comparison (5 tools)
- Compare multiple channels
- Analyze content strategies
- Benchmark performance
- Identify competitive advantages
- Track market share

### Report Generation (2 tools)
- Generate comprehensive channel reports
- Generate detailed video performance reports

### Framework Integration
Want to use YouTube MCP with **LangChain**, **LlamaIndex**, or other AI frameworks?

See the [Framework Integration Guide](./examples/framework-integration/README.md) for:
- Creating LangChain/LlamaIndex tools from MCP
- Building RAG systems with video transcripts
- Multi-video Q&A and research assistants
- Content creation agents and course builders

---

## Installation

### Prerequisites

- **Python 3.10+**
- **YouTube Data API Key** ([Get one here](https://console.cloud.google.com/))

### Step 1: Get a YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Enable the **YouTube Data API v3**.
4. Go to **Credentials** → **Create Credentials** → **API Key**.
5. Copy your API key.

### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-username/youtube-mcp.git
cd youtube-mcp

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the package
pip install -e .
```

### Step 3: Configure API Key

Create a `.env` file in the project root:

```bash
YOUTUBE_API_KEY=your_api_key_here
```

### Step 4: Test the Installation

```bash
# Run a quick test
python examples/basic/quick_test.py
```

---

## Usage with AI Assistants

### Claude Desktop

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "youtube": {
      "command": "python",
      "args": ["-m", "youtube_mcp.server"],
      "cwd": "C:/path/to/youtube-mcp",
      "env": {
        "YOUTUBE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Alternative (using .env file):**
```json
{
  "mcpServers": {
    "youtube": {
      "command": "python",
      "args": ["-m", "youtube_mcp.server"],
      "cwd": "C:/path/to/youtube-mcp"
    }
  }
}
```

### Cursor IDE

Add to your Cursor settings (`.cursor/mcp.json` in your project or global settings):

```json
{
  "mcpServers": {
    "youtube": {
      "command": "python",
      "args": ["-m", "youtube_mcp.server"],
      "cwd": "C:/path/to/youtube-mcp",
      "env": {
        "YOUTUBE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

> **Note:** Replace `C:/path/to/youtube-mcp` with the actual path to your youtube-mcp directory.

---

## Quick Start

Once configured, you can ask your AI assistant:

- *"Get info about this YouTube video: https://youtube.com/watch?v=dQw4w9WgXcQ"*
- *"Fetch the transcript for video ID abc123"*
- *"Search for Python tutorial videos"*
- *"Compare these two channels: UCX6OQ3DkcsbYNE6H8uQQuVA and UC-lHJZR3Gqxm24_Vd_AJ5Yw"*
- *"Track the performance of my latest video"*
- *"What are the trending videos in the US right now?"*

---

## Examples

The `examples/` directory contains test scripts organized by feature:

| Folder | Description | README |
|--------|-------------|--------|
| `examples/basic/` | Core tools (video info, transcripts, search) | [View README](examples/basic/README.md) |
| `examples/video-analytics/` | Analytics tools (metrics, growth, predictions) | [View README](examples/video-analytics/README.md) |
| `examples/channel-comparison/` | Comparison tools (benchmark, market share) | [View README](examples/channel-comparison/README.md) |

```bash
# Run basic demos
python examples/basic/demo_client.py

# Test video analytics
python examples/video-analytics/test_analytics.py all

# Test channel comparison
python examples/channel-comparison/demo_scenarios.py
```

---

## API Quota

YouTube Data API has daily quota limits:

- **Free tier:** 10,000 units per day
- **Search operations:** 100 units each
- **Other operations:** 1 unit each

Monitor usage in [Google Cloud Console](https://console.cloud.google.com/apis/dashboard).

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "YOUTUBE_API_KEY not configured" | Create `.env` file with your API key |
| "quotaExceeded" | Wait 24 hours or request quota increase |
| "Video not found" | Check video ID and ensure video is public |
| "Transcripts disabled" | Video doesn't have captions available |
| "Connection closed" | Check server logs for errors |

---

## Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [MCP Documentation](https://modelcontextprotocol.io)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)

---

## License

MIT License - see LICENSE file for details.

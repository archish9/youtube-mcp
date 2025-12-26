# YouTube MCP Examples

This folder contains example scripts and documentation for all YouTube MCP tools. Each subfolder focuses on a specific feature area.

---

## Quick Start

1. **Install dependencies:**
   ```bash
   cd youtube-mcp
   pip install -e .
   ```

2. **Configure API Key:**
   Create a `.env` file in the project root:
   ```bash
   YOUTUBE_API_KEY=your_api_key_here
   ```

3. **Run any example:**
   ```bash
   python examples/basic/individual_examples.py all
   ```

---

## Features Overview

| Feature | Tools | Description |
|---------|-------|-------------|
| [Basic Tools](./basic/) | 8 | Core YouTube data retrieval (videos, channels, search, comments, transcripts) |
| [Video Analytics](./video-analytics/) | 5 | Video performance analysis and engagement metrics |
| [Channel Comparison](./channel-comparison/) | 5 | Compare and benchmark multiple YouTube channels |
| [Report Generation](./report-generation/) | 2 | Generate comprehensive performance reports |
| [Framework Integration](./framework-integration/) | Guide | Integrate with LangChain, LlamaIndex, and other AI frameworks |

**Total: 20 tools**

---

## Tool Reference

### Basic Tools (8)

| Tool | Description | Documentation |
|------|-------------|---------------|
| `get_video_info` | Get detailed video information | [README](./basic/README.md#1-get_video_info) |
| `get_video_transcript` | Fetch video captions/subtitles | [README](./basic/README.md#2-get_video_transcript) |
| `get_video_comments` | Retrieve video comments | [README](./basic/README.md#3-get_video_comments) |
| `search_videos` | Search for videos by keyword | [README](./basic/README.md#4-search_videos) |
| `get_channel_info` | Get channel statistics and details | [README](./basic/README.md#5-get_channel_info) |
| `get_channel_videos` | List recent channel uploads | [README](./basic/README.md#6-get_channel_videos) |
| `get_trending_videos` | Discover trending videos by region | [README](./basic/README.md#7-get_trending_videos) |
| `get_playlist_info` | Get playlist contents | [README](./basic/README.md#8-get_playlist_info) |

---

### Video Analytics Tools (5)

| Tool | Description | Documentation |
|------|-------------|---------------|
| `get_video_analytics` | Get current metrics with engagement rates | [README](./video-analytics/README.md#1-get_video_analytics) |
| `analyze_video_engagement` | Analyze engagement quality with ratings | [README](./video-analytics/README.md#2-analyze_video_engagement) |
| `get_video_performance_score` | Calculate 0-100 performance score | [README](./video-analytics/README.md#3-get_video_performance_score) |
| `compare_videos` | Compare multiple videos side-by-side | [README](./video-analytics/README.md#4-compare_videos) |
| `analyze_video_potential` | Analyze content quality signals | [README](./video-analytics/README.md#5-analyze_video_potential) |

---

### Channel Comparison Tools (5)

| Tool | Description | Documentation |
|------|-------------|---------------|
| `compare_channels` | Compare multiple channels side-by-side | [README](./channel-comparison/README.md#1-compare_channels) |
| `analyze_content_strategy` | Analyze posting frequency and patterns | [README](./channel-comparison/README.md#2-analyze_content_strategy) |
| `benchmark_performance` | Benchmark against competitors | [README](./channel-comparison/README.md#3-benchmark_performance) |
| `identify_competitive_advantages` | Find strengths and weaknesses | [README](./channel-comparison/README.md#4-identify_competitive_advantages) |
| `track_market_share` | Track audience distribution | [README](./channel-comparison/README.md#5-track_market_share) |

---

### Report Generation Tools (2)

| Tool | Description | Documentation |
|------|-------------|---------------|
| `generate_channel_report` | Comprehensive channel performance report | [README](./report-generation/README.md#1-generate_channel_report) |
| `generate_video_report` | Detailed video performance report | [README](./report-generation/README.md#2-generate_video_report) |

---

## Folder Structure

```
examples/
├── README.md                    # This file
├── basic/
│   ├── README.md                # Core tools documentation
│   ├── individual_examples.py   # Test each tool individually
│   ├── demo_client.py           # Interactive demo
│   └── quick_test.py            # Quick API verification
├── video-analytics/
│   ├── README.md                # Analytics tools documentation
│   └── test_analytics.py        # Test analytics tools
├── channel-comparison/
│   ├── README.md                # Comparison tools documentation
│   └── test_comparison.py       # Test comparison tools
├── report-generation/
│   ├── README.md                # Report tools documentation
│   └── test_reports.py          # Test report generation
└── framework-integration/
    └── README.md                # LangChain/LlamaIndex integration guide
```

---

## Common Use Cases

### Content Creators
```bash
# Analyze your video performance
python examples/video-analytics/test_analytics.py score YOUR_VIDEO_ID

# Generate weekly channel report
python examples/report-generation/test_reports.py channel YOUR_CHANNEL_ID 7
```

### Marketing Teams
```bash
# Compare competitor channels
python examples/channel-comparison/test_comparison.py compare CHANNEL1 CHANNEL2 CHANNEL3

# Generate campaign video report
python examples/report-generation/test_reports.py video VIDEO_ID
```

### Researchers
```bash
# Search for videos on a topic
python examples/basic/individual_examples.py search

# Get trending videos
python examples/basic/individual_examples.py trending
```

---

## API Quota

All tools use the YouTube Data API v3 (free tier: 10,000 units/day).

| Operation | Approximate Cost |
|-----------|-----------------|
| Video info | 1 unit |
| Channel info | 1 unit |
| Search | 100 units |
| Transcript | 0 units (uses separate API) |

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `YOUTUBE_API_KEY not configured` | Create `.env` file with your API key |
| `Video not found` | Verify the video ID is correct |
| `quotaExceeded` | Wait 24 hours or request quota increase |
| `Connection closed` | Check server.py path and Python environment |

---

## Links

- [Main README](../README.md) — Project overview and installation
- [Framework Integration Guide](./framework-integration/README.md) — LangChain/LlamaIndex integration
- [YouTube API Console](https://console.cloud.google.com/) — Get API key
- [YouTube Data API Docs](https://developers.google.com/youtube/v3) — Official API reference

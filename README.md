# YouTube MCP Server

A Model Context Protocol (MCP) server for YouTube data access - fetch video metadata, transcripts, comments, and more.

## Features

- **Video Information** - Get detailed video metadata (title, description, views, likes, duration)
- **Transcripts** - Fetch video transcripts/captions in multiple languages
- **Comments** - Retrieve top comments from videos
- **Search** - Search for videos by keyword
- **Channel Information** - Get channel details and statistics
- **Trending Videos** - Get trending videos by region
- **Playlist Information** - Get playlist details and videos

## Setup

### 1. Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**
4. Go to "Credentials" -> "Create Credentials" -> "API Key"
5. Copy your API key

### 2. Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd youtube-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
YOUTUBE_API_KEY=your_api_key_here
```

### 4. Test the Server

```bash
python -m youtube_mcp.server
```

## Usage with Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "youtube": {
      "command": "python",
      "args": ["-m", "youtube_mcp.server"],
      "env": {
        "YOUTUBE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

Or use the `.env` file:

```json
{
  "mcpServers": {
    "youtube": {
      "command": "python",
      "args": ["-m", "youtube_mcp.server"],
      "cwd": "/path/to/youtube-mcp"
    }
  }
}
```

## Available Tools

### 1. `get_video_info`
Get comprehensive video metadata.

**Parameters:**
- `video_id` (required): YouTube video ID or URL

### 2. `get_video_transcript`
Fetch video transcript/captions.

**Parameters:**
- `video_id` (required): YouTube video ID or URL
- `language` (optional): Language code (default: "en")

### 3. `get_video_comments`
Get top comments from a video.

**Parameters:**
- `video_id` (required): YouTube video ID or URL
- `max_results` (optional): Number of comments (1-100, default: 20)
- `order` (optional): "time" or "relevance" (default: "relevance")

### 4. `search_videos`
Search for videos by keyword.

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Number of results (1-50, default: 10)
- `order` (optional): Sort by date/rating/relevance/title/viewCount

### 5. `get_channel_info`
Get channel information and statistics.

**Parameters:**
- `channel_id` (required): YouTube channel ID or URL

### 6. `get_channel_videos`
List recent videos from a channel.

**Parameters:**
- `channel_id` (required): YouTube channel ID
- `max_results` (optional): Number of videos (1-50, default: 10)

### 7. `get_trending_videos`
Get trending videos by region.

**Parameters:**
- `region_code` (optional): Country code (default: "US")
- `category_id` (optional): Category ID (default: "0" for all)
- `max_results` (optional): Number of videos (1-50, default: 10)

### 8. `get_playlist_info`
Get playlist details and videos.

**Parameters:**
- `playlist_id` (required): YouTube playlist ID
- `max_results` (optional): Number of videos (1-50, default: 20)

## API Quota Information

YouTube Data API has daily quota limits:
- **Free tier**: 10,000 units per day
- Each operation costs different units (typically 1-100)
- Monitor usage in Google Cloud Console

**Cost per operation (approximate):**
- `get_video_info`: 1 unit
- `get_video_transcript`: 0 units (uses different API)
- `get_video_comments`: 1 unit
- `search_videos`: 100 units
- `get_channel_info`: 1 unit
- `get_trending_videos`: 1 unit

## Examples

See the `examples/basic/` directory for testing scripts:
- `individual_examples.py` - Test individual tools
- `demo_client.py` - Complete demonstration
- `quick_test.py` - Quick functionality test
- `interactive_demo.py` - Interactive demo

## Troubleshooting

### Error: "YOUTUBE_API_KEY environment variable is required"
**Solution:** Create `.env` file with your API key or set it in environment

### Error: "Transcripts are disabled for this video"
**Solution:** Some videos don't have captions. Try a different video.

### Error: "quotaExceeded"
**Solution:** You've hit the daily API quota. Wait 24 hours or request quota increase.

### Error: "Video not found"
**Solution:** Check video ID is correct and video is public/available

## License

MIT License - see LICENSE file for details

## Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [MCP Documentation](https://modelcontextprotocol.io)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)

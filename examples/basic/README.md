# YouTube MCP Basic Examples

This folder contains testing scripts for the **Core Tools** of the YouTube MCP server. These are foundational tools for fetching video metadata, transcripts, comments, channel information, and more.

## Prerequisites

1. **Install the project:**
   ```bash
   cd path/to/youtube-mcp
   pip install -e .
   ```

2. **Configure API Key:**
   Create a `.env` file in the project root:
   ```bash
   YOUTUBE_API_KEY=your_api_key_here
   ```

---

## Available Tools

This section describes all **8 Core Tools** available in the YouTube MCP server.

### 1. `get_video_info`

Get detailed metadata about a YouTube video.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or full URL |

**Returns:** Title, description, channel info, published date, duration, statistics (views, likes, comments), tags, thumbnail URL.

**Example:**
```bash
python examples/basic/individual_examples.py video
```

---

### 2. `get_video_transcript`

Fetch the transcript/captions of a YouTube video with timestamps.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or full URL |
| `language` | string | No | Language code (default: "en") |

**Returns:** Timestamped transcript entries and full text.

**Example:**
```bash
python examples/basic/individual_examples.py transcript
```

> **Note:** Not all videos have transcripts. Some creators disable captions.

---

### 3. `get_video_comments`

Retrieve top comments from a YouTube video.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or full URL |
| `max_results` | number | No | Number of comments (1-100, default: 20) |
| `order` | string | No | "time" or "relevance" (default: "relevance") |

**Returns:** Author, comment text, likes, published date, reply count.

**Example:**
```bash
python examples/basic/individual_examples.py comments
```

---

### 4. `search_videos`

Search for YouTube videos by keyword.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query |
| `max_results` | number | No | Number of results (1-50, default: 10) |
| `order` | string | No | Sort by: date, rating, relevance, title, viewCount |

**Returns:** Video ID, title, description, channel, published date, thumbnail, URL.

**Example:**
```bash
python examples/basic/individual_examples.py search
```

---

### 5. `get_channel_info`

Get information about a YouTube channel.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube channel ID or channel URL |

**Returns:** Channel title, description, custom URL, subscribers, total views, video count, country, thumbnail.

**Example:**
```bash
python examples/basic/individual_examples.py channel
```

---

### 6. `get_channel_videos`

List recent videos from a YouTube channel.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube channel ID |
| `max_results` | number | No | Number of videos (1-50, default: 10) |

**Returns:** List of recent videos with titles, descriptions, published dates, thumbnails.

**Example:**
```bash
python examples/basic/individual_examples.py videos
```

---

### 7. `get_trending_videos`

Get trending videos by region and category.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `region_code` | string | No | Country code like "US", "GB", "IN" (default: "US") |
| `category_id` | string | No | Category ID like "10" for Music (default: "0" for all) |
| `max_results` | number | No | Number of videos (1-50, default: 10) |

**Returns:** Trending videos with titles, channels, views, likes, thumbnails.

**Example:**
```bash
python examples/basic/individual_examples.py trending
```

---

### 8. `get_playlist_info`

Get information about a YouTube playlist and its videos.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_id` | string | Yes | YouTube playlist ID |
| `max_results` | number | No | Number of videos (1-50, default: 20) |

**Returns:** Playlist title, description, channel, total videos, and list of videos.

**Example:**
```bash
python examples/basic/individual_examples.py playlist
```

---

## How to Get a Video ID

The **Video ID** is a unique 11-character string that identifies a YouTube video.

### Method 1: From the Browser URL

1. Open any YouTube video in your browser.
2. Look at the address bar URL.
3. The Video ID is the text after `v=`.

**Example:**
```
URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Video ID: dQw4w9WgXcQ
```

### Method 2: From the Share Button

1. Click the **Share** button below the video.
2. Copy the shortened URL.
3. The Video ID is the last part of the link.

**Example:**
```
Share Link: https://youtu.be/dQw4w9WgXcQ
Video ID: dQw4w9WgXcQ
```

### Method 3: From YouTube Studio (Your Own Videos)

1. Go to [YouTube Studio](https://studio.youtube.com/).
2. Click **Content** in the sidebar.
3. Hover over any video and click the three dots → **Get shareable link**.
4. Extract the Video ID from the link.

### Finding Competitor Video IDs

1. Navigate to the competitor's channel.
2. Click on any of their videos.
3. Use Method 1 or 2 above to extract the Video ID.

---

## How to Get a Channel ID

The **Channel ID** is a unique string that identifies a YouTube channel (usually starts with `UC`).

### Method 1: From Your Own Channel

1. Go to [YouTube Account Advanced](https://www.youtube.com/account_advanced).
2. Your Channel ID is displayed on this page.

### Method 2: From Channel URL

1. Go to any YouTube channel.
2. Look at the URL in the address bar.
3. If the URL contains `/channel/`, the ID follows it.

**Example:**
```
URL: https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA
Channel ID: UCX6OQ3DkcsbYNE6H8uQQuVA
```

### Method 3: From Custom URL (@username)

If the channel uses a custom URL like `@MrBeast`:
1. Go to the channel page.
2. Right-click → **View Page Source** (or press Ctrl+U).
3. Search for `"channelId"` in the source.
4. Copy the ID value (starts with `UC`).

**Alternative:** Use a browser extension like "YouTube Channel ID Finder" or online tools.

### Method 4: From Any Video

1. Open any video from the channel.
2. Click on the channel name below the video title.
3. Use Method 2 to get the Channel ID from the channel page.

### Finding Competitor Channel IDs

1. Navigate to the competitor's YouTube channel.
2. Use any method above to extract their Channel ID.
3. Save the IDs for use in comparison tools.

---

## Available Scripts

### 1. `quick_test.py`
Minimal test to verify your setup.
```bash
python quick_test.py
```

### 2. `individual_examples.py`
Test individual tools with command-line arguments.
```bash
python examples/basic/individual_examples.py           # Run all tests
python examples/basic/individual_examples.py search    # Search videos
python examples/basic/individual_examples.py video     # Get video info
python examples/basic/individual_examples.py transcript # Get transcript
python examples/basic/individual_examples.py comments  # Get comments
python examples/basic/individual_examples.py channel   # Get channel info
python examples/basic/individual_examples.py videos    # Get channel videos
python examples/basic/individual_examples.py trending  # Get trending videos
python examples/basic/individual_examples.py playlist  # Get playlist info
```

### 3. `demo_client.py`
Complete demonstration of all tools.
```bash
python examples/basic/demo_client.py
python examples/basic/demo_client.py video
python examples/basic/demo_client.py transcript
python examples/basic/demo_client.py search
```

### 4. `interactive_demo.py`
Interactive command-line interface.
```bash
python examples/basic/interactive_demo.py
```
Commands:
```
> video dQw4w9WgXcQ
> search python tutorial
> trending US
> exit
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "YOUTUBE_API_KEY not configured" | Create a `.env` file with your API key |
| "Transcripts are disabled" | Try a different video that has captions |
| "quotaExceeded" | Wait 24 hours or request quota increase |
| "Video not found" | Check the Video ID is correct and video is public |
| "Channel not found" | Verify Channel ID is correct (should start with `UC`) |
| "Connection closed" | Check server logs for errors |

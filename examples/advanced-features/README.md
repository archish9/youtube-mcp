# Advanced Features Tools

This folder demonstrates **Advanced Discovery and Community Features** added to the YouTube MCP server. These tools enable deeper exploration of the YouTube ecosystem beyond basic video/channel lookups.

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

This section describes **8 Advanced Tools** available in the YouTube MCP server.

### 1. `search_channels`

Search for channels by keyword.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search keyword |
| `max_results` | integer | No | Max results (default 10) |

**Returns:**
- List of channels matching the query
- Channel details (ID, title, description, thumbnail)

**Use Cases:**
- Find channels in a specific niche
- Discovery and competitive analysis

---

### 2. `get_channel_playlists`

List playlists for a specific channel.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube Channel ID |
| `max_results` | integer | No | Max results (default 10) |

**Returns:**
- List of playlists (ID, title, item count)
- Thumbnail images

**Use Cases:**
- Explore channel content organization
- Bulk content retrieval planning

---

### 3. `get_related_videos`

Find videos related to a specific video (using title-based search fallback).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | Target Video ID |
| `max_results` | integer | No | Max results (default 10) |

**Returns:**
- List of related videos
- Titles, channel names, and published dates

**Use Cases:**
- Content discovery
- Recommendation simulation

---

### 4. `get_video_categories`

List standard video categories for a region.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `region_code` | string | No | ISO region code (default "US") |

**Returns:**
- List of category IDs and Titles
- Assignable status

**Use Cases:**
- Metadata validation
- Understanding regional content categorization

---

### 5. `get_comment_replies`

Fetch replies to a specific top-level comment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `comment_id` | string | Yes | Comment ID (e.g., from `get_video_comments`) |
| `max_results` | integer | No | Max results (default 20) |

**Returns:**
- List of replies
- Author, text, likes, timestamp

**Use Cases:**
- Deep community engagement analysis
- Thread tracking

---

### 6. `get_live_stream_info`

Get status and details for a live stream.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | Video ID of the stream |

**Returns:**
- Live status (`live`, `upcoming`, `none`)
- Concurrent viewers (if live)
- Start/End times

**Use Cases:**
- Monitoring live events
- Real-time analytics

---
 
### 7. `get_most_liked_video`
 
Find the most liked video for a channel or search query.
 
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Channel name or search query |
| `channel_id` | string | No | Optional: Specific YouTube channel ID |
 
**Returns:**
- Detailed metadata for the most liked video found
- Includes likes, views, duration, and URL
 
**Use Cases:**
- Identifying viral hits for a channel
- Content research and benchmarking
 
---
 
### 8. `get_most_viewed_video`
 
Find the most viewed video for a channel or search query.
 
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Channel name or search query |
| `channel_id` | string | No | Optional: Specific YouTube channel ID |
 
**Returns:**
- Detailed metadata for the most viewed video found
- Includes views, likes, duration, and URL
 
**Use Cases:**
- Analyzing long-term channel performance
- Identifying evergreen content
 
---

## Available Scripts

### `test_advanced.py`

Command-line interface to test each advanced tool.

**Usage:**
```bash
python examples/advanced-features/test_advanced.py <command> [args]
```

**Commands:**

| Command | Args | Description |
|---------|------|-------------|
| `channels` | `[query]` | Search channels |
| `playlists` | `[channel_id]` | Get channel playlists |
| `related` | `[video_id]` | Get related videos |
| `categories` | `[region]` | Get video categories |
| `replies` | `[comment_id]` | Get comment replies |
| `live` | `[video_id]` | Get live stream info |
| `most_liked` | `[query]` | Find most liked video |
| `most_viewed` | `[query]` | Find most viewed video |
| `all` | `[video_id]` | Run all tests |

**Examples:**
```bash
# Search channels
python examples/advanced-features/test_advanced.py channels "Python Programming"

# Get playlists
python examples/advanced-features/test_advanced.py playlists UC_x5XG1OV2P6uZZ5FSM9Ttw

# Get related
python examples/advanced-features/test_advanced.py related dQw4w9WgXcQ
 
# Find most liked video
python examples/advanced-features/test_advanced.py most_liked "Keka HR"
```

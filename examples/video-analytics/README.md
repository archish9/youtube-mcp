# Video Analytics Tools

This folder demonstrates the **Video Analytics Tools** integrated into the YouTube MCP server. These tools allow you to track video metrics over time, monitor growth patterns, identify viral moments, compare performance at different stages, and predict future performance.

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

This section describes all **5 Video Analytics Tools** available in the YouTube MCP server.

### 1. `track_video_metrics`

Track how a video's metrics (views, likes, comments) change over time.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |

**Returns:**
- `video_id`: The video identifier
- `title`: Video title
- `snapshots`: Array of historical data points with timestamps, views, likes, comments

**Use Cases:**
- Monitor your video's performance over days/weeks
- See how metrics evolved since publication
- Track the impact of promotion campaigns

**Example:**
```bash
python examples/video-analytics/test_analytics.py metrics
python examples/video-analytics/test_analytics.py metrics dQw4w9WgXcQ
```

---

### 2. `monitor_growth_patterns`

Calculate growth rates for views, likes, and comments over the analysis period.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |

**Returns:**
- `days`: Number of days in the analysis period
- `views_growth_rate`: Daily view growth percentage
- `total_views_growth`: Total view growth percentage
- `likes_growth_rate`: Daily like growth percentage
- `total_likes_growth`: Total like growth percentage
- `views_per_day`: Average new views per day
- `likes_per_day`: Average new likes per day

**Use Cases:**
- Understand if your video is growing or declining
- Compare growth rates across your videos
- Identify which content resonates best with your audience

**Example:**
```bash
python examples/video-analytics/test_analytics.py growth
python examples/video-analytics/test_analytics.py growth dQw4w9WgXcQ
```

---

### 3. `identify_viral_moments`

Detect periods when a video experienced viral growth (rapid spikes in views).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |

**Returns:**
- `viral_moments`: Array of detected viral periods with:
  - `timestamp`: When the spike occurred
  - `views_per_hour`: Rate of views during the spike
  - `total_views`: Total views at that moment

**Viral Detection Criteria:** Views per hour > 10,000

**Use Cases:**
- Identify when your video got shared on social media
- Detect external traffic sources (Reddit, Twitter, etc.)
- Understand what triggers viral growth

**Example:**
```bash
python examples/video-analytics/test_analytics.py viral
python examples/video-analytics/test_analytics.py viral dQw4w9WgXcQ
```

---

### 4. `compare_video_performance`

Compare a video's current performance against its past performance (e.g., now vs. 14 days ago).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |

**Returns:**
- `current`: Current snapshot (views, likes, comments)
- `past`: Snapshot from 14 days ago
- `growth`: Calculated growth between the two periods
- `performance_summary`: Text summary of performance

**Use Cases:**
- See how much your video has grown in the last 2 weeks
- Evaluate the effectiveness of recent promotions
- Compare old vs. new performance metrics

**Example:**
```bash
python examples/video-analytics/test_analytics.py compare
python examples/video-analytics/test_analytics.py compare dQw4w9WgXcQ
```

---

### 5. `predict_video_performance`

Predict future view counts based on current growth trends (linear projection).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID |
| `days_ahead` | number | No | Days to predict (default: 7) |

**Returns:**
- `predictions`: Array of predicted view counts for each day:
  - `days_from_now`: Day number (1, 2, 3...)
  - `predicted_views`: Estimated view count
  - `predicted_views_formatted`: Human-readable format (e.g., "1.2M")

**Use Cases:**
- Estimate when you'll hit a milestone (100K, 1M views)
- Set realistic expectations for video performance
- Plan content strategy based on projections

**Example:**
```bash
python examples/video-analytics/test_analytics.py predict
python examples/video-analytics/test_analytics.py predict dQw4w9WgXcQ
```

---

## How to Get a Video ID

The **Video ID** is an 11-character string that uniquely identifies a YouTube video.

### Method 1: From the Browser URL

1. Open any YouTube video in your browser.
2. Look at the URL in the address bar.
3. The Video ID is the text after `v=`.

**Example:**
```
URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Video ID: dQw4w9WgXcQ
```

### Method 2: From the Share Button

1. Click **Share** below the video.
2. Copy the shortened URL.
3. The Video ID is the last part.

**Example:**
```
Share Link: https://youtu.be/dQw4w9WgXcQ
Video ID: dQw4w9WgXcQ
```

### Method 3: From YouTube Studio (Your Own Videos)

1. Go to [YouTube Studio](https://studio.youtube.com/).
2. Click **Content** in the left sidebar.
3. Find your video in the list.
4. The Video ID is visible in the video details or URL.

### Finding Competitor Video IDs

1. Go to the competitor's YouTube channel.
2. Click on any of their videos.
3. Copy the Video ID from the URL using Method 1.
4. Save the IDs for tracking and comparison.

---

## Available Scripts

### `test_analytics.py`

Command-line interface to test each analytics tool.

**Usage:**
```bash
python examples/video-analytics/test_analytics.py <command> [video_id]
```

**Commands:**

| Command | Description |
|---------|-------------|
| `metrics` | Track historical metrics (views/likes/comments) |
| `growth` | Calculate daily growth rates and total growth |
| `viral` | Identify viral moments (spikes in view rate) |
| `compare` | Compare current performance vs. 14 days ago |
| `predict` | Predict future views for the next 7 days |
| `all` | **(Default)** Run all tests sequentially |

**Examples:**
```bash
# Run all analytics tests
python examples/video-analytics/test_analytics.py all

# Run specific analytics tool
python examples/video-analytics/test_analytics.py metrics
python examples/video-analytics/test_analytics.py growth
python examples/video-analytics/test_analytics.py viral
python examples/video-analytics/test_analytics.py compare
python examples/video-analytics/test_analytics.py predict

# Run with a specific Video ID
python examples/video-analytics/test_analytics.py all dQw4w9WgXcQ
python examples/video-analytics/test_analytics.py metrics dQw4w9WgXcQ
```

---

## How It Works

1. **Client**: The script connects to the MCP server using standard I/O.
2. **Request**: Sends a tool call (e.g., `track_video_metrics`) with the `video_id`.
3. **Server**: 
   - Fetches current live data from the YouTube API.
   - Simulates historical data points (for demonstration purposes).
   - Calculates analytics metrics.
   - Returns results in JSON format.
4. **Output**: The script formats the JSON into a readable console report.

> **Note:** Historical data is simulated based on current metrics. For true historical tracking, you would need to store snapshots in a database over time.

---

## Practical Use Cases

### For Content Creators
- Track which videos are growing fastest
- Identify when videos go viral
- Predict milestone achievements

### For Marketing Teams
- Measure campaign impact on video performance
- Track ROI on promotional efforts
- Report on content performance trends

### For Researchers
- Study video growth patterns
- Analyze viral content characteristics
- Track information spread

### For Investors
- Evaluate influencer growth trajectories
- Assess content creator potential
- Monitor portfolio creator performance

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "YOUTUBE_API_KEY not configured" | Create a `.env` file with your API key |
| "Video not found" | Verify the Video ID is correct and video is public |
| "quotaExceeded" | Wait 24 hours or request quota increase |
| "No data available" | The video may be too new for meaningful analytics |

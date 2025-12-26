# Video Analytics Tools

This folder demonstrates the **Video Analytics Tools** integrated into the YouTube MCP server. These tools analyze video performance using **real current data** from the YouTube API — no simulated or historical data.

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

### 1. `get_video_analytics`

Get current video metrics with calculated engagement rates.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or URL |

**Returns:**
- Video title, channel, published date, duration
- Views, likes, comments (raw and formatted)
- `like_rate`: Percentage of viewers who liked
- `comment_rate`: Percentage of viewers who commented
- `engagement_score`: Weighted engagement score

**Use Cases:**
- Get a complete snapshot of video performance
- Understand engagement rates at a glance
- Collect data for reports

---

### 2. `analyze_video_engagement`

Analyze engagement quality with ratings and interpretation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or URL |

**Returns:**
- Engagement analysis with ratings:
  - `like_rating`: Excellent / Good / Average / Below Average
  - `comment_rating`: High / Moderate / Low Engagement
- Human-readable interpretation

**Rating Criteria:**
| Like Rate | Rating |
|-----------|--------|
| ≥ 5% | Excellent |
| ≥ 3% | Good |
| ≥ 1% | Average |
| < 1% | Below Average |

**Use Cases:**
- Quickly assess video quality
- Compare engagement across videos
- Identify content that resonates with audiences

---

### 3. `get_video_performance_score`

Calculate a 0-100 performance score with letter grade.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or URL |

**Returns:**
- `performance_score`: 0-100 score
- `grade`: A, B, C, D, or F
- `summary`: Performance explanation
- Detailed metrics breakdown

**Grading Scale:**
| Score | Grade | Meaning |
|-------|-------|---------|
| 80-100 | A | Exceptional performance |
| 60-79 | B | Good, above average |
| 40-59 | C | Average performance |
| 20-39 | D | Below average |
| 0-19 | F | Poor performance |

**Use Cases:**
- Get a quick performance assessment
- Compare videos using a standardized score
- Track content quality over time

---

### 4. `compare_videos`

Compare multiple videos side-by-side with rankings.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_ids` | array | Yes | List of 2-10 video IDs to compare |

**Returns:**
- Videos ranked by engagement score
- Highlights:
  - Best engagement
  - Most views
  - Best like rate
- Side-by-side metrics for each video

**Use Cases:**
- Compare your videos against each other
- Benchmark against competitor videos
- Identify your best-performing content

**Example:**
```bash
# Compare 3 videos
python examples/video-analytics/test_analytics.py compare video1_id video2_id video3_id
```

---

### 5. `analyze_video_potential`

Analyze content quality signals and audience resonance.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or URL |

**Returns:**
- Current metrics
- `quality_signals`: Positive indicators (e.g., "High like-to-view ratio")
- `areas_for_improvement`: Concerns (e.g., "Low comment rate")
- `overall_assessment`: Strong / Average / Needs Improvement

**Quality Signals Detected:**
- High like-to-view ratio (≥5%)
- High comment rate (≥0.5%)
- Viral reach (>1M views)
- Strong reach (>100K views)

**Concerns Flagged:**
- Low like-to-view ratio (<1%)
- Low comment rate (<0.05%)
- Limited reach (<1K views)

**Use Cases:**
- Understand what's working in your content
- Get actionable improvement suggestions
- Evaluate video quality before promotion

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
| `analytics` | Get current metrics with engagement rates |
| `engagement` | Analyze engagement quality with ratings |
| `score` | Calculate performance score (0-100) |
| `compare` | Compare multiple videos |
| `potential` | Analyze content quality signals |
| `all` | Run all tests sequentially |

**Examples:**
```bash
# Get video analytics
python examples/video-analytics/test_analytics.py analytics dQw4w9WgXcQ

# Analyze engagement
python examples/video-analytics/test_analytics.py engagement dQw4w9WgXcQ

# Get performance score
python examples/video-analytics/test_analytics.py score dQw4w9WgXcQ

# Compare videos
python examples/video-analytics/test_analytics.py compare dQw4w9WgXcQ abc123 xyz789

# Analyze potential
python examples/video-analytics/test_analytics.py potential dQw4w9WgXcQ
```

---

## How It Works

All analytics tools use **real current data** from the YouTube Data API:

1. **Client**: Connects to the MCP server.
2. **Request**: Sends tool call with video ID.
3. **Server**: 
   - Fetches current video data via YouTube API
   - Calculates engagement metrics (like rate, comment rate)
   - Applies performance scoring algorithms
4. **Response**: Returns analysis in JSON format.

> **Note:** All data is real and fetched live from YouTube. There is no simulated or historical data. For historical tracking, you would need to store snapshots over time in a database.

---

## Practical Use Cases

### For Content Creators
- Analyze which videos perform best
- Understand engagement patterns
- Get actionable improvement suggestions

### For Marketing Teams
- Compare campaign video performance
- Benchmark against competitors
- Generate performance reports

### For Researchers
- Study video engagement patterns
- Analyze content quality metrics
- Compare videos across categories

---

## API Quota Information

Each tool call uses approximately **1-2 API quota units**:

| Tool | Quota Cost |
|------|------------|
| `get_video_analytics` | 1 unit |
| `analyze_video_engagement` | 1 unit |
| `get_video_performance_score` | 1 unit |
| `compare_videos` | 1 unit per video |
| `analyze_video_potential` | 1 unit |

**Daily Quota:** 10,000 units (free tier)

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "Video not found" | Verify the Video ID is correct and video is public |
| "YOUTUBE_API_KEY not configured" | Create a `.env` file with your API key |
| "quotaExceeded" | Wait 24 hours or request quota increase |

# Channel Comparison Tools

This folder demonstrates the **Channel Comparison Tools** integrated into the YouTube MCP server. These tools allow you to compare multiple YouTube channels, analyze content strategies, benchmark performance, identify competitive advantages, and track market share.

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
   DEFAULT_CHANNEL_ID=your_channel_id_here  # Optional: your channel for benchmarking
   ```

---

## Available Tools

This section describes all **5 Channel Comparison Tools** available in the YouTube MCP server.

### 1. `compare_channels`

Compare multiple YouTube channels side-by-side with detailed metrics.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_ids` | array | Yes | List of 2-5 YouTube channel IDs |

**Returns:**
- For each channel: title, subscribers, total views, video count, average views per video, country
- Channels sorted by subscribers

**Use Cases:**
- Get a quick overview of how channels stack up
- Compare your channel vs. competitors at a glance
- Research potential collaboration partners

**Example:**
```bash
python examples/channel-comparison/individual_examples.py compare
```

---

### 2. `analyze_content_strategy`

Analyze a channel's content strategy including posting frequency and engagement patterns.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | YouTube channel ID |

**Returns:**
- `title`: Channel name
- `subscribers`: Subscriber count
- `total_videos`: Number of videos published
- `avg_views_per_video`: Average view count per video
- `posting_frequency`: Estimated frequency (Daily, Weekly, Monthly)
- `videos_per_month`: Estimated videos published per month

**Use Cases:**
- Understand how often competitors post
- Learn from successful creators' posting patterns
- Plan your own content calendar based on industry benchmarks

**Example:**
```bash
python examples/channel-comparison/individual_examples.py strategy
```

---

### 3. `benchmark_performance`

Benchmark a target channel's performance against competitors.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_channel_id` | string | Yes | Your channel ID to benchmark |
| `competitor_channel_ids` | array | Yes | List of competitor channel IDs |

**Returns:**
- `target_channel`: Your channel's metrics
- `competitors`: Array of competitor metrics
- `rankings`:
  - `subscriber_rank`: Where you rank by subscribers
  - `engagement_rank`: Where you rank by engagement score
- `engagement_scores`: Calculated engagement scores for all channels

**Use Cases:**
- See where you stand among competitors
- Identify areas for improvement
- Track your competitive position over time

**Example:**
```bash
python examples/channel-comparison/individual_examples.py benchmark
```

---

### 4. `identify_competitive_advantages`

Identify what makes a channel unique compared to others — both advantages and weaknesses.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_id` | string | Yes | Channel to analyze |
| `comparison_channel_ids` | array | Yes | Channels to compare against |

**Returns:**
- `channel`: Channel being analyzed
- `advantages`: Array of strengths (e.g., "Highest total views", "Best avg views per video")
- `weaknesses`: Array of areas to improve
- `metrics`: Key performance metrics

**Use Cases:**
- Discover your unique selling points
- Identify gaps in your content strategy
- Find opportunities to differentiate

**Example:**
```bash
python examples/channel-comparison/individual_examples.py advantages
```

---

### 5. `track_market_share`

Track market share and audience distribution across multiple channels in a niche.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel_ids` | array | Yes | List of YouTube channel IDs |

**Returns:**
- `total_subscribers`: Combined subscribers across all channels
- `total_views`: Combined views across all channels
- `market_share`: For each channel:
  - `subscriber_share`: Percentage of total subscribers
  - `view_share`: Percentage of total views

**Use Cases:**
- Understand audience distribution in your niche
- Track how market share changes over time
- Identify the dominant players in a category

**Example:**
```bash
python examples/channel-comparison/individual_examples.py market
```

---

## How to Get a Channel ID

The **Channel ID** is a unique identifier for a YouTube channel (usually starts with `UC`).

### Method 1: From Your Own Channel

1. Go to [YouTube Account Advanced](https://www.youtube.com/account_advanced).
2. Sign in with your YouTube account.
3. Your **Channel ID** is displayed on this page.

### Method 2: From Channel URL (Direct ID)

Some channels show their ID directly in the URL:

1. Go to the channel page.
2. Look at the URL in the address bar.

**Example:**
```
URL: https://www.youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA
Channel ID: UCX6OQ3DkcsbYNE6H8uQQuVA
```

### Method 3: From Custom URL (@username)

Many channels use custom URLs like `@MrBeast`. To get their Channel ID:

**Option A: View Page Source**
1. Go to the channel page (e.g., `youtube.com/@MrBeast`).
2. Right-click → **View Page Source** (or press `Ctrl+U`).
3. Press `Ctrl+F` and search for `"channelId"`.
4. Copy the ID value (starts with `UC`).

**Option B: Use the About Page**
1. Go to the channel's **About** tab.
2. Click the **Share** button.
3. Some browsers/extensions show the Channel ID here.

**Option C: Browser Extension**
Use a browser extension like "YouTube Channel ID Finder" for one-click extraction.

### Method 4: From Any Video

1. Open any video from the channel.
2. Click on the channel name below the video title.
3. Use Method 2 to copy the Channel ID from the URL.

---

## Finding Competitor Channel IDs

To compare your channel with competitors, you need their Channel IDs.

### Step-by-Step:

1. **Identify Competitors**
   - Think of channels in your niche or industry.
   - Search YouTube for your topic and note popular channels.

2. **Navigate to Their Channel**
   - Click on any video from the competitor.
   - Click the channel name to go to their channel page.

3. **Extract the Channel ID**
   - Use any method above (URL, page source, or extension).

4. **Save Your List**
   Create a list of competitor Channel IDs for repeated use:
   ```
   # My Competitors
   UCX6OQ3DkcsbYNE6H8uQQuVA  # MrBeast
   UC-lHJZR3Gqxm24_Vd_AJ5Yw  # PewDiePie
   UCq-Fj5jknLsUf-MWSy4_brA  # T-Series
   ```

---

## Available Scripts

### 1. `quick_test.py`
Minimal test to verify your setup.
```bash
python examples/channel-comparison/quick_test.py
```

### 2. `individual_examples.py`
Test individual tools with command-line arguments.
```bash
# Run all comparison tests
python examples/channel-comparison/individual_examples.py

# Run specific test
python examples/channel-comparison/individual_examples.py compare
python examples/channel-comparison/individual_examples.py strategy
python examples/channel-comparison/individual_examples.py benchmark
python examples/channel-comparison/individual_examples.py advantages
python examples/channel-comparison/individual_examples.py market

# Pass competitor channel IDs as arguments
python examples/channel-comparison/individual_examples.py compare UCX6OQ3DkcsbYNE6H8uQQuVA UC-lHJZR3Gqxm24_Vd_AJ5Yw
```

**Note:** The script will:
- Use your `DEFAULT_CHANNEL_ID` from `.env` as your channel.
- Prompt you to enter competitor channel IDs if not provided.

### 3. `demo_scenarios.py`
Complete demonstration of all comparison tools.
```bash
python examples/channel-comparison/demo_scenarios.py
```

---

## Example Output

### Compare Channels
```
Comparing 2 channels:

1. MrBeast
   Subscribers: 200M
   Total Views: 35.5B
   Videos: 741
   Avg Views/Video: 47.9M
   Country: US

2. PewDiePie
   Subscribers: 111M
   Total Views: 29.1B
   Videos: 4,716
   Avg Views/Video: 6.2M
   Country: GB
```

### Market Share
```
Market Overview:
   Total Subscribers: 311M
   Total Views: 64.6B

Market Share Distribution:

   MrBeast
      Subscriber Share: 64.31%
      View Share: 54.95%

   PewDiePie
      Subscriber Share: 35.69%
      View Share: 45.05%
```

---

## Practical Use Cases

### For Content Creators
- Compare your channel with successful creators in your niche
- Identify what posting frequency works best
- Find gaps in the market you can fill

### For Marketing Teams
- Benchmark influencer partnerships
- Track competitor performance
- Identify the best channels for collaborations

### For Researchers
- Study content strategies across industries
- Analyze market concentration
- Track trends in creator ecosystems

### For Investors
- Evaluate creator potential before partnerships
- Compare ROI across different channels
- Identify emerging creators

---

## API Quota Information

Channel comparison tools use the YouTube Data API:

| Tool | Approximate Cost |
|------|------------------|
| `compare_channels` | 1 unit per channel |
| `analyze_content_strategy` | 2 units (channel + videos) |
| `benchmark_performance` | 1 unit per channel |
| `identify_competitive_advantages` | 1 unit per channel |
| `track_market_share` | 1 unit per channel |

**Daily Quota:** 10,000 units (free tier)

**Tips to Conserve Quota:**
- Compare fewer channels at once
- Cache results for repeated analysis
- Use tools strategically rather than repeatedly

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "YOUTUBE_API_KEY not configured" | Create a `.env` file with your API key |
| "Channel not found" | Verify Channel ID is correct (starts with `UC`) |
| "quotaExceeded" | Wait 24 hours or request quota increase |
| "At least 2 channels required" | Provide at least 2 channel IDs for comparison |
| "DEFAULT_CHANNEL_ID not set" | Add your channel ID to the `.env` file |

---

## Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Channel Resource](https://developers.google.com/youtube/v3/docs/channels)
- [MCP Documentation](https://modelcontextprotocol.io)

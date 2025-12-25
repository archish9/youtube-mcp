# Channel Comparison Tools

This directory demonstrates the **Channel Comparison Tools** integrated into the YouTube MCP server. These tools allow you to compare channels, analyze strategies, benchmark performance, identify competitive advantages, and track market share.

## Prerequisites

1. **Install the project**:
   ```bash
   cd path/to/youtube-mcp
   pip install -e .
   ```

2. **Configure API Key**:
   Ensure you have a `.env` file in the project root with your YouTube Data API key:
   ```bash
   YOUTUBE_API_KEY=your_api_key_here
   ```

## Available Scripts

### 1. quick_test.py
A minimal test to verify your setup is working correctly.

```bash
python quick_test.py
```

### 2. individual_examples.py
Test individual tools with command-line arguments.

```bash
# Run all tests
python examples/channel-comparison/individual_examples.py

# Run specific test
python examples/channel-comparison/individual_examples.py compare
python examples/channel-comparison/individual_examples.py strategy
python examples/channel-comparison/individual_examples.py benchmark
python examples/channel-comparison/individual_examples.py advantages
python examples/channel-comparison/individual_examples.py market
```

### 3. demo_scenarios.py
Complete demonstration of all tools with practical examples.

```bash
# Run all demos
python examples/channel-comparison/demo_scenarios.py
```

## Available Tools

### 1. `compare_channels`
Compare multiple YouTube channels side-by-side with detailed metrics.

**Parameters:**
- `channel_ids` (required): Array of 2-5 YouTube channel IDs

**Returns:**
- Channel titles, subscribers, views, video counts, avg views per video, country

**Use Case:** Get a quick overview of how multiple channels stack up against each other.

### 2. `analyze_content_strategy`
Analyze a channel's content strategy including posting frequency and engagement patterns.

**Parameters:**
- `channel_id` (required): YouTube channel ID

**Returns:**
- Posting frequency, videos per month, total videos, subscriber count, avg views per video

**Use Case:** Understand how often a competitor posts and their content approach.

### 3. `benchmark_performance`
Benchmark a target channel's performance against competitors.

**Parameters:**
- `target_channel_id` (required): Your channel ID
- `competitor_channel_ids` (required): Array of competitor channel IDs

**Returns:**
- Rankings by subscribers and engagement, engagement scores, comparative metrics

**Use Case:** See where you rank among your competitors.

### 4. `identify_competitive_advantages`
Identify competitive advantages and weaknesses compared to other channels.

**Parameters:**
- `channel_id` (required): Channel to analyze
- `comparison_channel_ids` (required): Array of channels to compare against

**Returns:**
- List of advantages, list of weaknesses, key metrics

**Use Case:** Discover what makes your channel unique or where you need to improve.

### 5. `track_market_share`
Track market share and audience distribution across multiple channels.

**Parameters:**
- `channel_ids` (required): Array of YouTube channel IDs

**Returns:**
- Total subscribers/views, subscriber share %, view share % for each channel

**Use Case:** Understand the audience distribution in your niche or industry.

## How to Get Channel IDs

### Method 1: From Channel URL
1. Go to any YouTube channel
2. Look at the URL in the address bar
3. The channel ID is in the URL

**Examples:**
- `https://youtube.com/channel/UCX6OQ3DkcsbYNE6H8uQQuVA` → ID: `UCX6OQ3DkcsbYNE6H8uQQuVA`
- `https://youtube.com/@MrBeast` → Use the search method below

### Method 2: Using YouTube Search
If the channel uses a custom URL (like `@username`):
1. Go to the channel page
2. Click "About" tab
3. Click "Share" → "Copy channel ID"

### Method 3: From Video URL
1. Open any video from the channel
2. Click on the channel name
3. Use Method 1 to get the ID from the channel page URL

## API Quota Information

Channel comparison tools use the YouTube Data API:

**Cost per operation (approximate):**
- `compare_channels`: 1 unit per channel
- `analyze_content_strategy`: 2 units (channel info + video list)
- `benchmark_performance`: 1 unit per channel
- `identify_competitive_advantages`: 1 unit per channel
- `track_market_share`: 1 unit per channel

**Daily quota**: 10,000 units (free tier)

**Tips to conserve quota:**
- Compare fewer channels at once
- Cache results for repeated analysis
- Use the tools strategically rather than repeatedly

## Practical Use Cases

### For Content Creators
- Compare your channel with successful creators in your niche
- Identify what posting frequency works best
- Find gaps in the market you can fill

### For Marketing Teams
- Benchmark influencer partnerships
- Track competitor performance over time
- Identify the best channels for collaborations

### For Researchers
- Study content strategies across industries
- Analyze market concentration
- Track trends in creator ecosystems

### For Investors
- Evaluate creator potential before partnerships
- Compare ROI across different channels
- Identify emerging creators

## Troubleshooting

### Error: "YOUTUBE_API_KEY not configured"
**Solution:** Create a `.env` file in the project root with your API key.

### Error: "Channel not found"
**Solution:** Verify the channel ID is correct. Some channels may be private or deleted.

### Error: "quotaExceeded"
**Solution:** You've hit the daily API quota. Wait 24 hours or request a quota increase from Google Cloud Console.

### Error: "At least 2 channels required"
**Solution:** Provide at least 2 channel IDs for comparison tools.

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

### Content Strategy
```
Channel: MrBeast

Content Strategy Analysis:
   Total Videos: 741
   Posting Frequency: Weekly
   Est. Videos/Month: 5.2
   Subscribers: 200M
   Avg Views/Video: 47.9M
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

## Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Channel Resource](https://developers.google.com/youtube/v3/docs/channels)
- [Search Resource](https://developers.google.com/youtube/v3/docs/search)
- [MCP Documentation](https://modelcontextprotocol.io)

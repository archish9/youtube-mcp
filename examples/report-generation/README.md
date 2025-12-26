# Report Generation Tools

This folder demonstrates the **Report Generation Tools** integrated into the YouTube MCP server. These tools generate comprehensive performance reports for channels and videos.

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

This section describes all **2 Report Generation Tools** available in the YouTube MCP server.

### 1. `generate_channel_report`

Generate a comprehensive performance report for a YouTube channel.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `channel_id` | string | Yes | - | YouTube channel ID |
| `period_days` | number | No | 7 | Report period (7, 30, or 90 days) |
| `include_videos` | boolean | No | true | Include individual video details |

**Returns:**
```json
{
  "report_type": "channel_performance",
  "generated_at": "2024-12-26T12:00:00",
  "period_days": 7,
  "channel": {
    "title": "Channel Name",
    "subscribers_formatted": "10M",
    "total_views_formatted": "1.5B"
  },
  "period_summary": {
    "videos_published": 5,
    "total_views_formatted": "50M",
    "avg_views_formatted": "10M",
    "avg_like_rate": 4.5
  },
  "top_performers": {
    "by_views": [...],
    "by_engagement": [...]
  },
  "videos": [...]
}
```

**Use Cases:**
- Weekly/monthly channel performance summaries
- Competitive analysis reports
- Client reporting for marketing agencies
- Content strategy evaluation

---

### 2. `generate_video_report`

Generate a detailed performance report for a specific video.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `video_id` | string | Yes | YouTube video ID or URL |

**Returns:**
```json
{
  "report_type": "video_performance",
  "generated_at": "2024-12-26T12:00:00",
  "video": {
    "title": "Video Title",
    "channel": "Channel Name",
    "duration": "10:30"
  },
  "metrics": {
    "views_formatted": "1.5M",
    "likes_formatted": "100K",
    "like_rate": 6.67,
    "engagement_score": 5.2
  },
  "performance": {
    "score": 52.0,
    "grade": "C",
    "like_rating": "Good",
    "comment_rating": "Moderate Engagement"
  },
  "analysis": {
    "quality_signals": ["Strong video reach"],
    "areas_for_improvement": ["Low comment engagement"],
    "overall_assessment": "Average"
  }
}
```

**Use Cases:**
- Individual video performance analysis
- Post-campaign video evaluation
- Content quality assessment
- A/B testing video performance

---

## How to Get IDs

### Get a Channel ID

1. Go to any YouTube channel page
2. Click on the channel name to go to their main page
3. Look at the URL:
   - Format: `youtube.com/channel/UCxxxxxx` → The ID is `UCxxxxxx`
   - If URL shows `@username`, click "About" → "Share" → Copy channel URL

**Example Channel IDs:**
| Channel | ID |
|---------|-------|
| MrBeast | `UCX6OQ3DkcsbYNE6H8uQQuVA` |
| PewDiePie | `UC-lHJZR3Gqxm24_Vd_AJ5Yw` |
| T-Series | `UCq-Fj5jknLsUf-MWSy4_brA` |

### Get a Video ID

1. Go to any YouTube video
2. Look at the URL: `youtube.com/watch?v=dQw4w9WgXcQ`
3. The Video ID is the value after `v=` (e.g., `dQw4w9WgXcQ`)

---

## Available Scripts

### `test_reports.py`

Command-line interface to test each report generation tool.

**Usage:**
```bash
python examples/report-generation/test_reports.py <command> [args]
```

**Commands:**

| Command | Description |
|---------|-------------|
| `channel` | Generate channel performance report |
| `video` | Generate video performance report |
| `all` | Run all tests |

**Examples:**

```bash
# Generate channel report (default: MrBeast, 7 days)
python examples/report-generation/test_reports.py channel

# Generate channel report with custom channel and period
python examples/report-generation/test_reports.py channel UCX6OQ3DkcsbYNE6H8uQQuVA 30

# Generate video report
python examples/report-generation/test_reports.py video dQw4w9WgXcQ

# Run all tests
python examples/report-generation/test_reports.py all
```

---

## Report Output Formats

Reports are returned as JSON and can be:

1. **Viewed directly** — Print formatted output in terminal
2. **Saved to file** — Redirect output or save programmatically
3. **Processed further** — Parse JSON for dashboards, emails, etc.

**Example: Save report to file**
```python
import json

result = await session.call_tool(
    "generate_channel_report",
    arguments={"channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA", "period_days": 30}
)

report = json.loads(result.content[0].text)

# Save to JSON file
with open("channel_report.json", "w") as f:
    json.dump(report, f, indent=2)   

# Save to Markdown
with open("channel_report.md", "w") as f:
    f.write(f"# {report['channel']['title']} Report\n\n")
    f.write(f"**Period:** {report['period_days']} days\n\n")
    f.write(f"## Summary\n")
    f.write(f"- Videos: {report['period_summary']['videos_published']}\n")
    f.write(f"- Views: {report['period_summary']['total_views_formatted']}\n")
```

---

## Practical Use Cases

### For Content Creators
- Track your channel's weekly performance
- Identify your best-performing videos
- Understand engagement patterns

### For Marketing Teams
- Generate campaign performance reports
- Compare video performance across campaigns
- Export data for stakeholder presentations

### For Agencies
- Automate client reporting
- Generate comparative channel analyses
- Track influencer performance

---

## API Quota Information

| Tool | Quota Cost |
|------|------------|
| `generate_channel_report` | ~3-5 units (depends on video count) |
| `generate_video_report` | 1 unit |

**Daily Quota:** 10,000 units (free tier)

---

## Limitations

> **Note:** All data is real and fetched live from YouTube. Reports contain current-only data. For historical tracking over time, you would need to store reports periodically.

**What reports can include:**
- Current channel/video metrics
- Recent video performance (within period)
- Engagement analysis and ratings

**What reports cannot include:**
- Historical trends (requires stored data)
- Watch time, demographics (requires OAuth)
- Revenue data (requires OAuth + monetization)

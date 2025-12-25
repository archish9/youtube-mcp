# Video Analytics Example

This directory demonstrates the **Video Analytics** tools integrated into the MCP server. These tools allow you to track metrics, monitor growth, identify viral moments, and predict future performance.

## Prerequisites

1.  **Install the project**:
    ```bash
    pip install -e .
    ```
2.  **Configure API Key**:
    Ensure you have a `.env` file in the project root with your YouTube Data API key:
    ```bash
    YOUTUBE_API_KEY=your_api_key_here
    ```

## Available Scripts

### `test_analytics.py`

This script provides a command-line interface to test each analytics tool individually or all at once.

**Usage:**
```bash
python examples/video-analytics/test_analytics.py <command> [video_id]
```

**Commands:**

| Command | Description |
| :--- | :--- |
| `metrics` | Track historical metrics (views/likes/comments) |
| `growth` | Calculate daily growth rates and total growth |
| `viral` | Identify viral moments (spikes in view rate) |
| `compare` | Compare current performance vs. 14 days ago |
| `predict` | Predict future views for the next 7 days |
| `all` | **(Default)** Run all tests sequentially |

**Examples:**

```bash
# Run all tests
python examples/video-analytics/test_analytics.py all

# Run specific analytics tools
python examples/video-analytics/test_analytics.py metrics
python examples/video-analytics/test_analytics.py growth
python examples/video-analytics/test_analytics.py viral
python examples/video-analytics/test_analytics.py compare
python examples/video-analytics/test_analytics.py predict

# Run with a specific Video ID (e.g., dQw4w9WgXcQ)
python examples/video-analytics/test_analytics.py all dQw4w9WgXcQ
python examples/video-analytics/test_analytics.py metrics dQw4w9WgXcQ
```

## How to get a Video ID

The **Video ID** is a unique string of characters that identifies a specific YouTube video.

### Method 1: From the URL

1.  Open any YouTube video in your browser.
2.  Look at the address bar URL.
3.  The ID is the text after `v=`.

**Example:**
URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
Video ID: `dQw4w9WgXcQ`

### Method 2: From the "Share" Button

1.  Click the **Share** button below the video player.
2.  Look at the URL provided (e.g., `https://youtu.be/dQw4w9WgXcQ`).
3.  The ID is the last part of the link.

**Example:**
Link: `https://youtu.be/dQw4w9WgXcQ`
Video ID: `dQw4w9WgXcQ`

## How It Works

1.  **Client**: The script connects to the MCP server using standard I/O.
2.  **Request**: It sends a tool call (e.g., `track_video_metrics`) with the provided `video_id`.
3.  **Server**: 
    - Fetches the latest live data from the YouTube API.
    - Uses internal logic to simulate historical data points (for demonstration).
    - Returns calculated analytics in JSON format.
4.  **Output**: The script formats the JSON response into a readable console report.

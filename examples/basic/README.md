# YouTube MCP Basic Examples

This folder contains testing scripts for the YouTube MCP server.

## Prerequisites

1. Make sure you have installed the project:
   ```bash
   cd path/to/youtube-mcp
   pip install -e .
   ```

2. Configure your API key in `.env`:
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
python examples/basic/individual_examples.py

# Run specific test
python examples/basic/individual_examples.py search
python examples/basic/individual_examples.py video
python examples/basic/individual_examples.py transcript
python examples/basic/individual_examples.py comments
python examples/basic/individual_examples.py channel
python examples/basic/individual_examples.py videos
python examples/basic/individual_examples.py trending
python examples/basic/individual_examples.py playlist
```

### 3. demo_client.py
Complete demonstration of all tools with practical examples.

```bash
# Run all demos
python examples/basic/demo_client.py

# Run specific demo
python examples/basic/demo_client.py video
python examples/basic/demo_client.py transcript
python examples/basic/demo_client.py search
```

### 4. interactive_demo.py
Interactive command-line interface to test tools.

```bash
python examples/basic/interactive_demo.py
```

Then use commands like:
```
> video dQw4w9WgXcQ
> search python tutorial
> trending US
> exit
```

## Troubleshooting

### "YOUTUBE_API_KEY not configured"
Create a `.env` file in the project root with your API key.

### "quotaExceeded"
You've hit the daily YouTube API quota. Wait 24 hours or get a new API key.

### "Connection closed"
The MCP server may have crashed. Check the error message for details.

# Integrating YouTube MCP with Agentic Frameworks

This guide explains how to integrate the YouTube MCP server with popular agentic AI frameworks like **LangChain** and **LlamaIndex** to build intelligent YouTube-powered applications.

---

## Table of Contents

1. [Why Integrate with Frameworks?](#why-integrate-with-frameworks)
2. [Integration Approaches](#integration-approaches)
3. [LangChain Integration](#langchain-integration)
4. [LlamaIndex Integration](#llamaindex-integration)
5. [RAG with YouTube Content](#rag-with-youtube-content)
6. [Advanced Applications](#advanced-applications)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Why Integrate with Frameworks?

By itself, YouTube MCP **fetches data**. When combined with agentic frameworks, it gains **intelligence**:

| YouTube MCP Alone | + LangChain/LlamaIndex |
|------------------|------------------------|
| Fetches video info | Understands context across videos |
| Gets transcripts | Extracts key insights using NLP |
| Retrieves comments | Analyzes sentiment and patterns |
| Searches videos | Synthesizes information from multiple sources |
| Returns raw data | Creates intelligent recommendations |

### What Becomes Possible

- **Intelligent Research Assistant** — Search videos, extract insights, create study guides
- **Content Creation Agent** — Analyze successful videos, generate ideas, create outlines
- **Automated Course Creator** — Build learning curricula from YouTube tutorials
- **Competitive Analysis Bot** — Track and compare channel performance over time
- **Multi-Video Q&A System** — Answer questions using knowledge from multiple videos

---

## Integration Approaches

There are **three main approaches** to integrate YouTube MCP with frameworks:

### Approach 1: MCP Tools as LangChain/LlamaIndex Tools

Convert YouTube MCP tools into framework-compatible tools that agents can call.

**How it works:**
1. Create wrapper functions for each MCP tool
2. Define tool descriptions for the LLM
3. Initialize agent with tools
4. Agent decides when to call YouTube tools

**Best for:** Agent-based applications where the LLM decides which tools to use.

---

### Approach 2: RAG (Retrieval-Augmented Generation)

Index YouTube video transcripts in a vector database for semantic search.

**How it works:**
1. Fetch transcripts via MCP
2. Chunk and embed text
3. Store in vector database (Chroma, Pinecone, Weaviate)
4. Query semantically and augment LLM responses

**Best for:** Q&A systems, research assistants, knowledge bases.

---

### Approach 3: LangGraph/Workflow Agents

Build multi-step workflows that orchestrate YouTube data retrieval and processing.

**How it works:**
1. Define workflow nodes (search, analyze, synthesize)
2. Use MCP tools within each node
3. Chain operations with state management
4. Handle complex multi-step tasks

**Best for:** Complex workflows like content strategy, course creation, research.

---

## LangChain Integration

### Step 1: Install Dependencies

```bash
pip install langchain langchain-anthropic langchain-openai chromadb mcp python-dotenv
```

### Step 2: Create the MCP Wrapper Module

Create a file `youtube_mcp_wrapper.py` that wraps MCP tools for LangChain:

```python
"""
youtube_mcp_wrapper.py
Complete wrapper for YouTube MCP tools to use with LangChain/LlamaIndex
"""

import asyncio
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure MCP server connection
PROJECT_ROOT = Path(__file__).parent.parent  # Adjust path as needed
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"  # Windows
if not VENV_PYTHON.exists():
    VENV_PYTHON = PROJECT_ROOT / "venv" / "bin" / "python"  # Linux/Mac

SERVER_PARAMS = StdioServerParameters(
    command=str(VENV_PYTHON) if VENV_PYTHON.exists() else "python",
    args=["-m", "youtube_mcp.server"],
    cwd=str(PROJECT_ROOT),
    env={
        **os.environ,
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY", ""),
        "PYTHONPATH": str(PROJECT_ROOT / "src")
    }
)


class YouTubeMCPClient:
    """Synchronous wrapper for YouTube MCP tools"""
    
    @staticmethod
    def _run_async(coro):
        """Run async function synchronously"""
        return asyncio.get_event_loop().run_until_complete(coro)
    
    @staticmethod
    async def _call_tool(tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the result"""
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                return result.content[0].text
    
    # ===========================================
    # TOOL WRAPPER FUNCTIONS (for LangChain)
    # ===========================================
    
    @staticmethod
    def search_videos(query: str, max_results: int = 5) -> str:
        """
        Search YouTube videos by keyword.
        
        Args:
            query: Search query string
            max_results: Number of results (default 5)
        
        Returns:
            JSON string with video results
        """
        async def _search():
            return await YouTubeMCPClient._call_tool(
                "search_videos",
                {"query": query, "max_results": max_results}
            )
        return YouTubeMCPClient._run_async(_search())
    
    @staticmethod
    def get_video_info(video_id: str) -> str:
        """
        Get detailed information about a YouTube video.
        
        Args:
            video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
        
        Returns:
            JSON string with video details
        """
        async def _get_info():
            return await YouTubeMCPClient._call_tool(
                "get_video_info",
                {"video_id": video_id}
            )
        return YouTubeMCPClient._run_async(_get_info())
    
    @staticmethod
    def get_video_transcript(video_id: str, language: str = "en") -> str:
        """
        Get transcript/captions of a YouTube video.
        
        Args:
            video_id: YouTube video ID
            language: Language code (default 'en')
        
        Returns:
            JSON string with transcript entries
        """
        async def _get_transcript():
            return await YouTubeMCPClient._call_tool(
                "get_video_transcript",
                {"video_id": video_id, "language": language}
            )
        return YouTubeMCPClient._run_async(_get_transcript())
    
    @staticmethod
    def get_channel_info(channel_id: str) -> str:
        """
        Get information about a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID (e.g., 'UCX6OQ3DkcsbYNE6H8uQQuVA')
        
        Returns:
            JSON string with channel details
        """
        async def _get_channel():
            return await YouTubeMCPClient._call_tool(
                "get_channel_info",
                {"channel_id": channel_id}
            )
        return YouTubeMCPClient._run_async(_get_channel())
    
    @staticmethod
    def get_video_analytics(video_id: str) -> str:
        """
        Get engagement analytics for a video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            JSON string with engagement metrics
        """
        async def _get_analytics():
            return await YouTubeMCPClient._call_tool(
                "get_video_analytics",
                {"video_id": video_id}
            )
        return YouTubeMCPClient._run_async(_get_analytics())
    
    @staticmethod
    def generate_video_report(video_id: str) -> str:
        """
        Generate a comprehensive report for a video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            JSON string with performance report
        """
        async def _generate_report():
            return await YouTubeMCPClient._call_tool(
                "generate_video_report",
                {"video_id": video_id}
            )
        return YouTubeMCPClient._run_async(_generate_report())
    
    @staticmethod
    def generate_channel_report(channel_id: str, period_days: int = 7) -> str:
        """
        Generate a comprehensive report for a channel.
        
        Args:
            channel_id: YouTube channel ID
            period_days: Report period in days (7, 30, or 90)
        
        Returns:
            JSON string with channel performance report
        """
        async def _generate_report():
            return await YouTubeMCPClient._call_tool(
                "generate_channel_report",
                {"channel_id": channel_id, "period_days": period_days}
            )
        return YouTubeMCPClient._run_async(_generate_report())
```

### Step 3: Create LangChain Tools

```python
"""
langchain_youtube_tools.py
Create LangChain tools from YouTube MCP wrapper
"""

from langchain.agents import Tool
from youtube_mcp_wrapper import YouTubeMCPClient

def create_youtube_tools():
    """Create LangChain tools from YouTube MCP"""
    
    return [
        Tool(
            name="search_youtube_videos",
            func=lambda q: YouTubeMCPClient.search_videos(q, max_results=5),
            description="""
            Search YouTube videos by keyword.
            Input: A search query string (e.g., "python tutorial for beginners")
            Output: JSON with video titles, channels, URLs, and view counts
            Use this to find relevant videos on any topic.
            """
        ),
        Tool(
            name="get_video_details",
            func=YouTubeMCPClient.get_video_info,
            description="""
            Get detailed information about a specific YouTube video.
            Input: A YouTube video ID (e.g., "dQw4w9WgXcQ")
            Output: JSON with title, description, views, likes, duration, channel info
            Use this after searching to get more details about a specific video.
            """
        ),
        Tool(
            name="get_video_transcript",
            func=YouTubeMCPClient.get_video_transcript,
            description="""
            Get the full transcript/captions of a YouTube video.
            Input: A YouTube video ID
            Output: JSON with timestamped transcript entries and full text
            Use this to analyze video content, extract key points, or answer questions about the video.
            """
        ),
        Tool(
            name="get_channel_info",
            func=YouTubeMCPClient.get_channel_info,
            description="""
            Get information about a YouTube channel.
            Input: A YouTube channel ID (e.g., "UCX6OQ3DkcsbYNE6H8uQQuVA")
            Output: JSON with channel name, subscribers, total views, video count
            Use this to analyze channel performance or find channel details.
            """
        ),
        Tool(
            name="analyze_video_engagement",
            func=YouTubeMCPClient.get_video_analytics,
            description="""
            Get engagement analytics for a YouTube video.
            Input: A YouTube video ID
            Output: JSON with like rate, comment rate, engagement score
            Use this to evaluate how well a video is performing with its audience.
            """
        ),
        Tool(
            name="generate_video_report",
            func=YouTubeMCPClient.generate_video_report,
            description="""
            Generate a comprehensive performance report for a video.
            Input: A YouTube video ID
            Output: JSON with metrics, performance grade (A-F), quality signals, and recommendations
            Use this for detailed video analysis and performance evaluation.
            """
        )
    ]
```

### Step 4: Create and Use the Agent

```python
"""
youtube_research_agent.py
Complete example of using YouTube MCP with LangChain
"""

from langchain.agents import initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic
# Or use OpenAI:
# from langchain_openai import ChatOpenAI

from langchain_youtube_tools import create_youtube_tools

# Initialize LLM
llm = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0
)
# Or use OpenAI:
# llm = ChatOpenAI(model="gpt-4", temperature=0)

# Create tools
tools = create_youtube_tools()

# Initialize agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

# Example queries to try:

# 1. Research a topic
result = agent.run(
    "Find the top 3 videos about Python async programming. "
    "For each video, get its view count and engagement score. "
    "Summarize which video has the best engagement."
)
print(result)

# 2. Analyze a specific video
result = agent.run(
    "Analyze the video with ID 'dQw4w9WgXcQ'. "
    "Get its transcript and summarize the main content. "
    "Also get its engagement metrics."
)
print(result)

# 3. Compare channels
result = agent.run(
    "Compare the channels MrBeast (UCX6OQ3DkcsbYNE6H8uQQuVA) and "
    "PewDiePie (UC-lHJZR3Gqxm24_Vd_AJ5Yw). "
    "Which has more subscribers and total views?"
)
print(result)
```

### Key LangChain Concepts

| Concept | Usage with YouTube MCP |
|---------|----------------------|
| **Tools** | Each MCP tool becomes a LangChain Tool |
| **Agents** | Orchestrate multiple tool calls based on user query |
| **Memory** | Store conversation context about videos discussed |
| **Chains** | Create pipelines (search → get info → analyze) |
| **Callbacks** | Monitor tool calls and LLM responses |

---

## LlamaIndex Integration

### Step 1: Install Dependencies

```bash
pip install llama-index llama-index-llms-anthropic llama-index-llms-openai chromadb mcp python-dotenv
```

### Step 2: Create LlamaIndex Tools

Using the same `YouTubeMCPClient` wrapper from above:

```python
"""
llamaindex_youtube_tools.py
Create LlamaIndex tools from YouTube MCP wrapper
"""

from llama_index.core.tools import FunctionTool
from youtube_mcp_wrapper import YouTubeMCPClient

def create_llamaindex_tools():
    """Create LlamaIndex FunctionTools from YouTube MCP"""
    
    return [
        FunctionTool.from_defaults(
            fn=YouTubeMCPClient.search_videos,
            name="search_youtube",
            description="Search YouTube for videos. Args: query (str), max_results (int, default 5)"
        ),
        FunctionTool.from_defaults(
            fn=YouTubeMCPClient.get_video_info,
            name="get_video_info",
            description="Get detailed info about a video. Args: video_id (str)"
        ),
        FunctionTool.from_defaults(
            fn=YouTubeMCPClient.get_video_transcript,
            name="get_transcript",
            description="Get video transcript. Args: video_id (str), language (str, default 'en')"
        ),
        FunctionTool.from_defaults(
            fn=YouTubeMCPClient.get_channel_info,
            name="get_channel_info",
            description="Get channel information. Args: channel_id (str)"
        ),
        FunctionTool.from_defaults(
            fn=YouTubeMCPClient.get_video_analytics,
            name="analyze_video",
            description="Get engagement analytics. Args: video_id (str)"
        ),
        FunctionTool.from_defaults(
            fn=YouTubeMCPClient.generate_video_report,
            name="generate_report",
            description="Generate comprehensive video report. Args: video_id (str)"
        )
    ]
```

### Step 3: Create and Use ReAct Agent

```python
"""
llamaindex_youtube_agent.py
Complete LlamaIndex agent example
"""

from llama_index.core.agent import ReActAgent
from llama_index.llms.anthropic import Anthropic
# Or use OpenAI:
# from llama_index.llms.openai import OpenAI

from llamaindex_youtube_tools import create_llamaindex_tools

# Initialize LLM
llm = Anthropic(model="claude-3-sonnet-20240229")
# Or:
# llm = OpenAI(model="gpt-4")

# Create tools
tools = create_llamaindex_tools()

# Create ReAct agent
agent = ReActAgent.from_tools(
    tools=tools,
    llm=llm,
    verbose=True
)

# Example queries

# 1. Research videos on a topic
response = agent.chat(
    "Search for the top 3 Python tutorial videos. "
    "For the best one, get its transcript and summarize the key topics covered."
)
print(response)

# 2. Analyze video performance
response = agent.chat(
    "Generate a performance report for video ID 'dQw4w9WgXcQ'. "
    "What grade did it get and why?"
)
print(response)

# 3. Compare channels
response = agent.chat(
    "Get information about MrBeast's channel (UCX6OQ3DkcsbYNE6H8uQQuVA). "
    "How many subscribers and total views does it have?"
)
print(response)
```

### Step 4: Query the Agent

agent = ReActAgent.from_tools(
    tools=tools,
    llm=llm,
    verbose=True
)
```

### Step 4: Query the Agent

```python
response = agent.chat(
    "Research the best Python tutorial channels and compare their teaching styles"
)
```

---

## RAG with YouTube Content

Build a knowledge base from YouTube video transcripts for semantic Q&A.

### Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  User Question  │────▶│  Vector Search  │────▶│  LLM + Context  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  YouTube MCP    │
                        │  (Transcripts)  │
                        └─────────────────┘
```

### Complete RAG Implementation

```python
"""
youtube_rag_system.py
Complete RAG system for YouTube video transcripts
"""

import json
from youtube_mcp_wrapper import YouTubeMCPClient

# Install: pip install chromadb langchain langchain-openai
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# Or use Anthropic:
# from langchain_anthropic import ChatAnthropic


class YouTubeRAGSystem:
    """RAG system for querying YouTube video content"""
    
    def __init__(self):
        # Initialize vector database
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name="youtube_transcripts",
            metadata={"description": "YouTube video transcripts"}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize LLM
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        
        # Track indexed videos
        self.indexed_videos = []
    
    def index_videos(self, search_query: str, max_videos: int = 5):
        """
        Search YouTube and index video transcripts
        
        Args:
            search_query: Topic to search for
            max_videos: Number of videos to index
        """
        print(f"Searching YouTube for: {search_query}")
        
        # Search for videos
        search_result = YouTubeMCPClient.search_videos(search_query, max_videos)
        videos = json.loads(search_result)['videos']
        
        print(f"Found {len(videos)} videos. Indexing transcripts...")
        
        for video in videos:
            video_id = video['video_id']
            title = video['title']
            
            try:
                # Get transcript
                transcript_result = YouTubeMCPClient.get_video_transcript(video_id)
                transcript_data = json.loads(transcript_result)
                full_text = transcript_data['full_text']
                
                # Chunk the transcript
                chunks = self.text_splitter.split_text(full_text)
                
                # Create embeddings and store
                for i, chunk in enumerate(chunks):
                    embedding = self.embeddings.embed_query(chunk)
                    
                    self.collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{
                            "video_id": video_id,
                            "title": title,
                            "chunk_index": i,
                            "url": f"https://youtube.com/watch?v={video_id}"
                        }],
                        ids=[f"{video_id}_{i}"]
                    )
                
                self.indexed_videos.append({
                    "video_id": video_id,
                    "title": title,
                    "chunks": len(chunks)
                })
                
                print(f"  Indexed: {title} ({len(chunks)} chunks)")
                
            except Exception as e:
                print(f"  Skipped: {title} (no transcript available)")
        
        print(f"\nTotal: {len(self.indexed_videos)} videos indexed")
    
    def query(self, question: str, num_results: int = 5) -> str:
        """
        Query the RAG system with a question
        
        Args:
            question: User's question
            num_results: Number of relevant chunks to retrieve
        
        Returns:
            LLM-generated answer with citations
        """
        # Create embedding for question
        question_embedding = self.embeddings.embed_query(question)
        
        # Search for relevant chunks
        results = self.collection.query(
            query_embeddings=[question_embedding],
            n_results=num_results
        )
        
        # Format context with sources
        context_parts = []
        sources = []
        
        for i, (doc, metadata) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0]
        )):
            context_parts.append(f"[Source {i+1}]: {doc}")
            sources.append({
                "title": metadata['title'],
                "url": metadata['url']
            })
        
        context = "\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Based on the following excerpts from YouTube video transcripts, 
answer the question. Cite your sources using [Source N] notation.

TRANSCRIPTS:
{context}

QUESTION: {question}

ANSWER (with citations):"""
        
        # Get LLM response
        response = self.llm.invoke(prompt)
        
        # Format output
        answer = response.content
        source_list = "\n".join([f"- [{s['title']}]({s['url']})" for s in sources])
        
        return f"{answer}\n\n**Sources:**\n{source_list}"


# Example usage
if __name__ == "__main__":
    # Create RAG system
    rag = YouTubeRAGSystem()
    
    # Index videos on a topic
    rag.index_videos("python async await tutorial", max_videos=5)
    
    # Ask questions
    questions = [
        "What is async/await in Python?",
        "How do you create an async function?",
        "What is the difference between async and threading?"
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        print("-" * 50)
        answer = rag.query(question)
        print(answer)
        print()
```

### Vector Database Options

| Database | Best For | Installation |
|----------|----------|--------------|
| **Chroma** | Local development, small-medium datasets | `pip install chromadb` |
| **Pinecone** | Production, large-scale, managed service | `pip install pinecone-client` |
| **Weaviate** | Multi-modal, production workloads | `pip install weaviate-client` |
| **Qdrant** | Self-hosted, high performance | `pip install qdrant-client` |
| **FAISS** | Local, in-memory, fast prototyping | `pip install faiss-cpu` |

---

## Advanced Applications

### 1. Intelligent Video Research Assistant

**Workflow:**
1. User provides research topic
2. Agent searches for relevant videos
3. Fetches transcripts for top results
4. Indexes content in vector store
5. Extracts key concepts using NLP
6. Compares teaching approaches
7. Generates comprehensive study guide with citations

**Use Cases:**
- Academic research
- Competitive intelligence
- Learning new skills
- Content curation

---

### 2. Content Creation Agent

**Workflow:**
1. Analyze successful videos in your niche
2. Extract title patterns, optimal length, engagement factors
3. Identify trending themes from transcripts
4. Generate video ideas based on patterns
5. Create detailed outlines with timestamps
6. Predict performance based on historical data

**Use Cases:**
- YouTube creators
- Marketing teams
- Content agencies
- Influencer management

---

### 3. Multi-Video Q&A System

**Workflow:**
1. User asks complex question
2. Agent searches relevant videos
3. Retrieves specific transcript segments
4. Synthesizes answer from multiple sources
5. Cites timestamps and video sources
6. Provides follow-up recommendations

**Example Query:**
> "Compare how different experts explain gradient descent. What are the common analogies used?"

**System Response:**
> Based on 5 expert videos:
> - 3Blue1Brown uses ball-rolling-downhill analogy [Video 1, 3:42]
> - Andrew Ng emphasizes iterative updates [Video 2, 5:15]
> - StatQuest uses step-by-step visual [Video 3, 2:30]
> ...

---

### 4. Automated Course Creator

**Workflow:**
1. Search for tutorials on target topic
2. Analyze difficulty levels
3. Order videos from beginner to advanced
4. Create learning path with milestones
5. Generate quizzes from transcript content
6. Build 30-day study calendar

**Output:**
```
Week 1: Fundamentals
  - Day 1: "Python Basics" (Video A) - 15 min
  - Day 2: Quiz on variables, data types
  - Day 3: "Functions Explained" (Video B) - 20 min
  ...

Week 2: Intermediate
  - Day 8: "Object-Oriented Python" (Video C)
  ...
```

---

## Best Practices

### 1. Tool Design

- **Clear descriptions**: LLMs use tool descriptions to decide when to call them
- **Single responsibility**: Each tool should do one thing well
- **Error handling**: Return informative error messages
- **Rate limiting**: Respect YouTube API quotas

### 2. RAG Optimization

- **Chunk size**: 500-1000 tokens works well for transcripts
- **Overlap**: 10-20% overlap between chunks preserves context
- **Metadata**: Store video ID, title, timestamp with each chunk
- **Re-ranking**: Use cross-encoder re-ranking for better relevance

### 3. Agent Prompting

- **System prompt**: Explain available tools and their capabilities
- **Examples**: Provide few-shot examples of good tool usage
- **Guardrails**: Set limits on API calls per query
- **Fallbacks**: Handle cases when no relevant videos found

### 4. Performance

- **Caching**: Cache video info and transcripts
- **Batching**: Combine API calls where possible
- **Async**: Use async operations for concurrent requests
- **Lazy loading**: Don't fetch transcripts until needed

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Agent not using tools** | Improve tool descriptions, add examples to prompt |
| **Slow response times** | Cache results, use async, batch requests |
| **Poor RAG quality** | Tune chunk size, add re-ranking, improve embeddings |
| **API quota exceeded** | Implement caching, reduce max_results |
| **Transcripts unavailable** | Handle gracefully, skip videos without captions |
| **Context window exceeded** | Summarize transcripts, use selective retrieval |

---

## Example Prompts for Agents

### Research Assistant
```
You are a research assistant with access to YouTube video data.
Use the search_youtube tool to find relevant videos.
Use get_transcript to extract content for analysis.
Always cite your sources with video titles and timestamps.
```

### Content Strategist
```
You are a YouTube content strategist.
Analyze successful videos using the analytics tools.
Identify patterns in titles, lengths, and engagement.
Provide data-driven recommendations for new content.
```

### Learning Coach
```
You are an AI learning coach.
Find the best tutorial videos for the user's topic.
Create structured learning paths with clear milestones.
Use transcripts to generate quiz questions.
```

---

## Additional Resources

- [LangChain Documentation](https://python.langchain.com/docs/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [YouTube MCP Main README](../README.md)
- [All Examples Index](../examples/README.md)

---

## Summary

| Integration Method | Complexity | Best For |
|-------------------|------------|----------|
| **Tools as LangChain Tools** | Low | Simple agent applications |
| **RAG with Transcripts** | Medium | Q&A, research, knowledge bases |
| **Multi-step Workflows** | High | Complex tasks (course creation, strategies) |

Start with the **Tools approach** for quick prototyping, then add **RAG** for deeper content understanding, and finally build **workflows** for production applications.

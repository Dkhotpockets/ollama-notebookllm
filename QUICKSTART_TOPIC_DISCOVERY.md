# Quick Start: Topic Discovery

Get started with automatic topic-based content discovery in less than 5 minutes!

## Prerequisites

✅ **Minimal Setup (Discovery Only):**
- Python 3.13+
- `pip install ddgs` (DuckDuckGo search)

✅ **Full Setup (Discovery + Processing):**
- All of the above, plus:
- Vector storage (Supabase OR PostgreSQL with pgvector)
- Neo4j (optional, for knowledge graph)
- LLM provider (OpenAI, Google, or Ollama)

## Installation

1. **Install the dependency:**
   ```bash
   pip install ddgs
   ```

2. **Verify installation:**
   ```bash
   python -c "from ddgs import DDGS; print('✓ Ready!')"
   ```

That's it for basic discovery! For full RAG processing, see the [full setup guide](#full-rag-setup).

## Usage

### Method 1: Streamlit UI (Easiest)

1. **Start the app:**
   ```bash
   streamlit run src/notebookllama/Home.py
   ```

2. **Navigate to Topic Discovery:**
   - Look in the sidebar
   - Click **"6_Topic_Discovery"**

3. **Enter a topic and go:**
   ```
   What topic do you want to learn about?
   > TypeScript ← Enter any technical topic

   [🚀 Discover & Learn] ← Click this button
   ```

4. **Watch the magic happen:**
   ```
   🔍 Searching for resources about TypeScript...
   ✅ Discovered 10 resources

   🌐 Crawling TypeScript Documentation (1/10)
   🌐 Crawling Learn TypeScript Tutorial (2/10)
   ...

   ✅ Successfully processed 8 out of 10 resources
   ```

5. **Start learning:**
   - Go to **"Enhanced RAG Chat"**
   - Ask questions like:
     - "What is TypeScript?"
     - "How do I use interfaces?"
     - "Explain type guards"

### Method 2: Python API (Programmatic)

```python
import asyncio
from notebookllama.ragflow_integration import discover_and_process_topic

async def learn_typescript():
    results = await discover_and_process_topic(
        topic="TypeScript",
        max_resources=10,
        max_concurrent_crawls=3
    )

    print(f"✓ Processed {results['processed']} resources")
    print(f"You can now ask questions about TypeScript!")

asyncio.run(learn_typescript())
```

### Method 3: MCP Server Tools

If you're using the MCP server:

```python
# Via MCP client
result = await mcp_client.call_tool(
    "discover_topic_tool",
    {
        "topic": "Docker",
        "max_resources": 15
    }
)

print(f"Discovered: {result['discovered']}")
print(f"Processed: {result['processed']}")
```

## Examples

### Example 1: Learn a New Programming Language

```python
await discover_and_process_topic("Rust programming", max_resources=20)
# Wait ~60 seconds...
# ✓ Now ask: "How does Rust handle memory management?"
```

### Example 2: Understand a Framework

```python
await discover_and_process_topic("React hooks", max_resources=15)
# Wait ~45 seconds...
# ✓ Now ask: "When should I use useEffect?"
```

### Example 3: Learn DevOps Tools

```python
await discover_and_process_topic("Kubernetes basics", max_resources=10)
# Wait ~30 seconds...
# ✓ Now ask: "What is a Kubernetes pod?"
```

### Example 4: Explore ML Topics

```python
await discover_and_process_topic("neural networks", max_resources=20)
# Wait ~60 seconds...
# ✓ Now ask: "Explain backpropagation"
```

## What Gets Discovered?

The system automatically prioritizes:

### 🏆 Highest Priority: Official Documentation
- `docs.python.org` - Python official docs
- `developer.mozilla.org` - MDN Web Docs
- `typescriptlang.org` - TypeScript docs
- `kubernetes.io` - Kubernetes docs
- `docs.docker.com` - Docker docs

### 🎓 High Priority: Educational Platforms
- W3Schools
- freeCodeCamp
- MDN
- Codecademy
- Real Python

### 📚 Medium Priority: Quality Content
- High-quality blogs (CSS-Tricks, Smashing Magazine)
- GitHub repositories with good READMEs
- Tutorial sites

### ⚠️ Filtered Out:
- Forums (Stack Overflow, Reddit)
- Advertisement sites
- Paywalled content
- Spam/low-quality content

## Configuration

### Adjust Discovery Settings

In the Streamlit UI sidebar:

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Max resources | 10 | 5-30 | How many to discover |
| Concurrent crawls | 3 | 1-5 | Parallel processing |
| Extract entities | ✓ | On/Off | Knowledge graph |

### Recommended Settings

**Quick exploration (5 min):**
```
Max resources: 5
Concurrent crawls: 3
Extract entities: Off
```

**Thorough learning (15 min):**
```
Max resources: 20
Concurrent crawls: 3
Extract entities: On
```

**Deep dive (30 min):**
```
Max resources: 30
Concurrent crawls: 5
Extract entities: On
```

## Tips for Best Results

### ✅ Do's

1. **Be specific:**
   - ✓ "React hooks"
   - ✗ "React"

2. **Use technical terms:**
   - ✓ "Docker containers"
   - ✗ "container software"

3. **Start small:**
   - Begin with 5-10 resources
   - Add more if needed

4. **Check results:**
   - Review discovered sources
   - Re-run with adjustments if needed

### ❌ Don'ts

1. **Too broad:**
   - ✗ "Programming"
   - ✗ "Web development"

2. **Non-technical:**
   - ✗ "How to cook pasta"
   - ✗ "Best vacation spots"

3. **Too many resources at once:**
   - Avoid 30+ on first try
   - System may be slow

## Troubleshooting

### Issue: No resources discovered

**Solution:**
```bash
# Test internet connection
python -c "from ddgs import DDGS; print(DDGS().text('test', max_results=1))"

# If this fails, check:
# - Internet connection
# - Firewall settings
# - VPN if required
```

### Issue: Discovery works but processing fails

**Cause:** RAGFlow not configured

**Solution:**
- Discovery-only mode still works!
- Resources are shown, URLs provided
- Manual crawling possible
- See [Full RAG Setup](#full-rag-setup) below

### Issue: Slow processing

**Optimization:**
1. Reduce `max_resources` to 5-10
2. Disable entity extraction
3. Reduce concurrent crawls to 2
4. Check internet speed

### Issue: Some resources fail

**Normal behavior:**
- Some sites block crawlers
- Some content is protected
- Some URLs are invalid
- System continues with others

## Full RAG Setup

For complete functionality (vector search, knowledge graph, embeddings):

### 1. Choose Vector Storage

**Option A: Supabase (Cloud, Easiest)**
```bash
# Sign up at supabase.com
# Create a project
# Get your URL and key

export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-service-role-key"
```

**Option B: PostgreSQL (Local)**
```bash
# Install PostgreSQL with pgvector
# Create database

export PGVECTOR_HOST="localhost"
export PGVECTOR_DATABASE="notebookllama_rag"
export PGVECTOR_USER="postgres"
export PGVECTOR_PASSWORD="your-password"
```

### 2. Set Up Knowledge Graph (Optional)

```bash
# Install Neo4j
docker run -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:latest

export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"
```

### 3. Configure LLM Provider

**Option A: OpenAI**
```bash
export OPENAI_API_KEY="sk-..."
```

**Option B: Google Gemini**
```bash
export GOOGLE_API_KEY="..."
```

**Option C: Ollama (Local)**
```bash
# Install Ollama from ollama.ai
ollama run llama2

export OLLAMA_HOST="http://localhost:11434"
```

### 4. Test Setup

```bash
python test_topic_discovery.py
```

Expected output:
```
✅ PASSED: Topic Discovery Agent
✅ PASSED: RAGFlow Integration
🎉 ALL TESTS PASSED!
```

## Performance Expectations

### Discovery Phase (~5-10 seconds)
```
🔍 Searching DuckDuckGo for 6 different queries
📊 Ranking and filtering results
✅ Returns 10-20 high-quality URLs
```

### Crawling Phase (~20-40 seconds for 10 resources)
```
🌐 Parallel crawling (3 concurrent)
📄 Extracting markdown content
⏱️  ~2-4 seconds per URL
```

### Processing Phase (~20-30 seconds for 10 resources)
```
🔤 Generating embeddings
🗄️  Storing in vector database
🕸️  Extracting entities (if enabled)
💾 Saving to knowledge graph
```

**Total:** 45-80 seconds for 10 resources

## Next Steps

After discovering a topic:

1. **Search & Chat:**
   - Use "Enhanced RAG Chat"
   - Ask questions about the topic
   - Get answers with citations

2. **Browse Documents:**
   - Use "Document Management"
   - View all processed content
   - See summaries and highlights

3. **Explore Knowledge:**
   - Use knowledge graph search
   - Find related concepts
   - Discover connections

4. **Add More:**
   - Discover related topics
   - Go deeper on subtopics
   - Build comprehensive knowledge

## Example Session

```bash
# Start
streamlit run src/notebookllama/Home.py

# Discover
Topic: "FastAPI"
Resources: 15
Time: ~60 seconds

# Learn
Q: "What is FastAPI?"
A: [Answer from discovered docs with citations]

Q: "How do I create an API endpoint?"
A: [Code examples from tutorials]

Q: "FastAPI vs Flask differences?"
A: [Comparison from multiple sources]

# Explore More
Topics: "FastAPI authentication", "FastAPI testing", "FastAPI deployment"
```

## Support

- **Documentation:** `TOPIC_DISCOVERY_IMPLEMENTATION.md`
- **Examples:** `examples/topic_discovery_example.py`
- **Tests:** `test_topic_discovery.py`
- **Issues:** GitHub Issues

## Summary

Topic Discovery makes learning any technical topic as simple as:

1. **Enter a topic** ← "React hooks"
2. **Click a button** ← "Discover & Learn"
3. **Ask questions** ← "How does useState work?"

That's it! No manual searching, copying, or organizing needed. The system handles everything automatically.

Happy learning! 🚀

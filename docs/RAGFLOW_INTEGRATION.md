# RAGFlow Integration for NotebookLlama

This document provides comprehensive setup and usage instructions for the RAGFlow integration with NotebookLlama.

## Overview

The RAGFlow integration adds advanced Retrieval-Augmented Generation (RAG) capabilities to NotebookLlama, including:

- **Vector Search**: Semantic document search using Supabase vector storage
- **Knowledge Graph**: Entity relationships using Neo4j and Graphiti
- **Web Crawling**: Content extraction using Crawl4AI
- **Multi-LLM Support**: OpenAI, Google Gemini, Anthropic Claude, and Ollama

## Architecture

```
NotebookLlama + RAGFlow
├── Core NotebookLlama (unchanged)
│   ├── Document Management
│   ├── MCP Server
│   └── Streamlit UI
└── RAGFlow Integration (new)
    ├── Vector Storage (Supabase)
    ├── Knowledge Graph (Neo4j + Graphiti)
    ├── Web Crawling (Crawl4AI)
    └── Enhanced LLM Support
```

## Installation

### 1. Install Dependencies

The RAGFlow dependencies are included in the main `pyproject.toml`. Install with:

```bash
# Standard installation
pip install -e .

# Or with specific RAG extras (if defined)
pip install -e .[ragflow]
```

### 2. Required Services Setup

#### Supabase (Vector Storage)

1. Create a Supabase project at https://supabase.com
2. Get your project URL and API key
3. Add to your `.env` file:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-api-key
```

#### Neo4j (Knowledge Graph)

1. Install Neo4j locally or use Neo4j AuraDB
2. Create a database with credentials
3. Add to your `.env` file:

```bash
NEO4J_URI=neo4j://localhost:7687  # or bolt://your-aura-instance
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

#### LLM Providers

Configure at least one LLM provider:

```bash
# OpenAI
OPENAI_API_KEY=your-openai-key

# Google Gemini
GOOGLE_API_KEY=your-google-key

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-key

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
```

### 3. Run Setup Script

Execute the setup script to initialize databases and test connections:

```bash
python scripts/setup_ragflow_integration.py
```

This script will:
- Create Supabase database tables
- Test Neo4j connectivity
- Validate LLM providers
- Test web crawling functionality

### 4. Verify Installation

Run the integration tests to ensure everything works:

```bash
python scripts/test_integration.py
```

## Configuration

### Environment Variables

Complete `.env` configuration example:

```bash
# Required for RAG features
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=neo4j

# LLM Providers (at least one required)
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-key
ANTHROPIC_API_KEY=your-anthropic-key
OLLAMA_HOST=http://localhost:11434

# Feature toggles (optional)
ENABLE_RAG_FEATURES=true
ENABLE_WEB_CRAWLING=true
ENABLE_KNOWLEDGE_GRAPH=true

# Advanced settings (optional)
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=5
CRAWL_MAX_PAGES=10
GRAPH_MAX_ENTITIES=1000
```

### Feature Detection

The integration automatically detects available features based on configuration:

```python
from src.notebookllama.ragflow_integration import RAGFlowIntegration

integration = RAGFlowIntegration()
features = integration.get_available_features()

print("Available features:", features)
# Output: ['vector_search', 'knowledge_graph', 'web_crawling', 'multi_llm']
```

## Usage

### 1. Enhanced Document Management

Use the enhanced document manager for RAG-powered document processing:

```python
from src.notebookllama.documents import EnhancedDocumentManager

async def process_document():
    manager = EnhancedDocumentManager()
    
    # Add document with RAG processing
    doc = await manager.add_document(
        "path/to/document.pdf",
        enable_rag=True,
        extract_entities=True
    )
    
    # Hybrid search (vector + keyword)
    results = await manager.search_documents(
        "search query",
        method="hybrid",  # or "vector", "keyword"
        limit=5
    )
    
    return results
```

### 2. Web Content Processing

Crawl and process web content:

```python
async def process_url():
    manager = EnhancedDocumentManager()
    
    # Crawl and add URL
    doc = await manager.crawl_and_add_url(
        "https://example.com/article",
        extract_entities=True
    )
    
    return doc
```

### 3. Knowledge Graph Queries

Search the knowledge graph:

```python
from src.notebookllama.rag_clients.graphiti_client import search_knowledge_graph

async def graph_search():
    results = await search_knowledge_graph(
        "companies in AI industry",
        limit=10
    )
    
    for result in results:
        print(f"Entity: {result['name']}")
        print(f"Type: {result['type']}")
        print(f"Description: {result.get('description', 'N/A')}")
```

### 4. Multi-LLM Usage

Use different LLM providers:

```python
from src.notebookllama.rag_clients.llm_provider import get_llm_provider

async def use_llm():
    llm = get_llm_provider()
    
    # Get completion
    response = await llm.get_completion(
        "Explain quantum computing",
        provider="openai"  # or "google", "anthropic", "ollama"
    )
    
    # Get embeddings
    embeddings = await llm.get_embeddings(
        ["text to embed"],
        provider="openai"
    )
    
    return response, embeddings
```

### 5. Streamlit UI

The new Enhanced RAG Chat page provides a web interface:

1. Start the Streamlit app:
   ```bash
   streamlit run src/notebookllama/Home.py
   ```

2. Navigate to "Enhanced RAG Chat" page

3. Features available:
   - Upload documents with RAG processing
   - Search documents with multiple methods
   - Crawl web URLs
   - Chat with knowledge graph
   - Multi-LLM provider selection

### 6. MCP Server Tools

The MCP server includes new tools for RAG functionality:

```python
# Available tools:
# - enhanced_search: Advanced document search
# - crawl_and_process: Web crawling and processing  
# - knowledge_graph_search: Graph-based search
# - rag_statistics: Usage statistics

# Use via MCP client or programmatically
from src.notebookllama.server import create_mcp_server

server = create_mcp_server()
tools = server.list_tools()
print("Available tools:", [tool.name for tool in tools])
```

## Advanced Configuration

### Custom Embedding Models

Configure custom embedding models in the LLM provider:

```python
from src.notebookllama.rag_clients.llm_provider import LLMProvider

llm = LLMProvider()
llm.configure_embeddings(
    provider="openai",
    model="text-embedding-3-large",
    dimensions=1536
)
```

### Supabase Table Customization

The setup script creates default tables. For custom schemas:

```python
from src.notebookllama.rag_clients.supabase_client import create_custom_tables

await create_custom_tables(
    table_name="custom_documents",
    embedding_dimensions=1536
)
```

### Knowledge Graph Schema

Customize the knowledge graph schema:

```python
from src.notebookllama.rag_clients.graphiti_client import configure_schema

await configure_schema({
    "Person": ["name", "occupation", "location"],
    "Organization": ["name", "industry", "founded"],
    "Technology": ["name", "category", "description"]
})
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   ImportError: No module named 'supabase'
   ```
   Solution: Install dependencies with `pip install -e .`

2. **Supabase Connection Failed**
   ```
   Could not create Supabase client
   ```
   Solution: Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

3. **Neo4j Connection Failed**
   ```
   Could not connect to Neo4j
   ```
   Solution: Verify Neo4j is running and credentials are correct

4. **No LLM Providers Available**
   ```
   No LLM providers configured
   ```
   Solution: Add at least one LLM API key to `.env`

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in environment
export LOG_LEVEL=DEBUG
```

Run diagnostics:

```bash
# Test setup
python scripts/setup_ragflow_integration.py

# Test integration
python scripts/test_integration.py

# Check logs
tail -f ragflow_integration.log
```

### Performance Optimization

1. **Vector Search Optimization**
   - Adjust `RAG_CHUNK_SIZE` and `RAG_CHUNK_OVERLAP`
   - Use appropriate embedding models
   - Optimize Supabase queries

2. **Knowledge Graph Performance**
   - Limit entity extraction scope
   - Use graph indexes
   - Batch relationship creation

3. **Web Crawling Efficiency**
   - Set reasonable `CRAWL_MAX_PAGES`
   - Use crawling filters
   - Enable content caching

## Migration

### From Existing NotebookLlama

The integration is backward compatible. Existing functionality remains unchanged:

1. Install new dependencies
2. Add RAG configuration to `.env`
3. Run setup script
4. Existing documents can be enhanced with RAG processing

### Upgrading

To upgrade the RAGFlow integration:

1. Update dependencies: `pip install -e . --upgrade`
2. Run setup script: `python scripts/setup_ragflow_integration.py`
3. Test integration: `python scripts/test_integration.py`

## API Reference

### Core Classes

- `RAGFlowIntegration`: Main integration orchestrator
- `EnhancedDocumentManager`: Extended document management
- `LLMProvider`: Multi-LLM provider interface
- `CrawlManager`: Web crawling management

### Client Modules

- `supabase_client`: Vector storage operations
- `graphiti_client`: Knowledge graph operations
- `crawl_manager`: Web crawling operations
- `llm_provider`: LLM provider abstraction

### Tools

- `enhanced_search`: Advanced document search
- `crawl_and_process`: URL processing
- `knowledge_graph_search`: Graph queries
- `rag_statistics`: Usage analytics

## Support

For issues and questions:

1. Check the troubleshooting section
2. Run diagnostic scripts
3. Review logs and error messages
4. Create GitHub issues with details

## Contributing

To contribute to the RAGFlow integration:

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility

## License

The RAGFlow integration follows the same license as NotebookLlama.
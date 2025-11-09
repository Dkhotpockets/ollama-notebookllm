# Local Network Setup - Open Source RAGFlow Integration

This guide sets up NotebookLlama with RAGFlow using only **open-source software** that runs entirely on your local network.

## Architecture Overview

```
Your Local Network Setup
├── NotebookLlama + RAGFlow (this machine)
├── PostgreSQL + pgvector (local vector database)
├── Neo4j Community Edition (knowledge graph)
├── Ollama (local LLM models)
└── Optional: Elasticsearch (enhanced search)
```

## Required Open Source Components

### 1. PostgreSQL + pgvector (Vector Database)
**Replaces**: Supabase (cloud service)
- **PostgreSQL**: Open-source relational database
- **pgvector**: Vector similarity search extension
- **Benefits**: Full control, no external dependencies, excellent performance

### 2. Neo4j Community Edition (Knowledge Graph)
**Purpose**: Entity relationships and graph queries
- **Free**: Community edition with full graph capabilities
- **Local**: Runs entirely on your network
- **Web UI**: Built-in browser interface

### 3. Ollama (Local LLM Models)
**Purpose**: Large Language Models without API calls
- **Models**: Llama 3.1, Mistral, CodeLlama, etc.
- **API Compatible**: OpenAI-compatible API
- **Privacy**: Everything stays local

### 4. Optional: Elasticsearch (Enhanced Search)
**Purpose**: Advanced full-text search capabilities
- **Alternative to**: External search services
- **Features**: Powerful text analysis and search

## Step-by-Step Setup

### Step 1: Install PostgreSQL + pgvector

#### Windows (PostgreSQL)
```powershell
# Download PostgreSQL from https://www.postgresql.org/download/windows/
# Or use chocolatey
choco install postgresql

# Start PostgreSQL service
net start postgresql-x64-14
```

#### Install pgvector Extension
```sql
-- Connect to PostgreSQL as admin
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database for NotebookLlama
CREATE DATABASE notebookllama_rag;

-- Create user
CREATE USER raguser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE notebookllama_rag TO raguser;
```

### Step 2: Install Neo4j Community Edition

```powershell
# Download from https://neo4j.com/download-center/#community
# Or use chocolatey
choco install neo4j-community

# Start Neo4j
neo4j console

# Access web interface at http://localhost:7474
# Default credentials: neo4j/neo4j (change on first login)
```

### Step 3: Install Ollama

```powershell
# Download from https://ollama.ai
# Or use winget
winget install Ollama.Ollama

# Pull recommended models
ollama pull llama3.1:8b      # General purpose
ollama pull mistral:7b       # Fast and efficient
ollama pull nomic-embed-text # For embeddings

# Verify installation
ollama list
```

### Step 4: Install Elasticsearch (Optional)

```powershell
# Download from https://www.elastic.co/downloads/elasticsearch
# Or use chocolatey
choco install elasticsearch

# Start Elasticsearch
# Service should start automatically on http://localhost:9200
```

## Configuration

### Update Environment Variables

Create/update your `.env` file:

```bash
# PostgreSQL Vector Database (replaces Supabase)
DATABASE_URL=postgresql://raguser:secure_password@localhost:5432/notebookllama_rag
PGVECTOR_HOST=localhost
PGVECTOR_PORT=5432
PGVECTOR_DATABASE=notebookllama_rag
PGVECTOR_USER=raguser
PGVECTOR_PASSWORD=secure_password

# Neo4j Knowledge Graph
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# Ollama Local LLM
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Feature toggles for local setup
ENABLE_RAG_FEATURES=true
ENABLE_WEB_CRAWLING=true
ENABLE_KNOWLEDGE_GRAPH=true
USE_LOCAL_VECTOR_DB=true
USE_LOCAL_LLM=true

# Disable external services
SUPABASE_URL=
SUPABASE_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=

# Performance settings for local network
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=10
VECTOR_DIMENSIONS=1536
MAX_CONCURRENT_REQUESTS=4
```

### Network Access Configuration

To make it accessible on your local network:

#### 1. Configure PostgreSQL for Network Access

Edit `postgresql.conf`:
```conf
# Allow connections from local network
listen_addresses = '*'  # or '192.168.1.*' for specific subnet
```

Edit `pg_hba.conf`:
```conf
# Allow local network connections
host    notebookllama_rag    raguser    192.168.1.0/24    md5
```

#### 2. Configure Neo4j for Network Access

Edit `neo4j.conf`:
```conf
# Network connector configuration
dbms.default_listen_address=0.0.0.0
dbms.connector.bolt.listen_address=0.0.0.0:7687
dbms.connector.http.listen_address=0.0.0.0:7474
```

#### 3. Configure Ollama for Network Access

```bash
# Set environment variable for network binding
set OLLAMA_HOST=0.0.0.0:11434

# Restart Ollama service
```

#### 4. Configure NotebookLlama for Network Access

Update Streamlit configuration:
```toml
# .streamlit/config.toml
[server]
headless = true
port = 8501
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
```

## Custom RAG Client for PostgreSQL

I'll create a local PostgreSQL client to replace Supabase:

### PostgreSQL Vector Client

```python
# src/notebookllama/rag_clients/postgresql_client.py
import asyncpg
import numpy as np
from typing import List, Dict, Any, Optional
import asyncio
import os

class PostgreSQLVectorClient:
    """PostgreSQL + pgvector client for local vector storage"""
    
    def __init__(self):
        self.connection_string = os.getenv("DATABASE_URL")
        self.pool = None
    
    async def connect(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=2,
            max_size=10
        )
        await self._create_tables()
    
    async def _create_tables(self):
        """Create required tables with vector support"""
        async with self.pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create documents table with vector column
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create index for vector similarity search
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                ON documents USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
    
    async def add_document(self, content: str, embedding: List[float], 
                          metadata: Dict = None) -> int:
        """Add document with vector embedding"""
        async with self.pool.acquire() as conn:
            doc_id = await conn.fetchval("""
                INSERT INTO documents (content, embedding, metadata)
                VALUES ($1, $2, $3)
                RETURNING id;
            """, content, embedding, metadata or {})
            return doc_id
    
    async def search_similar(self, query_embedding: List[float], 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, content, metadata,
                       1 - (embedding <=> $1) as similarity
                FROM documents
                ORDER BY embedding <=> $1
                LIMIT $2;
            """, query_embedding, limit)
            
            return [dict(row) for row in results]
    
    async def hybrid_search(self, query: str, query_embedding: List[float],
                           limit: int = 5) -> List[Dict[str, Any]]:
        """Hybrid search combining text and vector similarity"""
        async with self.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT id, content, metadata,
                       1 - (embedding <=> $2) as vector_similarity,
                       ts_rank(to_tsvector('english', content), 
                               plainto_tsquery('english', $1)) as text_rank
                FROM documents
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                   OR (embedding <=> $2) < 0.5
                ORDER BY (1 - (embedding <=> $2)) * 0.7 + 
                         ts_rank(to_tsvector('english', content), 
                                plainto_tsquery('english', $1)) * 0.3 DESC
                LIMIT $3;
            """, query, query_embedding, limit)
            
            return [dict(row) for row in results]
```

## Testing Local Setup

### 1. Test PostgreSQL Connection
```bash
python -c "
import asyncio
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://raguser:secure_password@localhost:5432/notebookllama_rag')
    result = await conn.fetchval('SELECT version()')
    print(f'PostgreSQL: {result}')
    await conn.close()
asyncio.run(test())
"
```

### 2. Test Neo4j Connection
```bash
# Open http://localhost:7474 in browser
# Or use cypher-shell
cypher-shell -u neo4j -p your_password
```

### 3. Test Ollama
```bash
# Test API
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello, world!",
  "stream": false
}'

# List models
ollama list
```

### 4. Test NotebookLlama Integration
```bash
# Run local setup script
python scripts/setup_local_ragflow.py

# Run integration tests
python scripts/test_integration.py
```

## Performance Optimization

### PostgreSQL Tuning
```sql
-- Optimize for vector operations
ALTER SYSTEM SET shared_preload_libraries = 'vector';
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Neo4j Tuning
```conf
# neo4j.conf
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=1G
dbms.memory.pagecache.size=256m
```

### Ollama Optimization
```bash
# Set concurrent model handling
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_LOADED_MODELS=2

# For GPU acceleration (if available)
export OLLAMA_GPU=1
```

## Network Deployment

### Access from Other Devices

Once configured, access from any device on your network:

- **NotebookLlama UI**: `http://your-server-ip:8501`
- **Neo4j Browser**: `http://your-server-ip:7474`
- **Ollama API**: `http://your-server-ip:11434`

### Firewall Configuration

Open required ports:
```bash
# NotebookLlama Streamlit
netsh advfirewall firewall add rule name="NotebookLlama" dir=in action=allow protocol=TCP localport=8501

# PostgreSQL
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432

# Neo4j
netsh advfirewall firewall add rule name="Neo4j-Bolt" dir=in action=allow protocol=TCP localport=7687
netsh advfirewall firewall add rule name="Neo4j-HTTP" dir=in action=allow protocol=TCP localport=7474

# Ollama
netsh advfirewall firewall add rule name="Ollama" dir=in action=allow protocol=TCP localport=11434
```

## Benefits of This Setup

✅ **100% Open Source** - No proprietary software
✅ **Complete Privacy** - All data stays on your network  
✅ **No External Dependencies** - Works without internet
✅ **Full Control** - Customize everything
✅ **Cost Effective** - No subscription fees
✅ **High Performance** - Optimized for local hardware
✅ **Scalable** - Can distribute across multiple machines

## Maintenance

### Regular Tasks
- **PostgreSQL**: Regular VACUUM and index maintenance
- **Neo4j**: Monitor graph size and performance
- **Ollama**: Update models as needed
- **Backups**: Regular database backups

### Monitoring
- **PostgreSQL**: Check connection counts and query performance
- **Neo4j**: Monitor memory usage and graph statistics  
- **Ollama**: Monitor model loading and inference times
- **System**: CPU, memory, and disk usage

This setup gives you enterprise-grade RAG capabilities using only open-source software running on your local network!
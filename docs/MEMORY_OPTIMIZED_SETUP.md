# Memory-Optimized Local RAGFlow Setup for 16GB RAM

## 🧠 Memory Allocation Plan

With 16GB total RAM, here's the optimal allocation:
- **Windows OS**: ~4GB
- **Browser/Apps**: ~2GB  
- **Available for RAG**: ~10GB
- **Docker Services**: ~3GB
- **Ollama Models**: ~4-6GB (safe range)

## 📦 Recommended Ollama Models (Under 7B)

### Primary Models (Pick 1-2):

1. **Llama 3.1:8B** (4.7GB) - Best overall quality
   ```bash
   ollama pull llama3.1:8b
   ```

2. **Mistral 7B** (4.1GB) - Fastest, great for general tasks
   ```bash
   ollama pull mistral:7b
   ```

3. **Qwen2.5:7B** (4.4GB) - Excellent code understanding
   ```bash
   ollama pull qwen2.5:7b
   ```

### Specialized Models:

4. **Nomic-Embed-Text** (274MB) - Essential for embeddings
   ```bash
   ollama pull nomic-embed-text
   ```

5. **CodeLlama:7B** (3.8GB) - Code generation (if you need it)
   ```bash
   ollama pull codellama:7b
   ```

## 💡 Memory-Efficient Configuration

Create optimized settings for your laptop:

### Docker Resource Limits
Modify docker-compose.local.yml to use less memory:

```yaml
services:
  postgresql:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: notebookllama_rag
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  neo4j:
    image: neo4j:5.15-community
    environment:
      NEO4J_AUTH: neo4j/secure_password
      NEO4J_dbms_memory_heap_initial__size: 256m
      NEO4J_dbms_memory_heap_max__size: 512m
      NEO4J_dbms_memory_pagecache_size: 256m
    ports:
      - "7474:7474"
      - "7687:7687"
    deploy:
      resources:
        limits:
          memory: 768M

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms256m -Xmx512m"
    ports:
      - "9200:9200"
    deploy:
      resources:
        limits:
          memory: 768M
```

### Ollama Configuration
Configure Ollama for efficient memory usage:

```bash
# Set environment variables for memory optimization
set OLLAMA_NUM_PARALLEL=1
set OLLAMA_MAX_LOADED_MODELS=1
set OLLAMA_KEEP_ALIVE=5m
```

### NotebookLlama Configuration
Add to your .env:

```bash
# Memory optimization settings
RAG_CHUNK_SIZE=500          # Smaller chunks
RAG_CHUNK_OVERLAP=100       # Less overlap
RAG_TOP_K=3                 # Fewer results
MAX_CONCURRENT_REQUESTS=2   # Limit concurrent processing
VECTOR_DIMENSIONS=768       # Use smaller embeddings if supported

# Use efficient models
OLLAMA_DEFAULT_MODEL=mistral:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## 🚀 Recommended Installation Order

1. **Start Docker services** (already running)
2. **Install Ollama** 
3. **Pull one primary model** (start with mistral:7b - fastest)
4. **Pull embedding model**
5. **Test integration**
6. **Add more models as needed**

## 📊 Memory Monitoring

Keep an eye on memory usage:

```bash
# Check Docker memory usage
docker stats

# Check Ollama memory usage
ollama list
ollama show mistral:7b

# Windows Task Manager
# Monitor: Docker Desktop, Ollama, Python
```

## ⚡ Performance Tips

1. **Close unnecessary apps** while running RAG
2. **Use one model at a time** in Ollama
3. **Enable GPU acceleration** if you have discrete graphics
4. **Process documents in smaller batches**
5. **Use keyword search** when vector search is slow

## 🎯 Optimal Model Strategy

**Start Configuration:**
- **Mistral 7B** (4.1GB) - Fast general purpose
- **Nomic-embed-text** (274MB) - Embeddings
- **Total**: ~4.4GB

**If you need more capability later:**
- Replace Mistral with **Llama 3.1:8B** (4.7GB) for better quality
- Or add **Qwen2.5:7B** (4.4GB) for better code understanding

This setup should run smoothly on your 16GB laptop while giving you excellent RAG capabilities!
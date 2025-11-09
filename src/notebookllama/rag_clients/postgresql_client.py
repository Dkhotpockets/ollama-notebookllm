"""
PostgreSQL Vector Client for Local RAGFlow Integration

This module provides a local vector database client using PostgreSQL + pgvector
as a replacement for Supabase in the RAGFlow integration.
"""

import asyncio
import asyncpg
import numpy as np
from typing import List, Dict, Any, Optional, Union
import os
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PostgreSQLVectorClient:
    """PostgreSQL + pgvector client for local vector storage"""
    
    def __init__(self):
        self.connection_string = os.getenv(
            "DATABASE_URL", 
            f"postgresql://{os.getenv('PGVECTOR_USER', 'raguser')}:"
            f"{os.getenv('PGVECTOR_PASSWORD', 'password')}@"
            f"{os.getenv('PGVECTOR_HOST', 'localhost')}:"
            f"{os.getenv('PGVECTOR_PORT', '5432')}/"
            f"{os.getenv('PGVECTOR_DATABASE', 'notebookllama_rag')}"
        )
        self.pool = None
        self.vector_dimensions = int(os.getenv("VECTOR_DIMENSIONS", "1536"))
        
    async def connect(self) -> bool:
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
                command_timeout=60
            )
            await self._create_tables()
            logger.info("PostgreSQL vector client connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def _create_tables(self):
        """Create required tables with vector support"""
        async with self.pool.acquire() as conn:
            try:
                # Enable pgvector extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create documents table with vector column
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        content TEXT NOT NULL,
                        file_path TEXT,
                        file_type TEXT,
                        metadata JSONB DEFAULT '{{}}',
                        embedding vector({self.vector_dimensions}),
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Create full-text search index
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS documents_content_fts_idx 
                    ON documents USING GIN (to_tsvector('english', content));
                """)
                
                # Create vector similarity index (after some documents are added)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                    ON documents USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
                
                # Create chunks table for document segments
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                        chunk_index INTEGER,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{{}}',
                        embedding vector({self.vector_dimensions}),
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Index for chunk embeddings
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
                    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 50);
                """)
                
                # Create entities table for knowledge graph integration
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS entities (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        entity_type TEXT,
                        description TEXT,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Create document-entity relationships
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS document_entities (
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                        entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        confidence FLOAT DEFAULT 1.0,
                        PRIMARY KEY (document_id, entity_id)
                    );
                """)
                
                logger.info("Database tables created successfully")
                
            except Exception as e:
                logger.error(f"Failed to create tables: {e}")
                raise
    
    async def add_document(self, title: str, content: str, 
                          embedding: List[float], metadata: Dict = None,
                          file_path: str = None, file_type: str = None) -> int:
        """Add document with vector embedding"""
        async with self.pool.acquire() as conn:
            try:
                doc_id = await conn.fetchval("""
                    INSERT INTO documents (title, content, file_path, file_type, embedding, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id;
                """, title, content, file_path, file_type, embedding, json.dumps(metadata or {}))
                
                logger.info(f"Added document with ID: {doc_id}")
                return doc_id
                
            except Exception as e:
                logger.error(f"Failed to add document: {e}")
                raise
    
    async def add_document_chunk(self, document_id: int, chunk_index: int,
                                content: str, embedding: List[float],
                                metadata: Dict = None) -> int:
        """Add document chunk with vector embedding"""
        async with self.pool.acquire() as conn:
            try:
                chunk_id = await conn.fetchval("""
                    INSERT INTO document_chunks (document_id, chunk_index, content, embedding, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id;
                """, document_id, chunk_index, content, embedding, json.dumps(metadata or {}))
                
                return chunk_id
                
            except Exception as e:
                logger.error(f"Failed to add document chunk: {e}")
                raise
    
    async def search_similar(self, query_embedding: List[float], 
                           limit: int = 5, similarity_threshold: float = 0.1,
                           search_chunks: bool = True) -> List[Dict[str, Any]]:
        """Search for similar documents/chunks using vector similarity"""
        table = "document_chunks" if search_chunks else "documents"
        
        async with self.pool.acquire() as conn:
            try:
                if search_chunks:
                    results = await conn.fetch(f"""
                        SELECT dc.id, dc.content, dc.metadata, dc.document_id,
                               d.title, d.file_path, d.file_type,
                               1 - (dc.embedding <=> $1) as similarity
                        FROM document_chunks dc
                        JOIN documents d ON dc.document_id = d.id
                        WHERE 1 - (dc.embedding <=> $1) > $3
                        ORDER BY dc.embedding <=> $1
                        LIMIT $2;
                    """, query_embedding, limit, similarity_threshold)
                else:
                    results = await conn.fetch(f"""
                        SELECT id, title, content, file_path, file_type, metadata,
                               1 - (embedding <=> $1) as similarity
                        FROM documents
                        WHERE 1 - (embedding <=> $1) > $3
                        ORDER BY embedding <=> $1
                        LIMIT $2;
                    """, query_embedding, limit, similarity_threshold)
                
                return [dict(row) for row in results]
                
            except Exception as e:
                logger.error(f"Failed to search similar documents: {e}")
                return []
    
    async def keyword_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Full-text search using PostgreSQL's built-in capabilities"""
        async with self.pool.acquire() as conn:
            try:
                results = await conn.fetch("""
                    SELECT id, title, content, file_path, file_type, metadata,
                           ts_rank(to_tsvector('english', content), 
                                  plainto_tsquery('english', $1)) as rank
                    FROM documents
                    WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                    ORDER BY ts_rank(to_tsvector('english', content), 
                                   plainto_tsquery('english', $1)) DESC
                    LIMIT $2;
                """, query, limit)
                
                return [dict(row) for row in results]
                
            except Exception as e:
                logger.error(f"Failed to perform keyword search: {e}")
                return []
    
    async def hybrid_search(self, query: str, query_embedding: List[float],
                           limit: int = 5, vector_weight: float = 0.7,
                           text_weight: float = 0.3) -> List[Dict[str, Any]]:
        """Hybrid search combining text and vector similarity"""
        async with self.pool.acquire() as conn:
            try:
                results = await conn.fetch("""
                    SELECT d.id, d.title, d.content, d.file_path, d.file_type, d.metadata,
                           1 - (d.embedding <=> $2) as vector_similarity,
                           ts_rank(to_tsvector('english', d.content), 
                                  plainto_tsquery('english', $1)) as text_rank,
                           ((1 - (d.embedding <=> $2)) * $4 + 
                            ts_rank(to_tsvector('english', d.content), 
                                   plainto_tsquery('english', $1)) * $5) as combined_score
                    FROM documents d
                    WHERE to_tsvector('english', d.content) @@ plainto_tsquery('english', $1)
                       OR (d.embedding <=> $2) < 0.5
                    ORDER BY combined_score DESC
                    LIMIT $3;
                """, query, query_embedding, limit, vector_weight, text_weight)
                
                return [dict(row) for row in results]
                
            except Exception as e:
                logger.error(f"Failed to perform hybrid search: {e}")
                return []
    
    async def get_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchrow("""
                    SELECT id, title, content, file_path, file_type, metadata, created_at, updated_at
                    FROM documents
                    WHERE id = $1;
                """, document_id)
                
                return dict(result) if result else None
                
            except Exception as e:
                logger.error(f"Failed to get document {document_id}: {e}")
                return None
    
    async def list_documents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all documents with pagination"""
        async with self.pool.acquire() as conn:
            try:
                results = await conn.fetch("""
                    SELECT id, title, file_path, file_type, created_at, updated_at,
                           LENGTH(content) as content_length
                    FROM documents
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2;
                """, limit, offset)
                
                return [dict(row) for row in results]
                
            except Exception as e:
                logger.error(f"Failed to list documents: {e}")
                return []
    
    async def delete_document(self, document_id: int) -> bool:
        """Delete document and all associated chunks"""
        async with self.pool.acquire() as conn:
            try:
                # Delete will cascade to chunks and entities due to foreign keys
                result = await conn.execute("""
                    DELETE FROM documents WHERE id = $1;
                """, document_id)
                
                return result == "DELETE 1"
                
            except Exception as e:
                logger.error(f"Failed to delete document {document_id}: {e}")
                return False
    
    async def add_entity(self, name: str, entity_type: str, 
                        description: str = None, metadata: Dict = None) -> int:
        """Add entity to knowledge base"""
        async with self.pool.acquire() as conn:
            try:
                entity_id = await conn.fetchval("""
                    INSERT INTO entities (name, entity_type, description, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                    RETURNING id;
                """, name, entity_type, description, json.dumps(metadata or {}))
                
                return entity_id
                
            except Exception as e:
                logger.error(f"Failed to add entity: {e}")
                raise
    
    async def link_document_entity(self, document_id: int, entity_id: int, 
                                  confidence: float = 1.0) -> bool:
        """Link document to entity"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO document_entities (document_id, entity_id, confidence)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (document_id, entity_id) 
                    DO UPDATE SET confidence = $3;
                """, document_id, entity_id, confidence)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to link document to entity: {e}")
                return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        async with self.pool.acquire() as conn:
            try:
                stats = await conn.fetchrow("""
                    SELECT 
                        (SELECT COUNT(*) FROM documents) as total_documents,
                        (SELECT COUNT(*) FROM document_chunks) as total_chunks,
                        (SELECT COUNT(*) FROM entities) as total_entities,
                        (SELECT COUNT(*) FROM document_entities) as total_entity_links,
                        (SELECT AVG(LENGTH(content)) FROM documents) as avg_document_length;
                """)
                
                return dict(stats)
                
            except Exception as e:
                logger.error(f"Failed to get statistics: {e}")
                return {}


# Utility functions for integration
def create_postgresql_client() -> Optional[PostgreSQLVectorClient]:
    """Create PostgreSQL client if configuration is available"""
    required_vars = ["PGVECTOR_HOST", "PGVECTOR_DATABASE", "PGVECTOR_USER", "PGVECTOR_PASSWORD"]
    
    if not all(os.getenv(var) for var in required_vars):
        logger.warning("PostgreSQL configuration not complete, skipping vector client")
        return None
    
    return PostgreSQLVectorClient()


async def setup_postgresql_tables(client: PostgreSQLVectorClient) -> bool:
    """Setup PostgreSQL tables for RAG integration"""
    try:
        connected = await client.connect()
        if connected:
            logger.info("PostgreSQL tables setup completed")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to setup PostgreSQL tables: {e}")
        return False


async def test_postgresql_connection() -> Dict[str, Any]:
    """Test PostgreSQL connection and capabilities"""
    client = create_postgresql_client()
    
    if not client:
        return {"status": "error", "error": "No PostgreSQL configuration"}
    
    try:
        connected = await client.connect()
        
        if not connected:
            return {"status": "error", "error": "Could not connect to PostgreSQL"}
        
        # Test vector operations
        test_embedding = [0.1] * client.vector_dimensions
        doc_id = await client.add_document(
            title="Test Document",
            content="This is a test document for PostgreSQL vector operations.",
            embedding=test_embedding,
            metadata={"test": True}
        )
        
        # Test search
        results = await client.search_similar(test_embedding, limit=1)
        
        # Clean up
        await client.delete_document(doc_id)
        await client.disconnect()
        
        return {
            "status": "success",
            "vector_search_works": len(results) > 0,
            "vector_dimensions": client.vector_dimensions
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}
"""
Supabase Vector Storage Client for NotebookLlama
Enhanced from RAGFlow-Slim integration
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


def create_supabase_client(url: Optional[str] = None, key: Optional[str] = None) -> Optional[Client]:
    """Create Supabase client with environment fallback"""
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase not available - install with: pip install supabase")
        return None
    
    url = url or os.getenv("SUPABASE_URL")
    key = key or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        logger.warning("Supabase URL or KEY not configured")
        return None
    
    try:
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        return None


async def setup_supabase_tables(supabase_client: Client) -> bool:
    """Setup required tables for RAG functionality"""
    if not supabase_client:
        return False
    
    try:
        # SQL to create tables with vector extension
        setup_sql = """
        -- Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Create documents table (matches Supabase schema)
        CREATE TABLE IF NOT EXISTS documents (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            url TEXT,
            content_type TEXT DEFAULT 'text',
            metadata JSONB DEFAULT '{}',
            embedding vector(1536),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create index for vector similarity search
        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
        ON documents USING ivfflat (embedding vector_cosine_ops);
        
        -- Create crawl jobs table
        CREATE TABLE IF NOT EXISTS crawl_jobs (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            content TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        
        -- RPC function for vector similarity search
        CREATE OR REPLACE FUNCTION search_documents(
            query_embedding vector(1536),
            similarity_threshold float DEFAULT 0.7,
            match_count int DEFAULT 10
        )
        RETURNS TABLE(
            id int,
            title text,
            content text,
            title text,
            content text,
            url text,
            metadata jsonb,
            similarity float
        )
        LANGUAGE sql STABLE
        AS $$
            SELECT 
                documents.id,
                documents.title,
                documents.content,
                documents.url,
                documents.metadata,
                1 - (documents.embedding <=> query_embedding) as similarity
            FROM documents
            WHERE 1 - (documents.embedding <=> query_embedding) > similarity_threshold
            ORDER BY documents.embedding <=> query_embedding
            LIMIT match_count;
        $$;
        """
        
        # Execute setup SQL
        result = supabase_client.postgrest.rpc("exec", {"sql": setup_sql})
        logger.info("Supabase tables setup completed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup Supabase tables: {e}")
        return False


async def generate_embedding(text: str, provider: str = "openai") -> Optional[List[float]]:
    """Generate embedding for text using specified provider"""
    try:
        if provider == "openai":
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"  # 1536 dimensions
            )
            return response.data[0].embedding
        
        elif provider == "ollama":
            import aiohttp
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ollama_host}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("embedding")
        
        # Fallback: simple hash-based embedding (for testing)
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        # Create a simple 1536-dimensional vector from hash
        embedding = []
        hash_bytes = hash_obj.digest()
        for i in range(1536):
            embedding.append((hash_bytes[i % len(hash_bytes)] - 128) / 128.0)
        return embedding
            
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


async def add_document_to_supabase(
    supabase_client: Client,
    content: str,
    metadata: Dict[str, Any],
    title: Optional[str] = None,
    summary: Optional[str] = None
) -> bool:
    """Add document with vector embedding to Supabase"""
    if not supabase_client:
        return False
    
    try:
        # Generate embedding
        embedding = await generate_embedding(content)
        if not embedding:
            logger.warning("No embedding generated, storing without vector search capability")
        
        # Prepare document data
        doc_data = {
            "title": title or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content": content,
            "summary": summary or "",
            "metadata": metadata,
            "embedding": embedding,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Map to correct table schema
        # Supabase table is 'documents' with columns: id, title, content, url, content_type, metadata, embedding, created_at, updated_at
        # Ensure title is never None (required by Supabase schema)
        final_title = title or metadata.get("title") if metadata else None
        if not final_title:
            final_title = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Serialize datetime objects in metadata for JSON storage
        def serialize_metadata(meta):
            if not meta:
                return {}
            serialized = {}
            for key, value in meta.items():
                if isinstance(value, datetime):
                    serialized[key] = value.isoformat()
                elif hasattr(value, 'isoformat'):
                    serialized[key] = value.isoformat()
                else:
                    serialized[key] = value
            return serialized
        
        doc_insert = {
            "title": final_title,
            "content": content,
            "url": metadata.get("url", "") if metadata else "",
            "content_type": metadata.get("content_type", "text") if metadata else "text",
            "metadata": serialize_metadata(metadata),
            "embedding": embedding
        }
        
        # Insert into Supabase
        result = supabase_client.table("documents").insert(doc_insert).execute()
        
        if result.data:
            logger.info(f"Document added to Supabase: {title}")
            return True
        else:
            logger.error("Failed to add document to Supabase")
            return False
            
    except Exception as e:
        logger.error(f"Error adding document to Supabase: {e}")
        return False


async def search_documents_supabase(
    supabase_client: Client,
    query: str,
    limit: int = 10,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Search documents using vector similarity"""
    if not supabase_client:
        return []
    
    try:
        # Generate query embedding
        query_embedding = await generate_embedding(query)
        if not query_embedding:
            logger.warning("No query embedding, falling back to text search")
            # Fallback to text search
            result = supabase_client.table("documents").select("*").ilike("content", f"%{query}%").limit(limit).execute()
            return result.data or []
        
        # Use RPC function for vector search
        result = supabase_client.rpc(
            "search_documents",
            {
                "query_embedding": query_embedding,
                "similarity_threshold": similarity_threshold,
                "match_count": limit
            }
        ).execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        # Fallback to simple text search
        try:
            result = supabase_client.table("documents").select("*").ilike("content", f"%{query}%").limit(limit).execute()
            return result.data or []
        except:
            return []


async def get_document_by_name(
    supabase_client: Client,
    title: str
) -> Optional[Dict[str, Any]]:
    """Get specific document by name"""
    if not supabase_client:
        return None
    
    try:
        result = supabase_client.table("documents").select("*").eq("title", title).execute()
        if result.data:
            return result.data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return None


async def list_documents(supabase_client: Client, limit: int = 50) -> List[Dict[str, Any]]:
    """List all documents with metadata"""
    if not supabase_client:
        return []
    
    try:
        result = supabase_client.table("documents").select("id,title,summary,metadata,created_at").order("created_at", desc=True).limit(limit).execute()
        return result.data or []
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return []


async def delete_document(supabase_client: Client, document_id: int) -> bool:
    """Delete document by ID"""
    if not supabase_client:
        return False
    
    try:
        result = supabase_client.table("documents").delete().eq("id", document_id).execute()
        return len(result.data) > 0
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return False


# Compatibility layer with NotebookLlama's existing document structure
class SupabaseDocumentAdapter:
    """Adapter to make Supabase compatible with NotebookLlama's ManagedDocument"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
    
    async def add_managed_document(self, doc) -> bool:
        """Add ManagedDocument to Supabase with vector capabilities"""
        metadata = {
            "q_and_a": doc.q_and_a,
            "mindmap": doc.mindmap,
            "bullet_points": doc.bullet_points,
            "source": "notebookllama"
        }
        
        return await add_document_to_supabase(
            self.client,
            content=doc.content,
            metadata=metadata,
            title=doc.title,
            summary=doc.summary
        )
    
    async def search_managed_documents(self, query: str, limit: int = 10) -> List:
        """Search with conversion back to ManagedDocument structure"""
        results = await search_documents_supabase(self.client, query, limit)
        
        # Convert back to ManagedDocument-like structure
        managed_docs = []
        for result in results:
            from ..documents import ManagedDocument
            doc = ManagedDocument(
                title=result.get("title", ""),
                content=result.get("content", ""),
                summary=result.get("summary", ""),
                q_and_a=result.get("metadata", {}).get("q_and_a", ""),
                mindmap=result.get("metadata", {}).get("mindmap", ""),
                bullet_points=result.get("metadata", {}).get("bullet_points", "")
            )
            managed_docs.append(doc)
        
        return managed_docs
    
    def get_names(self) -> List[str]:
        """Get list of document names (titles) from Supabase"""
        try:
            import asyncio
            # Try to get or create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function
            if loop.is_running():
                # If loop is already running, use thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, list_documents(self.client, limit=100))
                    documents = future.result()
            else:
                documents = loop.run_until_complete(list_documents(self.client, limit=100))
            
            # Extract titles
            names = [doc.get("title", f"doc_{i}") for i, doc in enumerate(documents)]
            return names
        except Exception as e:
            logger.warning(f"Error retrieving document names: {e}")
            return []
    
    def get_documents(self, names: Optional[List[str]] = None) -> List:
        """Get documents by names (titles) from Supabase"""
        try:
            import asyncio
            # Try to get or create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            from ..documents import ManagedDocument
            
            if not names:
                # Return empty list if no names provided
                return []
            
            # Run async function to get documents
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # For each name, search for matching documents
                    all_results = []
                    for name in names:
                        future = executor.submit(asyncio.run, list_documents(self.client, limit=100))
                        docs = future.result()
                        # Filter by title
                        matching = [d for d in docs if d.get("title", "").lower() == name.lower()]
                        all_results.extend(matching)
            else:
                all_results = []
                for name in names:
                    docs = loop.run_until_complete(list_documents(self.client, limit=100))
                    # Filter by title
                    matching = [d for d in docs if d.get("title", "").lower() == name.lower()]
                    all_results.extend(matching)
            
            # Convert to ManagedDocument structure
            managed_docs = []
            for result in all_results:
                doc = ManagedDocument(
                    document_name=result.get("title", ""),
                    content=result.get("content", ""),
                    summary=result.get("summary", ""),
                    q_and_a=result.get("metadata", {}).get("q_and_a", ""),
                    mindmap=result.get("metadata", {}).get("mindmap", ""),
                    bullet_points=result.get("metadata", {}).get("bullet_points", "")
                )
                managed_docs.append(doc)
            
            return managed_docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
"""
RAGFlow-Slim Integration for NotebookLlama

This module provides hybrid RAG capabilities including:
- Vector search with Supabase
- Knowledge graph with Neo4j + Graphiti  
- Web crawling with Crawl4AI
- Multi-provider LLM support
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class RAGFlowConfig:
    """Configuration for RAGFlow integration"""
    # Cloud vector storage (Supabase)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # Local vector storage (PostgreSQL)
    postgresql_host: Optional[str] = None
    postgresql_database: Optional[str] = None
    postgresql_user: Optional[str] = None
    postgresql_password: Optional[str] = None
    
    # Knowledge graph
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    
    # LLM providers
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_host: Optional[str] = None
    ragflow_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'RAGFlowConfig':
        """Load configuration from environment variables"""
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY"),
            postgresql_host=os.getenv("PGVECTOR_HOST"),
            postgresql_database=os.getenv("PGVECTOR_DATABASE"),
            postgresql_user=os.getenv("PGVECTOR_USER"),
            postgresql_password=os.getenv("PGVECTOR_PASSWORD"),
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            ragflow_api_key=os.getenv("RAGFLOW_API_KEY", "changeme")
        )


class RAGFlowIntegration:
    """Main integration class for RAGFlow capabilities"""
    
    def __init__(self, config: Optional[RAGFlowConfig] = None):
        self.config = config or RAGFlowConfig.from_env()
        self._supabase_client = None
        self._postgresql_client = None
        self._graphiti_client = None
        self._crawl_manager = None
        self._llm_provider = None
        
    @property
    def available_features(self) -> Dict[str, bool]:
        """Check which RAGFlow features are available based on configuration"""
        # Vector search available via Supabase OR PostgreSQL
        vector_search_available = (
            bool(self.config.supabase_url and self.config.supabase_key) or
            bool(self.config.postgresql_host and self.config.postgresql_user and self.config.postgresql_password)
        )
        
        return {
            "vector_search": vector_search_available,
            "supabase_vector": bool(self.config.supabase_url and self.config.supabase_key),
            "postgresql_vector": bool(self.config.postgresql_host and self.config.postgresql_user and self.config.postgresql_password),
            "knowledge_graph": bool(self.config.neo4j_password),
            "web_crawling": True,  # Crawl4AI doesn't need external auth
            "google_gemini": bool(self.config.google_api_key),
            "openai": bool(self.config.openai_api_key),
            "ollama": True  # Ollama assumed available locally
        }
    
    def get_vector_client(self):
        """Get vector client (Supabase or PostgreSQL)"""
        # Prefer Supabase if configured, fall back to PostgreSQL
        if self.config.supabase_url and self.config.supabase_key:
            return self.get_supabase_client()
        elif self.config.postgresql_host:
            return self.get_postgresql_client()
        return None
    
    def get_supabase_client(self):
        """Get or create Supabase client"""
        if self._supabase_client is None and self.available_features["supabase_vector"]:
            try:
                from .rag_clients.supabase_client import create_supabase_client
                self._supabase_client = create_supabase_client(
                    url=self.config.supabase_url,
                    key=self.config.supabase_key
                )
            except ImportError:
                logger.warning("Supabase not available - trying PostgreSQL fallback")
        return self._supabase_client
    
    def get_postgresql_client(self):
        """Get or create PostgreSQL client"""
        if self._postgresql_client is None and self.available_features["postgresql_vector"]:
            try:
                from .rag_clients.postgresql_client import create_postgresql_client
                self._postgresql_client = create_postgresql_client()
            except ImportError:
                logger.warning("PostgreSQL client not available - vector search disabled")
            except Exception as e:
                logger.error(f"Failed to create PostgreSQL client: {e}")
        return self._postgresql_client
    
    def get_graphiti_client(self):
        """Get or create Graphiti client"""
        if self._graphiti_client is None and self.available_features["knowledge_graph"]:
            try:
                from .rag_clients.graphiti_client import create_graphiti_client
                self._graphiti_client = create_graphiti_client(
                    neo4j_uri=self.config.neo4j_uri,
                    neo4j_user=self.config.neo4j_user,
                    neo4j_password=self.config.neo4j_password
                )
            except ImportError:
                logger.warning("Graphiti not available - knowledge graph disabled")
        return self._graphiti_client
    
    def get_crawl_manager(self):
        """Get or create Crawl4AI manager"""
        if self._crawl_manager is None:
            try:
                from .rag_clients.crawl_manager import CrawlJobManager
                # Initialize with Supabase if available, otherwise use local storage
                storage_client = self.get_supabase_client()
                self._crawl_manager = CrawlJobManager(storage_client)
            except ImportError:
                logger.warning("Crawl4AI not available - web crawling disabled")
        return self._crawl_manager
    
    def get_llm_provider(self):
        """Get or create multi-provider LLM client"""
        if self._llm_provider is None:
            try:
                from .rag_clients.llm_provider import MultiLLMProvider
                self._llm_provider = MultiLLMProvider(
                    google_api_key=self.config.google_api_key,
                    openai_api_key=self.config.openai_api_key,
                    ollama_host=self.config.ollama_host
                )
            except ImportError:
                logger.warning("Multi-LLM provider not available")
        return self._llm_provider
    
    async def hybrid_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform hybrid search combining vector and graph results"""
        results = {"vector_results": [], "graph_results": [], "combined_score": []}
        
        # Vector search
        if self.available_features["vector_search"]:
            supabase = self.get_supabase_client()
            if supabase:
                try:
                    from .rag_clients.supabase_client import search_documents_supabase
                    vector_results = await search_documents_supabase(
                        supabase, query, limit=limit
                    )
                    results["vector_results"] = vector_results
                except Exception as e:
                    logger.error(f"Vector search error: {e}")
        
        # Knowledge graph search
        if self.available_features["knowledge_graph"]:
            graphiti = self.get_graphiti_client()
            if graphiti:
                try:
                    from .rag_clients.graphiti_client import search_graph
                    graph_results = await search_graph(query, limit=limit)
                    results["graph_results"] = graph_results
                except Exception as e:
                    logger.error(f"Graph search error: {e}")
        
        return results
    
    async def add_document_with_extraction(self,
                                         content: str,
                                         metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add document with full RAG processing: vector storage + entity extraction"""
        results = {"vector_stored": False, "entities_extracted": False, "basic_stored": False, "errors": []}

        # Store in vector database
        if self.available_features["vector_search"]:
            supabase = self.get_supabase_client()
            if supabase:
                try:
                    from .rag_clients.supabase_client import add_document_to_supabase
                    await add_document_to_supabase(
                        supabase, content, metadata or {}
                    )
                    results["vector_stored"] = True
                except Exception as e:
                    results["errors"].append(f"Vector storage error: {e}")

        # Extract entities and relationships
        if self.available_features["knowledge_graph"]:
            try:
                from .rag_clients.graphiti_client import add_episode
                await add_episode(content, metadata)
                results["entities_extracted"] = True
            except Exception as e:
                results["errors"].append(f"Entity extraction error: {e}")

        # Fallback: Store in basic DocumentManager if no RAG available
        if not results["vector_stored"] and not results["entities_extracted"]:
            try:
                from .documents import DocumentManager, ManagedDocument
                import os

                # Get database connection with fallback to SQLite
                db_url = os.getenv("DATABASE_URL")
                doc_manager = None

                # Try PostgreSQL first if configured
                if not db_url:
                    pgql_db = os.getenv("pgql_db", "notebookllama")
                    pgql_user = os.getenv("pgql_user", "postgres")
                    pgql_psw = os.getenv("pgql_psw", "password")
                    pgql_host = os.getenv("pgql_host", "localhost")
                    pgql_port = os.getenv("pgql_port", "5432")

                    # Check if PostgreSQL env vars look valid
                    if pgql_user not in ["localhost", ""] and pgql_psw not in ["", "your-password", "password"]:
                        db_url = f"postgresql://{pgql_user}:{pgql_psw}@{pgql_host}:{pgql_port}/{pgql_db}"

                # Try to create document manager with PostgreSQL
                if db_url:
                    try:
                        doc_manager = DocumentManager(engine_url=db_url)
                        # Test connection
                        doc_manager.get_names()  # This will fail if DB not accessible
                    except Exception as pg_error:
                        logger.warning(f"PostgreSQL not available: {pg_error}, falling back to SQLite")
                        doc_manager = None

                # Fallback to SQLite if PostgreSQL failed or not configured
                if doc_manager is None:
                    import tempfile
                    sqlite_path = os.path.join(tempfile.gettempdir(), "notebookllama_crawled.db")
                    db_url = f"sqlite:///{sqlite_path}"
                    logger.info(f"Using SQLite fallback: {sqlite_path}")
                    doc_manager = DocumentManager(engine_url=db_url)

                # Create document
                doc_name = metadata.get("document_name", metadata.get("source_url", "crawled_document"))
                # Truncate long URLs for document name
                if len(doc_name) > 200:
                    doc_name = doc_name[:197] + "..."

                # Create summary from first 500 chars
                summary = content[:500] + "..." if len(content) > 500 else content

                document = ManagedDocument(
                    document_name=doc_name,
                    content=content,
                    summary=summary,
                    q_and_a="",
                    mindmap="",
                    bullet_points=""
                )

                # Store document
                doc_manager.put_documents([document])
                results["basic_stored"] = True
                logger.info(f"Stored document in basic storage: {doc_name}")

            except Exception as e:
                results["errors"].append(f"Basic storage error: {e}")
                logger.error(f"Failed to store in basic storage: {e}")

        return results
    
    async def crawl_and_process_url(self, url: str,
                                  extract_entities: bool = True) -> Dict[str, Any]:
        """Crawl URL and process content with full RAG pipeline"""
        results = {"crawled": False, "processed": False, "content": "", "errors": []}

        crawl_manager = self.get_crawl_manager()
        if not crawl_manager:
            results["errors"].append("Crawl manager not available")
            return results

        try:
            from .rag_clients.crawl_manager import CrawlJobRequest, CrawlStatus

            # Create crawl job
            crawl_request = CrawlJobRequest(
                url=url,
                extract_entities=extract_entities,
                politeness_delay=1.0
            )

            # Execute crawl
            crawl_response = await crawl_manager.create_and_execute_job(crawl_request)

            # Check status using enum comparison
            if crawl_response.status == CrawlStatus.COMPLETED:
                results["crawled"] = True
                results["content"] = crawl_response.content

                # Process crawled content through RAG pipeline
                if crawl_response.content:
                    processing_results = await self.add_document_with_extraction(
                        content=crawl_response.content,
                        metadata={"source_url": url, "crawled_at": datetime.utcnow().isoformat()}
                    )
                    # Consider processed if stored in vector DB, knowledge graph, OR basic storage
                    results["processed"] = (
                        processing_results.get("vector_stored", False) or
                        processing_results.get("entities_extracted", False) or
                        processing_results.get("basic_stored", False)
                    )
                    results["errors"].extend(processing_results.get("errors", []))
            else:
                results["errors"].append(f"Crawl failed: {crawl_response.status.value if hasattr(crawl_response.status, 'value') else crawl_response.status}")

        except Exception as e:
            results["errors"].append(f"Crawl processing error: {e}")

        return results

    async def discover_and_process_topic(self,
                                       topic: str,
                                       max_resources: int = 10,
                                       max_concurrent_crawls: int = 3,
                                       extract_entities: bool = True,
                                       progress_callback = None) -> Dict[str, Any]:
        """
        Discover and process learning resources for a topic.

        This method:
        1. Uses TopicDiscoveryAgent to find relevant resources
        2. Crawls discovered URLs (with rate limiting)
        3. Processes content through RAG pipeline (vector + graph)
        4. Calls progress_callback with status updates if provided

        Args:
            topic: Topic to learn about
            max_resources: Maximum resources to discover
            max_concurrent_crawls: Concurrent crawl limit
            extract_entities: Whether to extract entities
            progress_callback: Optional callback(status_dict) for progress updates

        Returns:
            Dictionary with processing results
        """
        results = {
            "topic": topic,
            "discovered": 0,
            "crawled": 0,
            "processed": 0,
            "resources": [],
            "errors": []
        }

        try:
            from .agents.topic_discovery_agent import TopicDiscoveryAgent

            # Step 1: Discover resources
            if progress_callback:
                progress_callback({"status": "discovering", "message": f"Searching for resources about {topic}..."})

            agent = TopicDiscoveryAgent(max_results_per_query=5)
            discovered_resources = await agent.discover_resources(topic, max_resources)
            results["discovered"] = len(discovered_resources)

            if not discovered_resources:
                results["errors"].append("No resources discovered")
                return results

            logger.info(f"Discovered {len(discovered_resources)} resources for topic: {topic}")

            # Step 2: Crawl and process resources with concurrency control
            semaphore = asyncio.Semaphore(max_concurrent_crawls)

            async def crawl_and_track(resource):
                """Helper to crawl a single resource with semaphore"""
                async with semaphore:
                    try:
                        if progress_callback:
                            progress_callback({
                                "status": "crawling",
                                "message": f"Crawling {resource.title}...",
                                "current": results["crawled"] + 1,
                                "total": len(discovered_resources)
                            })

                        crawl_result = await self.crawl_and_process_url(
                            resource.url,
                            extract_entities=extract_entities
                        )

                        resource_data = {
                            "url": resource.url,
                            "title": resource.title,
                            "source_type": resource.source_type,
                            "priority_score": resource.priority_score,
                            "crawled": crawl_result["crawled"],
                            "processed": crawl_result["processed"],
                            "content_length": len(crawl_result.get("content", "")),
                            "errors": crawl_result.get("errors", [])
                        }

                        if crawl_result["crawled"]:
                            results["crawled"] += 1
                        if crawl_result["processed"]:
                            results["processed"] += 1

                        results["resources"].append(resource_data)

                        if crawl_result.get("errors"):
                            results["errors"].extend(crawl_result["errors"])

                    except Exception as e:
                        error_msg = f"Error processing {resource.url}: {e}"
                        logger.error(error_msg)
                        results["errors"].append(error_msg)

            # Execute crawls concurrently
            crawl_tasks = [crawl_and_track(resource) for resource in discovered_resources]
            await asyncio.gather(*crawl_tasks, return_exceptions=True)

            # Step 3: Final status
            if progress_callback:
                progress_callback({
                    "status": "completed",
                    "message": f"Processed {results['processed']} resources about {topic}",
                    "results": results
                })

            logger.info(f"Topic discovery complete: {results['processed']}/{results['discovered']} resources processed")

        except ImportError as e:
            error_msg = f"Topic discovery dependencies not available: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        except Exception as e:
            error_msg = f"Topic discovery error: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results


# Global instance for easy access
_ragflow_integration = None

def get_ragflow_integration() -> RAGFlowIntegration:
    """Get global RAGFlow integration instance"""
    global _ragflow_integration
    if _ragflow_integration is None:
        _ragflow_integration = RAGFlowIntegration()
    return _ragflow_integration


def is_ragflow_available() -> bool:
    """Check if any RAGFlow features are available"""
    integration = get_ragflow_integration()
    features = integration.available_features
    return any(features.values())


# Convenience functions for common operations
async def enhanced_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """Convenience function for hybrid search"""
    integration = get_ragflow_integration()
    return await integration.hybrid_search(query, limit)


async def enhanced_document_add(content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function for enhanced document processing"""
    integration = get_ragflow_integration()
    return await integration.add_document_with_extraction(content, metadata)


async def crawl_url(url: str, extract_entities: bool = True) -> Dict[str, Any]:
    """Convenience function for URL crawling"""
    integration = get_ragflow_integration()
    return await integration.crawl_and_process_url(url, extract_entities)


async def discover_and_process_topic(topic: str,
                                    max_resources: int = 10,
                                    max_concurrent_crawls: int = 3,
                                    extract_entities: bool = True) -> Dict[str, Any]:
    """
    Discover and process learning resources for a topic.

    This is a high-level convenience function that:
    1. Discovers relevant resources using TopicDiscoveryAgent
    2. Crawls discovered URLs
    3. Processes content through the RAG pipeline

    Args:
        topic: Topic to learn about (e.g., "TypeScript")
        max_resources: Maximum number of resources to discover
        max_concurrent_crawls: Maximum concurrent crawl operations
        extract_entities: Whether to extract entities from crawled content

    Returns:
        Dictionary with results including:
        - discovered: Number of resources discovered
        - crawled: Number successfully crawled
        - processed: Number successfully processed
        - resources: List of processed resource metadata
        - errors: List of errors encountered
    """
    integration = get_ragflow_integration()
    return await integration.discover_and_process_topic(
        topic=topic,
        max_resources=max_resources,
        max_concurrent_crawls=max_concurrent_crawls,
        extract_entities=extract_entities
    )
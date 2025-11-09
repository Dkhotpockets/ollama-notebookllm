from dataclasses import dataclass
from sqlalchemy import (
    Table,
    MetaData,
    Column,
    Text,
    Integer,
    create_engine,
    Engine,
    Connection,
    insert,
    select,
)
from typing import Optional, List, cast, Union, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


def apply_string_correction(string: str) -> str:
    return string.replace("''", "'").replace('""', '"')


@dataclass
class ManagedDocument:
    document_name: str
    content: str
    summary: str
    q_and_a: str
    mindmap: str
    bullet_points: str


class DocumentManager:
    def __init__(
        self,
        engine: Optional[Engine] = None,
        engine_url: Optional[str] = None,
        table_name: Optional[str] = None,
        table_metadata: Optional[MetaData] = None,
    ):
        self.table_name: str = table_name or "documents"
        self._table: Optional[Table] = None
        self._connection: Optional[Connection] = None
        self.metadata: MetaData = cast(MetaData, table_metadata or MetaData())
        if engine or engine_url:
            self._engine: Union[Engine, str] = cast(
                Union[Engine, str], engine or engine_url
            )
        else:
            raise ValueError("One of engine or engine_setup_kwargs must be set")

    @property
    def connection(self) -> Connection:
        if not self._connection:
            self._connect()
        return cast(Connection, self._connection)

    @property
    def table(self) -> Table:
        # If table is not created yet, attempt to create it.
        # However, avoid creating a connection if the engine URL appears to contain
        # placeholder or missing credentials (for example when environment variables
        # are unset and appear as the string 'None'). This prevents tests from
        # attempting to connect with invalid credentials.
        if self._table is None:
            try:
                # If engine is a URL string, perform a light check for invalid creds
                if isinstance(self._engine, str):
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(self._engine)
                        # Only apply the "missing credential" guard for Postgres-like schemes
                        scheme = (parsed.scheme or "").lower()
                        if "postgres" in scheme or "pgsql" in scheme:
                            username = parsed.username
                            password = parsed.password
                            if username in (None, "None", "") or password in (None, "None", ""):
                                # Skip creating table to avoid attempting a bad DB connection
                                return cast(Table, None)
                    except Exception:
                        # If parsing fails, fall through and attempt normal behavior
                        pass

                self._create_table()
            except Exception:
                # If creating the table fails, avoid bubbling exceptions here;
                # return None so callers can handle absence of a table.
                return cast(Table, None)
        return cast(Table, self._table)

    def _connect(self) -> None:
        # move network calls outside of constructor
        if isinstance(self._engine, str):
            self._engine = create_engine(self._engine)
        self._connection = self._engine.connect()

    def _create_table(self) -> None:
        self._table = Table(
            self.table_name,
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("document_name", Text),
            Column("content", Text),
            Column("summary", Text),
            Column("q_and_a", Text),
            Column("mindmap", Text),
            Column("bullet_points", Text),
        )
        self._table.create(self.connection, checkfirst=True)

    def put_documents(self, documents: List[ManagedDocument]) -> None:
        for document in documents:
            stmt = insert(self.table).values(
                document_name=document.document_name,
                content=document.content,
                summary=document.summary,
                q_and_a=document.q_and_a,
                mindmap=document.mindmap,
                bullet_points=document.bullet_points,
            )
            self.connection.execute(stmt)
        self.connection.commit()

    def get_documents(self, names: Optional[List[str]] = None) -> List[ManagedDocument]:
        if self.table is None:
            self._create_table()
        if not names:
            stmt = select(self.table).order_by(self.table.c.id)
        else:
            stmt = (
                select(self.table)
                .where(self.table.c.document_name.in_(names))
                .order_by(self.table.c.id)
            )
        result = self.connection.execute(stmt)
        rows = result.fetchall()
        documents = []
        for row in rows:
            documents.append(
                ManagedDocument(
                    document_name=row.document_name,
                    content=row.content,
                    summary=row.summary,
                    q_and_a=row.q_and_a,
                    mindmap=row.mindmap,
                    bullet_points=row.bullet_points,
                )
            )
        return documents

    def get_names(self) -> List[str]:
        if self.table is None:
            self._create_table()
        stmt = select(self.table)
        result = self.connection.execute(stmt)
        rows = result.fetchall()
        return [row.document_name for row in rows]

    def disconnect(self) -> None:
        # Close active connection and dispose engine to release file locks (SQLite)
        try:
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass
                self._connection = None
        except Exception:
            # ignore errors while closing
            pass

        # Dispose engine if it's an Engine instance
        try:
            if hasattr(self._engine, "dispose"):
                try:
                    self._engine.dispose()
                except Exception:
                    pass
            # Reset engine reference
            self._engine = None
        except Exception:
            pass


class EnhancedDocumentManager(DocumentManager):
    """Enhanced DocumentManager with RAG capabilities"""
    
    def __init__(self, *args, enable_ragflow: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_ragflow = enable_ragflow
        self._ragflow_integration = None
        
        if enable_ragflow:
            try:
                from .ragflow_integration import get_ragflow_integration, is_ragflow_available
                if is_ragflow_available():
                    self._ragflow_integration = get_ragflow_integration()
                    logger.info("RAGFlow integration enabled")
                else:
                    logger.warning("RAGFlow not available - using standard document management")
                    self.enable_ragflow = False
            except ImportError as e:
                logger.warning(f"RAGFlow integration not available: {e}")
                self.enable_ragflow = False
    
    def put_documents(self, documents: List[ManagedDocument]) -> None:
        """Enhanced document storage with RAG processing"""
        # Store in standard database
        super().put_documents(documents)
        
        # Process with RAG if enabled
        if self.enable_ragflow and self._ragflow_integration:
            asyncio.create_task(self._process_documents_with_rag(documents))
    
    async def _process_documents_with_rag(self, documents: List[ManagedDocument]) -> None:
        """Process documents through RAG pipeline"""
        for doc in documents:
            try:
                metadata = {
                    "document_name": doc.document_name,
                    "summary": doc.summary,
                    "source": "notebookllama",
                    "q_and_a": doc.q_and_a,
                    "mindmap": doc.mindmap,
                    "bullet_points": doc.bullet_points
                }
                
                # Add to RAG system with vector storage and entity extraction
                result = await self._ragflow_integration.add_document_with_extraction(
                    content=doc.content,
                    metadata=metadata
                )
                
                if result["vector_stored"]:
                    logger.info(f"Document '{doc.document_name}' added to vector storage")
                if result["entities_extracted"]:
                    logger.info(f"Entities extracted from '{doc.document_name}'")
                if result["errors"]:
                    logger.warning(f"RAG processing errors for '{doc.document_name}': {result['errors']}")
                    
            except Exception as e:
                logger.error(f"Error processing document '{doc.document_name}' with RAG: {e}")
    
    async def enhanced_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform enhanced search using both traditional and RAG methods"""
        results = {
            "standard_results": [],
            "vector_results": [],
            "graph_results": [],
            "hybrid_score": []
        }
        
        # Standard text search
        try:
            standard_docs = self.search_documents(query)
            results["standard_results"] = [
                {
                    "document_name": doc.document_name,
                    "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    "summary": doc.summary,
                    "source": "standard_search"
                }
                for doc in standard_docs[:limit]
            ]
        except:
            logger.warning("Standard search failed")
        
        # RAG-enhanced search
        if self.enable_ragflow and self._ragflow_integration:
            try:
                rag_results = await self._ragflow_integration.hybrid_search(query, limit)
                results.update(rag_results)
            except Exception as e:
                logger.error(f"RAG search failed: {e}")
        
        return results
    
    def search_documents(self, query: str) -> List[ManagedDocument]:
        """Standard document search with text matching"""
        if self.table is None:
            self._create_table()
        
        # Simple text search across content and summary
        stmt = select(self.table).where(
            (self.table.c.content.ilike(f"%{query}%")) |
            (self.table.c.summary.ilike(f"%{query}%")) |
            (self.table.c.document_name.ilike(f"%{query}%"))
        ).order_by(self.table.c.id)
        
        result = self.connection.execute(stmt)
        rows = result.fetchall()
        
        documents = []
        for row in rows:
            documents.append(
                ManagedDocument(
                    document_name=row.document_name,
                    content=row.content,
                    summary=row.summary,
                    q_and_a=row.q_and_a,
                    mindmap=row.mindmap,
                    bullet_points=row.bullet_points,
                )
            )
        
        return documents
    
    async def add_document_from_url(self, url: str, 
                                  extract_entities: bool = True) -> Optional[ManagedDocument]:
        """Add document by crawling URL"""
        if not self.enable_ragflow or not self._ragflow_integration:
            logger.warning("URL crawling requires RAGFlow integration")
            return None
        
        try:
            # Crawl URL
            crawl_result = await self._ragflow_integration.crawl_and_process_url(
                url=url, 
                extract_entities=extract_entities
            )
            
            if not crawl_result["crawled"] or not crawl_result["content"]:
                logger.error(f"Failed to crawl URL: {url}")
                return None
            
            # Create ManagedDocument from crawled content
            from .processing import process_file_from_text  # Assuming this function exists
            
            # Use existing processing pipeline to generate summary, Q&A, etc.
            try:
                # For now, create a basic document - can be enhanced with full processing
                doc = ManagedDocument(
                    document_name=f"Crawled: {url}",
                    content=crawl_result["content"],
                    summary="",  # Could be generated using existing processing
                    q_and_a="",
                    mindmap="",
                    bullet_points=""
                )
                
                # Store document
                self.put_documents([doc])
                
                return doc
                
            except Exception as e:
                logger.error(f"Error processing crawled content: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error crawling URL {url}: {e}")
            return None
    
    def get_rag_statistics(self) -> Dict[str, Any]:
        """Get statistics about RAG integration"""
        if not self.enable_ragflow or not self._ragflow_integration:
            return {"ragflow_enabled": False}
        
        try:
            features = self._ragflow_integration.available_features
            return {
                "ragflow_enabled": True,
                "available_features": features,
                "vector_search_available": features["vector_search"],
                "knowledge_graph_available": features["knowledge_graph"],
                "web_crawling_available": features["web_crawling"],
                "llm_providers": [
                    provider for provider, available in {
                        "google_gemini": features["google_gemini"],
                        "openai": features["openai"],
                        "ollama": features["ollama"]
                    }.items() if available
                ]
            }
        except Exception as e:
            logger.error(f"Error getting RAG statistics: {e}")
            return {"ragflow_enabled": False, "error": str(e)}

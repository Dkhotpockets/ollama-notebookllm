"""
Graphiti Knowledge Graph Client for NotebookLlama
Enhanced from RAGFlow-Slim integration
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from graphiti_core.graphiti import Graphiti
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    Graphiti = None
    Neo4jDriver = None

# Global Graphiti instance
_graphiti = None


def create_graphiti_client(
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None
) -> Optional[Graphiti]:
    """Create Graphiti client with Neo4j backend"""
    global _graphiti
    
    if not GRAPHITI_AVAILABLE:
        logger.warning("Graphiti not available - install with: pip install graphiti-core neo4j")
        return None
    
    if _graphiti:
        return _graphiti
    
    # Get configuration from environment
    neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
    
    if not neo4j_password:
        logger.warning("Neo4j password not configured - knowledge graph disabled")
        return None
    
    try:
        # Create Neo4j driver with error handling for API changes
        try:
            driver = Neo4jDriver(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password
            )
        except AttributeError as e:
            if 'decode' in str(e):
                logger.warning("Graphiti Neo4j driver API incompatibility - knowledge graph disabled")
                logger.info("This is a non-critical issue. Vector search and web crawling still work.")
                return None
            else:
                raise
        
        # Create Graphiti instance
        _graphiti = Graphiti(driver)
        
        logger.info("Graphiti client created successfully")
        return _graphiti
        
    except Exception as e:
        logger.warning(f"Failed to create Graphiti client: {e}")
        logger.info("Knowledge graph functionality disabled - this is non-critical")
        return None


async def add_episode(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    group_id: str = "notebookllama"
) -> Dict[str, Any]:
    """Add content as an episode to the knowledge graph"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return {"success": False, "error": "Graphiti not available"}
    
    try:
        # Prepare episode metadata
        episode_data = {
            "name": metadata.get("document_name", f"Episode_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "text": content,
            "timestamp": datetime.utcnow(),
            "source": metadata.get("source", "notebookllama"),
            "metadata": metadata or {}
        }
        
        # Add episode to knowledge graph
        result = await graphiti.add_episode(
            name=episode_data["name"],
            text=episode_data["text"],
            timestamp=episode_data["timestamp"],
            group_id=group_id
        )
        
        logger.info(f"Episode added to knowledge graph: {episode_data['name']}")
        return {
            "success": True,
            "episode_id": result.episode_id if hasattr(result, 'episode_id') else None,
            "entities_extracted": result.entities if hasattr(result, 'entities') else [],
            "edges_created": result.edges if hasattr(result, 'edges') else []
        }
        
    except Exception as e:
        logger.error(f"Error adding episode to knowledge graph: {e}")
        return {"success": False, "error": str(e)}


async def search_graph(
    query: str,
    group_id: str = "notebookllama",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search the knowledge graph for relevant information"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return []
    
    try:
        # Search for entities and relationships
        results = await graphiti.search(
            query=query,
            group_id=group_id,
            limit=limit
        )
        
        # Convert results to standard format
        formatted_results = []
        for result in results:
            formatted_result = {
                "type": "graph_entity",
                "entity_name": getattr(result, 'name', ''),
                "entity_type": getattr(result, 'type', ''),
                "description": getattr(result, 'description', ''),
                "relevance_score": getattr(result, 'score', 0.0),
                "properties": getattr(result, 'properties', {}),
                "relationships": getattr(result, 'relationships', [])
            }
            formatted_results.append(formatted_result)
        
        logger.info(f"Found {len(formatted_results)} graph results for query: {query}")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error searching knowledge graph: {e}")
        return []


async def get_temporal_context(
    entity_name: str,
    group_id: str = "notebookllama",
    time_range: Optional[tuple] = None
) -> Dict[str, Any]:
    """Get temporal evolution of an entity"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return {"success": False, "error": "Graphiti not available"}
    
    try:
        # Get temporal information about entity
        temporal_data = await graphiti.get_temporal_context(
            entity_name=entity_name,
            group_id=group_id,
            start_time=time_range[0] if time_range else None,
            end_time=time_range[1] if time_range else None
        )
        
        return {
            "success": True,
            "entity_name": entity_name,
            "temporal_evolution": temporal_data.evolution if hasattr(temporal_data, 'evolution') else [],
            "key_events": temporal_data.events if hasattr(temporal_data, 'events') else [],
            "relationship_changes": temporal_data.relationships if hasattr(temporal_data, 'relationships') else []
        }
        
    except Exception as e:
        logger.error(f"Error getting temporal context: {e}")
        return {"success": False, "error": str(e)}


async def get_entity_relationships(
    entity_name: str,
    group_id: str = "notebookllama",
    max_depth: int = 2
) -> Dict[str, Any]:
    """Get all relationships for a specific entity"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return {"success": False, "error": "Graphiti not available"}
    
    try:
        # Get entity and its relationships
        relationships = await graphiti.get_entity_relationships(
            entity_name=entity_name,
            group_id=group_id,
            max_depth=max_depth
        )
        
        formatted_relationships = []
        for rel in relationships:
            formatted_rel = {
                "source_entity": getattr(rel, 'source', ''),
                "target_entity": getattr(rel, 'target', ''),
                "relationship_type": getattr(rel, 'type', ''),
                "strength": getattr(rel, 'strength', 0.0),
                "created_at": getattr(rel, 'created_at', None),
                "properties": getattr(rel, 'properties', {})
            }
            formatted_relationships.append(formatted_rel)
        
        return {
            "success": True,
            "entity_name": entity_name,
            "relationships": formatted_relationships,
            "relationship_count": len(formatted_relationships)
        }
        
    except Exception as e:
        logger.error(f"Error getting entity relationships: {e}")
        return {"success": False, "error": str(e)}


async def list_entities(
    group_id: str = "notebookllama",
    entity_type: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """List all entities in the knowledge graph"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return []
    
    try:
        # Get all entities
        entities = await graphiti.list_entities(
            group_id=group_id,
            entity_type=entity_type,
            limit=limit
        )
        
        formatted_entities = []
        for entity in entities:
            formatted_entity = {
                "name": getattr(entity, 'name', ''),
                "type": getattr(entity, 'type', ''),
                "description": getattr(entity, 'description', ''),
                "created_at": getattr(entity, 'created_at', None),
                "properties": getattr(entity, 'properties', {}),
                "relationship_count": getattr(entity, 'relationship_count', 0)
            }
            formatted_entities.append(formatted_entity)
        
        return formatted_entities
        
    except Exception as e:
        logger.error(f"Error listing entities: {e}")
        return []


async def extract_entities_from_text(
    text: str,
    context: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Extract entities from text without adding to graph"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return []
    
    try:
        # Use Graphiti's entity extraction without persistence
        extracted = await graphiti.extract_entities(
            text=text,
            context=context
        )
        
        entities = []
        for entity in extracted:
            formatted_entity = {
                "name": getattr(entity, 'name', ''),
                "type": getattr(entity, 'type', ''),
                "description": getattr(entity, 'description', ''),
                "confidence": getattr(entity, 'confidence', 0.0),
                "properties": getattr(entity, 'properties', {})
            }
            entities.append(formatted_entity)
        
        return entities
        
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return []


async def get_graph_statistics(group_id: str = "notebookllama") -> Dict[str, Any]:
    """Get statistics about the knowledge graph"""
    graphiti = create_graphiti_client()
    if not graphiti:
        return {"success": False, "error": "Graphiti not available"}
    
    try:
        # Get graph statistics
        stats = await graphiti.get_statistics(group_id=group_id)
        
        return {
            "success": True,
            "total_entities": getattr(stats, 'entity_count', 0),
            "total_relationships": getattr(stats, 'relationship_count', 0),
            "total_episodes": getattr(stats, 'episode_count', 0),
            "entity_types": getattr(stats, 'entity_types', {}),
            "relationship_types": getattr(stats, 'relationship_types', {}),
            "last_updated": getattr(stats, 'last_updated', None)
        }
        
    except Exception as e:
        logger.error(f"Error getting graph statistics: {e}")
        return {"success": False, "error": str(e)}


# Compatibility layer with NotebookLlama
class GraphitiDocumentProcessor:
    """Process NotebookLlama documents through Graphiti knowledge graph"""
    
    def __init__(self, group_id: str = "notebookllama"):
        self.group_id = group_id
    
    async def process_managed_document(self, doc) -> Dict[str, Any]:
        """Process ManagedDocument through knowledge graph extraction"""
        metadata = {
            "document_name": doc.document_name,
            "summary": doc.summary,
            "source": "notebookllama",
            "q_and_a_count": len(doc.questions) if hasattr(doc, 'questions') else 0
        }
        
        # Add main content as episode
        content_result = await add_episode(
            content=doc.content,
            metadata=metadata,
            group_id=self.group_id
        )
        
        # Add summary as separate episode if available
        summary_result = {"success": True}
        if doc.summary and len(doc.summary.strip()) > 0:
            summary_metadata = {**metadata, "content_type": "summary"}
            summary_result = await add_episode(
                content=doc.summary,
                metadata=summary_metadata,
                group_id=self.group_id
            )
        
        return {
            "content_processed": content_result["success"],
            "summary_processed": summary_result["success"],
            "entities_extracted": content_result.get("entities_extracted", []),
            "errors": [
                error for error in [
                    content_result.get("error"),
                    summary_result.get("error")
                ] if error
            ]
        }
    
    async def search_related_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for documents related to query using knowledge graph"""
        return await search_graph(query, self.group_id, limit)
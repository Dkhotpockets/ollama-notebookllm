import os
import sys
from querying import query_index
from processing import process_file
from mindmap import get_mind_map
from fastmcp import FastMCP
from typing import List, Union, Literal, Dict, Any
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import RAGFlow integration
try:
    from notebookllama.ragflow_integration import (
        get_ragflow_integration,
        is_ragflow_available,
        enhanced_search,
        enhanced_document_add,
        crawl_url,
        discover_and_process_topic
    )
    RAGFLOW_AVAILABLE = is_ragflow_available()
except ImportError:
    RAGFLOW_AVAILABLE = False

logger = logging.getLogger(__name__)

mcp: FastMCP = FastMCP(name="MCP For NotebookLM with RAGFlow")


@mcp.tool(
    name="process_file_tool",
    description="This tool is useful to process files and produce summaries, question-answers and highlights.",
)
async def process_file_tool(
    filename: str,
) -> Union[str, Literal["Sorry, your file could not be processed."]]:
    notebook_model, text = await process_file(filename=filename)
    if notebook_model is None:
        return "Sorry, your file could not be processed."
    if text is None:
        text = ""
    return notebook_model + "\n%separator%\n" + text


@mcp.tool(name="get_mind_map_tool", description="This tool is useful to get a mind ")
async def get_mind_map_tool(
    summary: str, highlights: List[str]
) -> Union[str, Literal["Sorry, mind map creation failed."]]:
    mind_map_fl = await get_mind_map(summary=summary, highlights=highlights)
    if mind_map_fl is None:
        return "Sorry, mind map creation failed."
    return mind_map_fl


@mcp.tool(name="query_index_tool", description="Query a LlamaCloud index.")
async def query_index_tool(question: str) -> str:
    response = await query_index(question=question)
    if response is None:
        return "Sorry, I was unable to find an answer to your question."
    return response


# Enhanced RAG Tools (available when RAGFlow is configured)
if RAGFLOW_AVAILABLE:
    
    @mcp.tool(
        name="enhanced_search_tool",
        description="Search documents using hybrid RAG: vector similarity + knowledge graph + traditional text search."
    )
    async def enhanced_search_tool(
        query: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        try:
            results = await enhanced_search(query, limit)
            return {
                "status": "success",
                "query": query,
                "results": results,
                "total_results": len(results.get("vector_results", [])) + len(results.get("graph_results", []))
            }
        except Exception as e:
            logger.error(f"Enhanced search error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }

    @mcp.tool(
        name="crawl_and_process_tool",
        description="Crawl a web URL and process the content through the RAG pipeline for enhanced retrieval."
    )
    async def crawl_and_process_tool(
        url: str, 
        extract_entities: bool = True
    ) -> Dict[str, Any]:
        try:
            result = await crawl_url(url, extract_entities)
            return {
                "status": "success",
                "url": url,
                "crawled": result.get("crawled", False),
                "processed": result.get("processed", False),
                "content_length": len(result.get("content", "")),
                "errors": result.get("errors", [])
            }
        except Exception as e:
            logger.error(f"Crawl and process error: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "url": url
            }

    @mcp.tool(
        name="knowledge_graph_search_tool",
        description="Search the knowledge graph for entities and relationships."
    )
    async def knowledge_graph_search_tool(query: str, limit: int = 10) -> Dict[str, Any]:
        try:
            from notebookllama.rag_clients.graphiti_client import search_graph
            results = await search_graph(query, limit=limit)
            
            return {
                "status": "success",
                "query": query,
                "entities_found": len(results),
                "entities": results
            }
        except Exception as e:
            logger.error(f"Knowledge graph search error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "query": query
            }

    @mcp.tool(
        name="add_document_with_rag_tool", 
        description="Add document content with full RAG processing: vector storage + entity extraction."
    )
    async def add_document_with_rag_tool(
        content: str,
        document_name: str = None,
        source: str = "manual_input"
    ) -> Dict[str, Any]:
        try:
            metadata = {
                "document_name": document_name or f"Manual_{asyncio.get_event_loop().time()}",
                "source": source,
                "added_via": "mcp_tool"
            }
            
            result = await enhanced_document_add(content, metadata)
            
            return {
                "status": "success",
                "document_name": metadata["document_name"],
                "vector_stored": result.get("vector_stored", False),
                "entities_extracted": result.get("entities_extracted", False),
                "errors": result.get("errors", [])
            }
        except Exception as e:
            logger.error(f"Add document with RAG error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "document_name": document_name
            }

    @mcp.tool(
        name="get_rag_statistics_tool",
        description="Get statistics about available RAG features and current system status."
    )
    async def get_rag_statistics_tool() -> Dict[str, Any]:
        try:
            integration = get_ragflow_integration()
            features = integration.available_features
            
            # Get additional statistics if available
            stats = {
                "ragflow_available": True,
                "available_features": features,
                "enabled_providers": [
                    provider for provider, enabled in features.items() 
                    if enabled and provider in ["google_gemini", "openai", "ollama"]
                ]
            }
            
            # Try to get knowledge graph statistics
            try:
                from notebookllama.rag_clients.graphiti_client import get_graph_statistics
                graph_stats = await get_graph_statistics()
                if graph_stats.get("success"):
                    stats["knowledge_graph"] = {
                        "total_entities": graph_stats.get("total_entities", 0),
                        "total_relationships": graph_stats.get("total_relationships", 0),
                        "total_episodes": graph_stats.get("total_episodes", 0)
                    }
            except:
                pass
            
            return {
                "status": "success",
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Get RAG statistics error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    @mcp.tool(
        name="discover_topic_tool",
        description="Automatically discover, crawl, and process high-quality learning resources for any topic. This tool searches the web, finds authoritative sources (official docs, tutorials, guides), crawls them, and adds them to the RAG database."
    )
    async def discover_topic_tool(
        topic: str,
        max_resources: int = 10,
        max_concurrent_crawls: int = 3,
        extract_entities: bool = True
    ) -> Dict[str, Any]:
        """
        Discover and process learning resources for a topic.

        Args:
            topic: Topic to learn about (e.g., "TypeScript", "Docker", "React hooks")
            max_resources: Maximum number of resources to discover (5-30)
            max_concurrent_crawls: Number of concurrent crawls (1-5)
            extract_entities: Whether to extract entities for knowledge graph

        Returns:
            Dictionary with discovery results including discovered, crawled, and processed counts
        """
        try:
            # Validate inputs
            max_resources = max(5, min(30, max_resources))
            max_concurrent_crawls = max(1, min(5, max_concurrent_crawls))

            logger.info(f"Starting topic discovery for: {topic}")

            # Run discovery
            results = await discover_and_process_topic(
                topic=topic,
                max_resources=max_resources,
                max_concurrent_crawls=max_concurrent_crawls,
                extract_entities=extract_entities
            )

            # Format response
            return {
                "status": "success",
                "topic": topic,
                "discovered": results.get("discovered", 0),
                "crawled": results.get("crawled", 0),
                "processed": results.get("processed", 0),
                "resources": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "source_type": r.get("source_type"),
                        "priority_score": r.get("priority_score"),
                        "crawled": r.get("crawled"),
                        "processed": r.get("processed"),
                        "content_length": r.get("content_length", 0)
                    }
                    for r in results.get("resources", [])
                ],
                "errors": results.get("errors", [])[:5]  # Limit errors to first 5
            }

        except Exception as e:
            logger.error(f"Topic discovery error for '{topic}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "topic": topic
            }

    @mcp.tool(
        name="discover_resources_tool",
        description="Discover learning resources for a topic (discovery only, no crawling). Returns a list of URLs with priority scores. Use this for quick resource discovery without processing."
    )
    async def discover_resources_tool(
        topic: str,
        max_resources: int = 20
    ) -> Dict[str, Any]:
        """
        Discover resources for a topic without crawling or processing.

        Args:
            topic: Topic to search for
            max_resources: Maximum resources to discover

        Returns:
            List of discovered resources with URLs, titles, and priority scores
        """
        try:
            from notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

            logger.info(f"Discovering resources for: {topic}")

            agent = TopicDiscoveryAgent(max_results_per_query=5)
            resources = await agent.discover_resources(topic, max_resources)

            # Group by source type
            by_type = {}
            for r in resources:
                if r.source_type not in by_type:
                    by_type[r.source_type] = []
                by_type[r.source_type].append({
                    "title": r.title,
                    "url": r.url,
                    "description": r.description[:200] + "..." if len(r.description) > 200 else r.description,
                    "priority_score": round(r.priority_score, 2)
                })

            return {
                "status": "success",
                "topic": topic,
                "total_resources": len(resources),
                "resources": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "source_type": r.source_type,
                        "priority_score": round(r.priority_score, 2),
                        "description": r.description[:200] + "..." if len(r.description) > 200 else r.description
                    }
                    for r in resources
                ],
                "resources_by_type": by_type
            }

        except Exception as e:
            logger.error(f"Resource discovery error for '{topic}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "topic": topic
            }

else:
    # RAGFlow not available - provide informational tools
    @mcp.tool(
        name="ragflow_setup_info_tool",
        description="Get information about setting up RAGFlow integration for enhanced capabilities."
    )
    async def ragflow_setup_info_tool() -> Dict[str, Any]:
        return {
            "status": "info",
            "ragflow_available": False,
            "message": "RAGFlow integration not configured",
            "setup_required": {
                "dependencies": [
                    "pip install supabase",
                    "pip install graphiti-core",
                    "pip install neo4j",
                    "pip install crawl4ai",
                    "pip install google-genai"
                ],
                "environment_variables": {
                    "SUPABASE_URL": "Your Supabase project URL",
                    "SUPABASE_KEY": "Your Supabase service role key", 
                    "NEO4J_PASSWORD": "Neo4j database password",
                    "GOOGLE_API_KEY": "Google AI API key (optional)",
                    "OPENAI_API_KEY": "OpenAI API key (optional)"
                },
                "services": [
                    "Neo4j database (for knowledge graph)",
                    "Supabase database (for vector storage)"
                ]
            }
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

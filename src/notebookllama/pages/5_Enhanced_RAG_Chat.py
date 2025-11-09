"""
Enhanced RAG-Powered Document Chat Interface
Extends the existing Document Chat with RAG capabilities
"""

import streamlit as st
import asyncio
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Import async helper for Streamlit compatibility
from notebookllama.utils.async_streamlit import run_async

# Import existing NotebookLlama components
try:
    from notebookllama.documents import EnhancedDocumentManager
    from notebookllama.ragflow_integration import get_ragflow_integration, is_ragflow_available
    RAGFLOW_AVAILABLE = is_ragflow_available()
except ImportError:
    from notebookllama.documents import DocumentManager as EnhancedDocumentManager
    RAGFLOW_AVAILABLE = False

st.set_page_config(
    page_title="Enhanced Document Chat",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Enhanced Document Chat with RAG")
st.markdown("*Advanced document interaction with vector search, knowledge graph, and web crawling*")

# Initialize session state
if "enhanced_chat_history" not in st.session_state:
    st.session_state.enhanced_chat_history = []

if "enhanced_document_manager" not in st.session_state:
    # Initialize enhanced document manager
    try:
        import os
        db_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/notebookllama")
        st.session_state.enhanced_document_manager = EnhancedDocumentManager(
            engine_url=db_url,
            enable_ragflow=RAGFLOW_AVAILABLE
        )
    except Exception as e:
        st.error(f"Failed to initialize enhanced document manager: {e}")
        st.stop()

# Sidebar for RAG features
with st.sidebar:
    st.header("🔧 RAG Features")
    
    if RAGFLOW_AVAILABLE:
        doc_manager = st.session_state.enhanced_document_manager
        rag_stats = doc_manager.get_rag_statistics()
        
        st.success("✅ RAGFlow Integration Active")
        
        with st.expander("Available Features"):
            for feature, available in rag_stats.get("available_features", {}).items():
                icon = "✅" if available else "❌"
                st.write(f"{icon} {feature.replace('_', ' ').title()}")
        
        if rag_stats.get("llm_providers"):
            st.info(f"LLM Providers: {', '.join(rag_stats['llm_providers'])}")
            
        # Web crawling section
        st.subheader("🌐 Web Crawling")
        url_input = st.text_input(
            "Crawl and add URL to knowledge base:",
            placeholder="https://example.com/article"
        )
        
        if st.button("Crawl URL") and url_input:
            with st.spinner("Crawling and processing URL..."):
                try:
                    result = run_async(
                        doc_manager.add_document_from_url(url_input, extract_entities=True)
                    )
                    
                    if result:
                        st.success(f"Successfully crawled and added: {result.document_name}")
                        st.rerun()
                    else:
                        st.error("Failed to crawl URL")
                except Exception as e:
                    st.error(f"Error crawling URL: {e}")
        
        # Knowledge graph exploration
        st.subheader("🕸️ Knowledge Graph")
        if st.button("Show Graph Statistics"):
            try:
                from notebookllama.rag_clients.graphiti_client import get_graph_statistics
                stats = run_async(get_graph_statistics())
                
                if stats.get("success"):
                    st.metric("Entities", stats.get("total_entities", 0))
                    st.metric("Relationships", stats.get("total_relationships", 0))
                    st.metric("Episodes", stats.get("total_episodes", 0))
                else:
                    st.warning("Could not retrieve graph statistics")
            except Exception as e:
                st.error(f"Error getting graph stats: {e}")
                
    else:
        st.warning("❌ RAGFlow Integration Disabled")
        with st.expander("Setup Instructions"):
            st.markdown("""
            To enable RAGFlow features:
            
            1. **Install dependencies:**
            ```bash
            pip install supabase graphiti-core neo4j crawl4ai google-genai
            ```
            
            2. **Set environment variables:**
            - `SUPABASE_URL`: Your Supabase project URL
            - `SUPABASE_KEY`: Your Supabase service role key
            - `NEO4J_PASSWORD`: Neo4j database password
            - `GOOGLE_API_KEY`: Google AI API key (optional)
            - `OPENAI_API_KEY`: OpenAI API key (optional)
            
            3. **Start services:**
            - Neo4j database for knowledge graph
            - Supabase database for vector storage
            """)

# Main chat interface
st.header("💬 Chat Interface")

# Search mode selection
search_mode = st.selectbox(
    "Search Mode:",
    ["Standard Text Search", "Enhanced RAG Search", "Knowledge Graph Search"],
    index=1 if RAGFLOW_AVAILABLE else 0,
    disabled=not RAGFLOW_AVAILABLE if st.selectbox == "Enhanced RAG Search" else False
)

# Chat input
user_query = st.chat_input("Ask a question about your documents...")

if user_query:
    # Add user message to history
    st.session_state.enhanced_chat_history.append({
        "role": "user",
        "content": user_query,
        "timestamp": pd.Timestamp.now()
    })
    
    # Process query based on search mode
    with st.spinner("Searching and generating response..."):
        try:
            doc_manager = st.session_state.enhanced_document_manager
            
            if search_mode == "Enhanced RAG Search" and RAGFLOW_AVAILABLE:
                # Use enhanced RAG search
                search_results = run_async(doc_manager.enhanced_search(user_query, limit=5))
                
                # Combine results for response generation
                context_parts = []
                
                # Add vector search results
                for result in search_results.get("vector_results", [])[:3]:
                    context_parts.append(f"Vector Match: {result.get('content', '')}")
                
                # Add knowledge graph results
                for result in search_results.get("graph_results", [])[:2]:
                    context_parts.append(f"Entity: {result.get('entity_name', '')} - {result.get('description', '')}")
                
                context = "\n\n".join(context_parts)
                
                # Generate response using available LLM
                try:
                    from notebookllama.rag_clients.llm_provider import generate_text
                    
                    system_prompt = "You are a helpful assistant. Answer questions based on the provided context. If the context doesn't contain enough information, say so clearly."
                    
                    prompt = f"Context:\n{context}\n\nQuestion: {user_query}\n\nAnswer:"
                    
                    response = run_async(generate_text(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=500,
                        temperature=0.7
                    ))
                    
                    # Add assistant response to history
                    st.session_state.enhanced_chat_history.append({
                        "role": "assistant", 
                        "content": response,
                        "timestamp": pd.Timestamp.now(),
                        "search_results": search_results,
                        "search_mode": search_mode
                    })
                    
                except Exception as llm_error:
                    # Fallback to showing search results
                    response = f"Found {len(context_parts)} relevant results. Here's what I found:\n\n{context}"
                    st.session_state.enhanced_chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": pd.Timestamp.now(),
                        "search_results": search_results,
                        "search_mode": search_mode,
                        "note": f"LLM generation failed: {llm_error}"
                    })
            
            elif search_mode == "Knowledge Graph Search" and RAGFLOW_AVAILABLE:
                # Use knowledge graph search only
                from notebookllama.rag_clients.graphiti_client import search_graph
                
                graph_results = run_async(search_graph(user_query, limit=5))
                
                if graph_results:
                    response_parts = [f"Found {len(graph_results)} entities/concepts related to your query:"]
                    
                    for entity in graph_results:
                        name = entity.get("entity_name", "Unknown")
                        desc = entity.get("description", "No description")
                        entity_type = entity.get("entity_type", "Unknown type")
                        response_parts.append(f"• **{name}** ({entity_type}): {desc}")
                    
                    response = "\n".join(response_parts)
                else:
                    response = "No relevant entities found in the knowledge graph."
                
                st.session_state.enhanced_chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": pd.Timestamp.now(),
                    "search_mode": search_mode,
                    "graph_results": graph_results
                })
            
            else:
                # Standard text search
                standard_results = doc_manager.search_documents(user_query)
                
                if standard_results:
                    response_parts = [f"Found {len(standard_results)} documents matching your query:"]
                    
                    for doc in standard_results[:3]:
                        summary = doc.summary if doc.summary else doc.content[:200] + "..."
                        response_parts.append(f"**{doc.document_name}**: {summary}")
                    
                    response = "\n\n".join(response_parts)
                else:
                    response = "No documents found matching your query."
                
                st.session_state.enhanced_chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": pd.Timestamp.now(),
                    "search_mode": search_mode,
                    "standard_results": standard_results
                })
                
        except Exception as e:
            error_response = f"Error processing query: {e}"
            st.session_state.enhanced_chat_history.append({
                "role": "assistant",
                "content": error_response,
                "timestamp": pd.Timestamp.now(),
                "error": True
            })

# Display chat history
for message in st.session_state.enhanced_chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # Show additional information for assistant messages
        if message["role"] == "assistant" and message.get("search_results"):
            with st.expander("🔍 Search Details"):
                results = message["search_results"]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Vector Results")
                    if results.get("vector_results"):
                        for i, result in enumerate(results["vector_results"][:3], 1):
                            st.write(f"{i}. {result.get('document_name', 'Unknown')}")
                            st.write(f"   Similarity: {result.get('similarity', 'N/A')}")
                    else:
                        st.write("No vector results")
                
                with col2:
                    st.subheader("Graph Results")
                    if results.get("graph_results"):
                        for i, result in enumerate(results["graph_results"][:3], 1):
                            st.write(f"{i}. {result.get('entity_name', 'Unknown')}")
                            st.write(f"   Type: {result.get('entity_type', 'N/A')}")
                    else:
                        st.write("No graph results")

# Clear chat button
if st.button("Clear Chat History"):
    st.session_state.enhanced_chat_history = []
    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Enhanced with RAGFlow: Vector search, Knowledge graphs, and Web crawling*")
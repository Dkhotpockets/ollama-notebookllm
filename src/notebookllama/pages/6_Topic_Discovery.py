"""
Topic Discovery - Automatic Learning Resource Discovery and Processing

Automatically discovers, crawls, and processes high-quality learning resources
for any topic you want to learn about.
"""

import streamlit as st
import asyncio
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# Import RAGFlow integration
try:
    from notebookllama.ragflow_integration import (
        get_ragflow_integration,
        is_ragflow_available,
        discover_and_process_topic,
        crawl_url,
    )
    from notebookllama.utils.async_streamlit import run_async
    RAGFLOW_AVAILABLE = is_ragflow_available()
except ImportError as e:
    logger.error(f"Failed to import RAGFlow: {e}")
    RAGFLOW_AVAILABLE = False

st.set_page_config(
    page_title="Subject Discovery",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Automatic Subject Discovery")
st.markdown("*Let AI discover and process learning resources about any subject*")

# Initialize session state
if "discovery_history" not in st.session_state:
    st.session_state.discovery_history = []

if "current_discovery" not in st.session_state:
    st.session_state.current_discovery = None

if "discovery_progress" not in st.session_state:
    st.session_state.discovery_progress = None

if "retry_history" not in st.session_state:
    st.session_state.retry_history = []

# Check if RAGFlow is available
if not RAGFLOW_AVAILABLE:
    st.error("❌ RAGFlow Integration is not available")
    st.markdown("""
    Topic Discovery requires RAGFlow to be configured. Please set up:

    1. **Vector Storage** (at least one):
       - Supabase: `SUPABASE_URL` and `SUPABASE_KEY`
       - PostgreSQL: `PGVECTOR_HOST`, `PGVECTOR_DATABASE`, `PGVECTOR_USER`, `PGVECTOR_PASSWORD`

    2. **Knowledge Graph** (optional but recommended):
       - Neo4j: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

    3. **LLM Provider** (optional):
       - OpenAI: `OPENAI_API_KEY`
       - Google: `GOOGLE_API_KEY`
       - Ollama: Running at `OLLAMA_HOST`

    See the Enhanced RAG Chat page for detailed setup instructions.
    """)
    st.stop()

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Discovery Settings")

    # Get RAG statistics
    try:
        rag = get_ragflow_integration()
        features = rag.available_features

        st.success("✅ RAGFlow Active")

        with st.expander("Available Features"):
            for feature, available in features.items():
                icon = "✅" if available else "❌"
                st.write(f"{icon} {feature.replace('_', ' ').title()}")
    except Exception as e:
        st.warning(f"Could not load RAG features: {e}")

    st.markdown("---")

    max_resources = st.slider(
        "Max resources to discover",
        min_value=5,
        max_value=30,
        value=10,
        help="Maximum number of resources to find and process"
    )

    max_concurrent = st.slider(
        "Concurrent crawls",
        min_value=1,
        max_value=5,
        value=3,
        help="Number of simultaneous web crawls (higher = faster but more resource intensive)"
    )

    extract_entities = st.checkbox(
        "Extract entities",
        value=True,
        help="Extract entities and relationships for knowledge graph (slower but enables advanced search)"
    )

    st.markdown("---")

    if st.button("View Discovery History"):
        st.session_state.show_history = not st.session_state.get("show_history", False)

# Main interface
col1, col2 = st.columns([3, 1])

with col1:
    topic_input = st.text_input(
        "What subject do you want to learn about?",
        placeholder="e.g., TypeScript, machine learning, React hooks, blockchain...",
        help="Enter any technical subject - the system will automatically find and process relevant learning resources"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    discover_button = st.button("🚀 Discover & Learn", type="primary", use_container_width=True)

# Example topics
st.markdown("**Popular subjects:** `Python`, `React`, `Docker`, `Machine Learning`, `Kubernetes`, `TypeScript`, `REST APIs`, `GraphQL`")

# Discovery process
if discover_button and topic_input:
    st.session_state.current_discovery = {
        "topic": topic_input,
        "started_at": datetime.now(),
        "status": "running",
        "results": None
    }

    # Progress tracking
    progress_container = st.container()

    with progress_container:
        st.markdown(f"### 🔍 Discovering resources for: **{topic_input}**")

        status_text = st.empty()
        progress_bar = st.progress(0)
        metrics_cols = st.columns(4)

        discovered_metric = metrics_cols[0].empty()
        crawled_metric = metrics_cols[1].empty()
        processed_metric = metrics_cols[2].empty()
        time_metric = metrics_cols[3].empty()

        # Initialize metrics
        discovered_metric.metric("Discovered", "0")
        crawled_metric.metric("Crawled", "0")
        processed_metric.metric("Processed", "0")
        time_metric.metric("Time", "0s")

        # Progress callback
        progress_data = {"discovered": 0, "crawled": 0, "processed": 0}

        def update_progress(status_dict: Dict[str, Any]):
            """Update UI with progress information"""
            status = status_dict.get("status", "")
            message = status_dict.get("message", "")

            if status == "discovering":
                status_text.info(f"🔎 {message}")
                progress_bar.progress(0.1)

            elif status == "crawling":
                current = status_dict.get("current", 0)
                total = status_dict.get("total", 1)
                progress = 0.1 + (current / total * 0.8)
                progress_bar.progress(min(progress, 0.9))
                status_text.info(f"🌐 {message} ({current}/{total})")

            elif status == "completed":
                progress_bar.progress(1.0)
                status_text.success(f"✅ {message}")
                results = status_dict.get("results", {})
                progress_data.update(results)

        # Execute discovery
        try:
            start_time = datetime.now()

            # Run async discovery with progress callback
            results = run_async(
                discover_and_process_topic(
                    topic=topic_input,
                    max_resources=max_resources,
                    max_concurrent_crawls=max_concurrent,
                    extract_entities=extract_entities
                )
            )

            # Final update
            elapsed = (datetime.now() - start_time).total_seconds()

            discovered_metric.metric("Discovered", results.get("discovered", 0))
            crawled_metric.metric("Crawled", results.get("crawled", 0))
            processed_metric.metric("Processed", results.get("processed", 0))
            time_metric.metric("Time", f"{int(elapsed)}s")

            # Store results
            st.session_state.current_discovery.update({
                "status": "completed",
                "completed_at": datetime.now(),
                "results": results,
                "elapsed_time": elapsed
            })

            # Add to history
            st.session_state.discovery_history.insert(0, st.session_state.current_discovery)

            # Success message
            if results.get("processed", 0) > 0:
                st.success(f"""
                ✅ **Discovery Complete!**

                Successfully processed **{results['processed']}** out of **{results['discovered']}** discovered resources about **{topic_input}**.

                You can now search and chat about this topic using the Enhanced RAG Chat page.
                """)
            else:
                st.warning(f"""
                ⚠️ **Discovery completed but no resources were processed.**

                Found {results.get('discovered', 0)} resources but couldn't process them.
                Check the errors below for details.
                """)

        except Exception as e:
            st.error(f"❌ Error during discovery: {e}")
            logger.error(f"Discovery error for topic '{topic_input}': {e}", exc_info=True)

            st.session_state.current_discovery.update({
                "status": "failed",
                "error": str(e)
            })

# Display current discovery results
if st.session_state.current_discovery and st.session_state.current_discovery.get("status") == "completed":
    results = st.session_state.current_discovery.get("results", {})

    st.markdown("---")
    st.markdown("### 📊 Discovery Results")

    # Resources table
    if results.get("resources"):
        resources_df = pd.DataFrame(results["resources"])

        # Format columns
        if "priority_score" in resources_df.columns:
            resources_df["priority_score"] = resources_df["priority_score"].round(2)

        # Display table
        st.dataframe(
            resources_df[[
                "title", "url", "source_type", "priority_score",
                "crawled", "processed", "content_length"
            ]],
            use_container_width=True,
            hide_index=True
        )

        # Per-resource retry controls for failed resources
        st.markdown("---")
        st.markdown("### 🔧 Retry individual resources")
        for idx, r in resources_df.iterrows():
            processed_flag = bool(r.get("processed")) if "processed" in r.index else False
            if not processed_flag:
                cols = st.columns([6, 1])
                cols[0].markdown(f"**{r.get('title', 'Untitled')}**  \n{r.get('url')}  \n*{r.get('source_type', '')}*")
                btn_key = f"retry_row_{idx}_{hash(r.get('url', ''))}"
                if cols[1].button("Retry", key=btn_key):
                    url_to_retry = r.get('url')
                    st.info(f"Retrying: {url_to_retry}")
                    try:
                        retry_res = run_async(crawl_url(url_to_retry, extract_entities=extract_entities))
                        entry = {
                            "url": url_to_retry,
                            "time": datetime.now().isoformat(),
                            "result": retry_res
                        }
                        st.session_state.retry_history.insert(0, entry)

                        if retry_res.get("processed"):
                            st.success(f"Processed: {url_to_retry}")
                        else:
                            st.warning(f"Still failed: {url_to_retry} — errors: {retry_res.get('errors')}")
                    except Exception as e:
                        st.error(f"Retry error for {url_to_retry}: {e}")

        # Download results
        csv = resources_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"topic_discovery_{topic_input}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # Errors
    if results.get("errors"):
        with st.expander(f"⚠️ Errors ({len(results['errors'])} total)"):
            for i, error in enumerate(results["errors"], 1):
                st.text(f"{i}. {error}")

            # Retry controls for discovery failures
            st.markdown("---")
            col_retry_left, col_retry_right = st.columns([1,1])

            with col_retry_left:
                if st.button("🔁 Retry Discovery"):
                    st.info("Retrying full discovery... this may take a few minutes")
                    try:
                        start_time = datetime.now()
                        results = run_async(
                            discover_and_process_topic(
                                topic=topic_input,
                                max_resources=max_resources,
                                max_concurrent_crawls=max_concurrent,
                                extract_entities=extract_entities
                            )
                        )
                        elapsed = (datetime.now() - start_time).total_seconds()
                        st.success(f"Retry complete — processed {results.get('processed',0)}/{results.get('discovered',0)} resources in {int(elapsed)}s")
                        # Update session state
                        st.session_state.current_discovery.update({
                            "status": "completed",
                            "completed_at": datetime.now(),
                            "results": results,
                            "elapsed_time": elapsed
                        })
                        # Refresh page (Streamlit will reflect changes)
                    except Exception as e:
                        st.error(f"Retry failed: {e}")

            with col_retry_right:
                if st.button("↻ Retry Failed Resources"):
                    # Retry only resources that failed to crawl/process
                    failed_urls = []
                    resources = results.get("resources", [])
                    for r in resources:
                        if not r.get("processed"):
                            failed_urls.append(r.get("url"))

                    if not failed_urls:
                        st.info("No failed resources to retry")
                    else:
                        st.info(f"Retrying {len(failed_urls)} failed resources...")
                        retry_results = []
                        for url in failed_urls:
                            try:
                                res = run_async(crawl_url(url, extract_entities=extract_entities))
                                retry_results.append((url, res))
                                if res.get("processed"):
                                    st.success(f"Processed: {url}")
                                else:
                                    st.warning(f"Still failed: {url} — errors: {res.get('errors')}")
                            except Exception as e:
                                st.error(f"Error retrying {url}: {e}")

                        # Summarize retry
                        processed_count = sum(1 for _, r in retry_results if r.get("processed"))
                        st.info(f"Retry complete — {processed_count}/{len(retry_results)} succeeded")

# Discovery history
if st.session_state.get("show_history") and st.session_state.discovery_history:
    st.markdown("---")
    st.markdown("### 📜 Discovery History")

    for i, discovery in enumerate(st.session_state.discovery_history):
        with st.expander(
            f"**{discovery['topic']}** - {discovery['started_at'].strftime('%Y-%m-%d %H:%M')} "
            f"({discovery.get('results', {}).get('processed', 0)} processed)"
        ):
            results = discovery.get("results", {})

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Discovered", results.get("discovered", 0))
            col2.metric("Crawled", results.get("crawled", 0))
            col3.metric("Processed", results.get("processed", 0))
            col4.metric("Time", f"{int(discovery.get('elapsed_time', 0))}s")

            if results.get("resources"):
                st.write(f"**Top Resources:**")
                for resource in results["resources"][:5]:
                    st.write(f"• [{resource['title']}]({resource['url']}) - {resource['source_type']}")

# Quick start guide
if not st.session_state.get("current_discovery"):
    st.markdown("---")
    st.markdown("""
    ### 🚀 How it works

    1. **Enter a subject** - Any technical subject you want to learn about
    2. **Wait for discovery** - The system searches for high-quality resources (official docs, tutorials, guides)
    3. **Automatic processing** - Content is crawled, processed, and indexed in your RAG database
    4. **Start learning** - Use the Enhanced RAG Chat to ask questions about the topic

    ### 🎯 What gets discovered?

    The system prioritizes:
    - **Official documentation** - From authoritative sources
    - **Tutorial platforms** - W3Schools, freeCodeCamp, MDN, etc.
    - **Educational content** - High-quality guides and courses
    - **GitHub repositories** - With good documentation

    ### 💡 Tips

    - Be specific: "React hooks" is better than "React"
    - Start small: Try 5-10 resources first
    - Check results: Review what was discovered before processing more
    - Use knowledge graph: Enable entity extraction for better search
    """)

# Footer
st.markdown("---")
st.markdown("*Powered by DuckDuckGo search, Crawl4AI web crawling, and RAGFlow processing*")

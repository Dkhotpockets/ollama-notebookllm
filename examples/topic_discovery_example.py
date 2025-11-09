"""
Topic Discovery - Usage Examples

This script demonstrates various ways to use the Topic Discovery feature.
"""

import asyncio
import json


async def example_1_basic_discovery():
    """Example 1: Basic topic discovery (discovery only, no crawling)"""
    print("=" * 60)
    print("Example 1: Basic Discovery")
    print("=" * 60)

    from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

    # Create agent
    agent = TopicDiscoveryAgent(max_results_per_query=5)

    # Discover resources
    topic = "Docker"
    resources = await agent.discover_resources(topic, max_resources=10)

    print(f"\nDiscovered {len(resources)} resources for '{topic}':")
    print("-" * 60)

    # Display top 5
    for i, resource in enumerate(resources[:5], 1):
        print(f"\n{i}. {resource.title}")
        print(f"   URL: {resource.url}")
        print(f"   Type: {resource.source_type}")
        print(f"   Priority: {resource.priority_score:.2f}")

    # Filter by type
    official_docs = agent.get_resources_by_type(resources, "official_docs")
    print(f"\n\nOfficial documentation sources: {len(official_docs)}")
    for doc in official_docs:
        print(f"  - {doc.title}")


async def example_2_full_pipeline():
    """Example 2: Full pipeline (discovery + crawling + RAG processing)"""
    print("\n" + "=" * 60)
    print("Example 2: Full Pipeline (Discovery → Crawl → Process)")
    print("=" * 60)

    from src.notebookllama.ragflow_integration import discover_and_process_topic

    # Define progress callback
    def on_progress(status_dict):
        status = status_dict.get("status", "")
        message = status_dict.get("message", "")

        if status == "discovering":
            print(f"\n🔍 {message}")
        elif status == "crawling":
            current = status_dict.get("current", 0)
            total = status_dict.get("total", 0)
            print(f"🌐 [{current}/{total}] {message}")
        elif status == "completed":
            print(f"\n✅ {message}")

    # Run discovery and processing
    results = await discover_and_process_topic(
        topic="Kubernetes",
        max_resources=5,
        max_concurrent_crawls=2,
        extract_entities=True
    )

    # Display results
    print("\n" + "-" * 60)
    print("Results:")
    print(f"  Discovered: {results['discovered']}")
    print(f"  Crawled:    {results['crawled']}")
    print(f"  Processed:  {results['processed']}")

    if results['errors']:
        print(f"\n⚠️  Errors: {len(results['errors'])}")
        for error in results['errors'][:3]:
            print(f"  - {error}")

    # Show successfully processed resources
    processed = [r for r in results['resources'] if r['processed']]
    print(f"\n✅ Successfully processed {len(processed)} resources:")
    for r in processed:
        print(f"  - {r['title']}")
        print(f"    {r['url']}")
        print(f"    Content length: {r['content_length']} chars")


async def example_3_custom_workflow():
    """Example 3: Custom workflow with manual control"""
    print("\n" + "=" * 60)
    print("Example 3: Custom Workflow")
    print("=" * 60)

    from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent
    from src.notebookllama.ragflow_integration import get_ragflow_integration

    # Step 1: Discover resources
    agent = TopicDiscoveryAgent()
    resources = await agent.discover_resources("GraphQL", max_resources=10)

    print(f"\n1. Discovered {len(resources)} resources")

    # Step 2: Filter to only official docs and educational content
    filtered = [
        r for r in resources
        if r.source_type in ["official_docs", "educational"]
    ]

    print(f"2. Filtered to {len(filtered)} high-quality resources")

    # Step 3: Process selected resources
    rag = get_ragflow_integration()

    processed_count = 0
    for resource in filtered[:3]:  # Process top 3
        print(f"\n3. Processing: {resource.title}")

        result = await rag.crawl_and_process_url(
            url=resource.url,
            extract_entities=True
        )

        if result['processed']:
            processed_count += 1
            print(f"   ✅ Successfully processed")
        else:
            print(f"   ❌ Failed: {result.get('errors', [])}")

    print(f"\n4. Total processed: {processed_count}/{len(filtered[:3])}")


async def example_4_batch_topics():
    """Example 4: Process multiple topics"""
    print("\n" + "=" * 60)
    print("Example 4: Batch Topic Processing")
    print("=" * 60)

    from src.notebookllama.ragflow_integration import discover_and_process_topic

    topics = ["Python", "JavaScript", "Rust"]

    all_results = {}

    for topic in topics:
        print(f"\n📚 Processing topic: {topic}")
        print("-" * 40)

        results = await discover_and_process_topic(
            topic=topic,
            max_resources=5,
            max_concurrent_crawls=2,
            extract_entities=False  # Faster without entities
        )

        all_results[topic] = results

        print(f"   Discovered: {results['discovered']}")
        print(f"   Processed:  {results['processed']}")

    # Summary
    print("\n" + "=" * 60)
    print("Batch Processing Summary:")
    print("=" * 60)

    for topic, results in all_results.items():
        success_rate = (
            results['processed'] / results['discovered'] * 100
            if results['discovered'] > 0 else 0
        )
        print(f"{topic:15s}: {results['processed']}/{results['discovered']} ({success_rate:.0f}%)")


async def example_5_save_results():
    """Example 5: Save discovery results to file"""
    print("\n" + "=" * 60)
    print("Example 5: Save Results to File")
    print("=" * 60)

    from src.notebookllama.ragflow_integration import discover_and_process_topic
    from datetime import datetime

    topic = "FastAPI"

    # Run discovery
    results = await discover_and_process_topic(
        topic=topic,
        max_resources=10,
        max_concurrent_crawls=3
    )

    # Prepare data for export
    export_data = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "discovered": results['discovered'],
            "crawled": results['crawled'],
            "processed": results['processed']
        },
        "resources": results['resources']
    }

    # Save to JSON
    filename = f"topic_discovery_{topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {filename}")
    print(f"   Discovered: {results['discovered']}")
    print(f"   Processed:  {results['processed']}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("TOPIC DISCOVERY - USAGE EXAMPLES")
    print("=" * 60)

    # Uncomment the examples you want to run:

    # Example 1: Basic discovery (fast, no RAG required)
    await example_1_basic_discovery()

    # Example 2: Full pipeline (requires RAG configuration)
    # await example_2_full_pipeline()

    # Example 3: Custom workflow
    # await example_3_custom_workflow()

    # Example 4: Batch processing
    # await example_4_batch_topics()

    # Example 5: Save results
    # await example_5_save_results()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nNote: Some examples require RAGFlow to be configured.")
    print("See TOPIC_DISCOVERY_IMPLEMENTATION.md for setup instructions.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

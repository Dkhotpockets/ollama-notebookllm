"""
End-to-end test of Topic Discovery
Tests the complete flow from discovery to crawling
"""

import asyncio
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_discovery_and_crawl():
    """Test discovery and crawling (no RAG required)"""
    print("=" * 60)
    print("END-TO-END TEST: Discovery + Crawling")
    print("=" * 60)

    # Step 1: Discover resources
    print("\n[Step 1] Discovering resources for 'Docker'...")
    from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

    agent = TopicDiscoveryAgent(max_results_per_query=2)
    resources = await agent.discover_resources("Docker", max_resources=3)

    print(f"✅ Discovered {len(resources)} resources:")
    for i, r in enumerate(resources, 1):
        print(f"   {i}. {r.title[:50]}... (priority: {r.priority_score:.2f})")

    if not resources:
        print("❌ No resources discovered - test failed")
        return False

    # Step 2: Crawl first resource
    print(f"\n[Step 2] Crawling first resource...")
    from src.notebookllama.ragflow_integration import get_ragflow_integration

    rag = get_ragflow_integration()
    url = resources[0].url

    print(f"   URL: {url}")
    result = await rag.crawl_and_process_url(url, extract_entities=False)

    print(f"\n✅ Crawl Results:")
    print(f"   Crawled: {result['crawled']}")
    print(f"   Content Length: {len(result['content'])} chars")

    if not result['crawled']:
        print(f"   ❌ Crawling failed!")
        if result.get('errors'):
            print(f"   Errors: {result['errors']}")
        return False

    if len(result['content']) == 0:
        print(f"   ⚠️  No content extracted")
        return False

    # Show preview
    print(f"\n📄 Content Preview (first 300 chars):")
    print("-" * 60)
    print(result['content'][:300])
    print("-" * 60)

    # Step 3: Verify multiple resources
    print(f"\n[Step 3] Testing multiple resources...")

    success_count = 0
    for i, resource in enumerate(resources[:3], 1):
        print(f"\n   [{i}/3] Testing: {resource.title[:40]}...")
        result = await rag.crawl_and_process_url(resource.url, extract_entities=False)

        if result['crawled'] and len(result['content']) > 0:
            print(f"        ✅ Success ({len(result['content'])} chars)")
            success_count += 1
        else:
            print(f"        ❌ Failed")

    print(f"\n✅ Successfully crawled {success_count}/{len(resources[:3])} resources")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Discovery: Working ({len(resources)} resources found)")
    print(f"✅ Crawling: Working ({success_count}/{len(resources[:3])} successful)")
    print(f"✅ Content Extraction: Working")
    print("\n🎉 END-TO-END TEST PASSED!")
    print("=" * 60)

    return True


async def test_with_streamlit_data():
    """Simulate what happens in Streamlit UI"""
    print("\n" + "=" * 60)
    print("STREAMLIT UI SIMULATION")
    print("=" * 60)

    print("\n👤 User enters topic: 'Python'")
    print("👤 User sets max_resources: 5")
    print("👤 User clicks 'Discover & Learn'")

    print("\n🔄 Processing...")

    from src.notebookllama.ragflow_integration import discover_and_process_topic

    # Simulate progress callback
    progress_updates = []

    def track_progress(status_dict):
        progress_updates.append(status_dict)
        status = status_dict.get('status', '')
        message = status_dict.get('message', '')

        if status == 'discovering':
            print(f"   🔍 {message}")
        elif status == 'crawling':
            current = status_dict.get('current', 0)
            total = status_dict.get('total', 0)
            print(f"   🌐 [{current}/{total}] {message}")
        elif status == 'completed':
            print(f"   ✅ {message}")

    # Note: progress_callback not implemented in current version
    # This simulates what the UI would show

    results = await discover_and_process_topic(
        topic="Python",
        max_resources=5,
        max_concurrent_crawls=2,
        extract_entities=False  # Faster without entities
    )

    print("\n📊 Results:")
    print(f"   Discovered: {results.get('discovered', 0)} resources")
    print(f"   Crawled: {results.get('crawled', 0)} resources")
    print(f"   Processed: {results.get('processed', 0)} resources")

    if results.get('errors'):
        print(f"\n⚠️  Errors encountered: {len(results['errors'])}")
        for error in results['errors'][:3]:
            print(f"   - {error}")

    # Show successful resources
    successful = [r for r in results.get('resources', []) if r.get('crawled')]
    print(f"\n✅ Successfully crawled resources:")
    for r in successful:
        print(f"   • {r['title'][:50]}...")
        print(f"     {r['url']}")
        print(f"     Content: {r.get('content_length', 0)} chars")

    print("\n" + "=" * 60)
    if results.get('crawled', 0) > 0:
        print("✅ STREAMLIT SIMULATION PASSED")
        print("   Users can now discover and crawl content!")
    else:
        print("❌ STREAMLIT SIMULATION FAILED")
        print("   Check errors above")
    print("=" * 60)

    return results.get('crawled', 0) > 0


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TOPIC DISCOVERY - END-TO-END TESTS")
    print("=" * 60)
    print("\nThese tests verify the complete system works")
    print("from discovery → crawling → content extraction")
    print("\nNote: RAG processing (vector storage, knowledge graph)")
    print("is optional and not tested here.")
    print("=" * 60)

    # Test 1: Basic discovery and crawl
    test1_passed = await test_discovery_and_crawl()

    # Test 2: Streamlit simulation
    test2_passed = await test_with_streamlit_data()

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    print(f"{'✅ PASS' if test1_passed else '❌ FAIL'}: Discovery + Crawling Test")
    print(f"{'✅ PASS' if test2_passed else '❌ FAIL'}: Streamlit UI Simulation")

    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYou can now:")
        print("1. Run: streamlit run src/notebookllama/Home.py")
        print("2. Navigate to 'Topic Discovery'")
        print("3. Enter any topic and click 'Discover & Learn'")
        print("4. Resources will be discovered AND crawled! ✅")
    else:
        print("\n⚠️  Some tests failed")
        print("Please check the errors above")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

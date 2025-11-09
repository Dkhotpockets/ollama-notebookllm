"""
Simple test script for Topic Discovery functionality
"""

import asyncio
import logging
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_topic_discovery():
    """Test the TopicDiscoveryAgent"""
    print("=" * 60)
    print("Testing Topic Discovery Agent")
    print("=" * 60)

    try:
        from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

        # Create agent
        agent = TopicDiscoveryAgent(max_results_per_query=5)
        print("\n✅ TopicDiscoveryAgent initialized successfully")

        # Test discovery with a simple topic
        test_topic = "TypeScript"
        print(f"\n🔍 Discovering resources for: {test_topic}")
        print("-" * 60)

        resources = await agent.discover_resources(test_topic, max_resources=5)

        print(f"\n✅ Discovered {len(resources)} resources")
        print("-" * 60)

        # Display results
        for i, resource in enumerate(resources, 1):
            print(f"\n{i}. {resource.title}")
            print(f"   URL: {resource.url}")
            print(f"   Type: {resource.source_type}")
            print(f"   Priority: {resource.priority_score:.2f}")
            print(f"   Description: {resource.description[:100]}...")

        print("\n" + "=" * 60)
        print("✅ Topic Discovery Test PASSED")
        print("=" * 60)

        return True

    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ragflow_integration():
    """Test RAGFlow integration (basic check only)"""
    print("\n" + "=" * 60)
    print("Testing RAGFlow Integration")
    print("=" * 60)

    try:
        from src.notebookllama.ragflow_integration import get_ragflow_integration

        rag = get_ragflow_integration()
        print("\n✅ RAGFlowIntegration initialized")

        # Check available features
        features = rag.available_features
        print("\n📊 Available Features:")
        for feature, available in features.items():
            status = "✅" if available else "❌"
            print(f"   {status} {feature.replace('_', ' ').title()}")

        # Check if topic discovery method exists
        if hasattr(rag, 'discover_and_process_topic'):
            print("\n✅ discover_and_process_topic method exists")
        else:
            print("\n❌ discover_and_process_topic method NOT found")
            return False

        print("\n" + "=" * 60)
        print("✅ RAGFlow Integration Test PASSED")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TOPIC DISCOVERY SYSTEM - TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Topic Discovery Agent
    result1 = await test_topic_discovery()
    results.append(("Topic Discovery Agent", result1))

    # Test 2: RAGFlow Integration
    result2 = await test_ragflow_integration()
    results.append(("RAGFlow Integration", result2))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nYou can now:")
        print("1. Run 'streamlit run src/notebookllama/Home.py' to start the app")
        print("2. Navigate to the 'Topic Discovery' page (6_Topic_Discovery)")
        print("3. Enter a topic and let the system discover resources")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please check the error messages above")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

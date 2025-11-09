"""
Debug script to test DuckDuckGo search functionality
"""

import asyncio
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_basic_search():
    """Test basic DuckDuckGo search"""
    print("=" * 60)
    print("Testing DuckDuckGo Search")
    print("=" * 60)

    try:
        from ddgs import DDGS
        print("\n✅ DDGS imported successfully")
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            print("\n✅ duckduckgo_search imported successfully")
        except ImportError:
            print("\n❌ Could not import DDGS")
            print("Please install: pip install ddgs")
            return False

    # Test 1: Simple synchronous search
    print("\n" + "-" * 60)
    print("Test 1: Basic synchronous search")
    print("-" * 60)

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text("Python programming", max_results=3))

        print(f"✅ Found {len(results)} results")

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('title', 'No title')}")
            print(f"   URL: {result.get('href', 'No URL')}")
            print(f"   Snippet: {result.get('body', 'No description')[:100]}...")

        if len(results) == 0:
            print("⚠️  Search returned 0 results")
            return False

    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Async search using thread pool
    print("\n" + "-" * 60)
    print("Test 2: Async search (thread pool)")
    print("-" * 60)

    try:
        def search():
            with DDGS() as ddgs:
                return list(ddgs.text("TypeScript tutorial", max_results=3))

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, search)

        print(f"✅ Found {len(results)} results (async)")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('title', 'No title')}")

    except Exception as e:
        print(f"❌ Async search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3: Multiple queries
    print("\n" + "-" * 60)
    print("Test 3: Multiple search queries")
    print("-" * 60)

    queries = [
        "Docker containers tutorial",
        "React hooks official documentation",
        "Kubernetes getting started"
    ]

    for query in queries:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=2))
            print(f"✅ '{query}': {len(results)} results")
        except Exception as e:
            print(f"❌ '{query}': {e}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    return True


async def test_topic_discovery_agent():
    """Test the actual TopicDiscoveryAgent"""
    print("\n" + "=" * 60)
    print("Testing TopicDiscoveryAgent")
    print("=" * 60)

    try:
        from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

        agent = TopicDiscoveryAgent(max_results_per_query=3)
        print("\n✅ TopicDiscoveryAgent initialized")

        # Test discovery
        topic = "Python"
        print(f"\n🔍 Discovering resources for: {topic}")
        print("-" * 60)

        resources = await agent.discover_resources(topic, max_resources=5)

        print(f"\n✅ Discovered {len(resources)} resources")

        if len(resources) == 0:
            print("\n⚠️  WARNING: No resources discovered!")
            print("\nPossible causes:")
            print("1. Network connectivity issues")
            print("2. DuckDuckGo blocking requests")
            print("3. Search API changes")
            print("4. Firewall or proxy blocking")
            return False

        for i, resource in enumerate(resources, 1):
            print(f"\n{i}. {resource.title}")
            print(f"   URL: {resource.url}")
            print(f"   Type: {resource.source_type}")
            print(f"   Priority: {resource.priority_score:.2f}")

        return True

    except Exception as e:
        print(f"\n❌ TopicDiscoveryAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_network_connectivity():
    """Test network connectivity"""
    print("\n" + "=" * 60)
    print("Testing Network Connectivity")
    print("=" * 60)

    import urllib.request
    import socket

    # Test 1: DNS resolution
    print("\nTest 1: DNS Resolution")
    try:
        ip = socket.gethostbyname("duckduckgo.com")
        print(f"✅ duckduckgo.com resolves to: {ip}")
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

    # Test 2: HTTP connection
    print("\nTest 2: HTTP Connection")
    try:
        req = urllib.request.Request(
            "https://duckduckgo.com/",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req, timeout=10)
        print(f"✅ HTTP connection successful: {response.status}")
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
        return False

    print("\n✅ Network connectivity OK")
    return True


async def main():
    """Run all debug tests"""
    print("\n" + "=" * 60)
    print("TOPIC DISCOVERY - DEBUG DIAGNOSTICS")
    print("=" * 60)

    results = []

    # Test 1: Network connectivity
    print("\n[1/3] Testing network connectivity...")
    network_ok = await test_network_connectivity()
    results.append(("Network Connectivity", network_ok))

    if not network_ok:
        print("\n⚠️  Network connectivity issues detected!")
        print("Please check your internet connection and firewall settings.")
        return

    # Test 2: Basic DuckDuckGo search
    print("\n[2/3] Testing DuckDuckGo search...")
    search_ok = await test_basic_search()
    results.append(("DuckDuckGo Search", search_ok))

    if not search_ok:
        print("\n⚠️  DuckDuckGo search is not working!")
        print("\nTroubleshooting steps:")
        print("1. Try reinstalling: pip uninstall ddgs && pip install ddgs")
        print("2. Check if DuckDuckGo is accessible in your region")
        print("3. Try using a VPN if DuckDuckGo is blocked")
        return

    # Test 3: TopicDiscoveryAgent
    print("\n[3/3] Testing TopicDiscoveryAgent...")
    agent_ok = await test_topic_discovery_agent()
    results.append(("TopicDiscoveryAgent", agent_ok))

    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 All diagnostics passed!")
        print("\nThe Topic Discovery system should be working correctly.")
        print("If you're still seeing 'no resources found', please share:")
        print("1. The exact topic you're searching for")
        print("2. Any error messages you see")
        print("3. Screenshots of the issue")
    else:
        print("\n⚠️  Some diagnostics failed")
        print("Please address the issues above and try again.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

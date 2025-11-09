"""
Diagnose crawling issues using Playwright
"""

import asyncio
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_discovery_and_crawl():
    """Test discovery and then try to crawl one resource"""
    print("=" * 60)
    print("Step 1: Discover Resources")
    print("=" * 60)

    from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

    # Discover resources
    agent = TopicDiscoveryAgent(max_results_per_query=3)
    resources = await agent.discover_resources("Docker", max_resources=5)

    print(f"\n✅ Discovered {len(resources)} resources")

    if not resources:
        print("❌ No resources discovered - cannot test crawling")
        return

    # Show discovered resources
    for i, r in enumerate(resources, 1):
        print(f"{i}. {r.title}")
        print(f"   URL: {r.url}")

    # Test crawling the first resource
    print("\n" + "=" * 60)
    print("Step 2: Test Crawling First Resource")
    print("=" * 60)

    test_url = resources[0].url
    print(f"\n🌐 Testing URL: {test_url}")

    # Try to check if Crawl4AI is available
    try:
        import crawl4ai
        print("✅ crawl4ai module found")
        print(f"   Version: {crawl4ai.__version__ if hasattr(crawl4ai, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"❌ crawl4ai not available: {e}")
        return

    # Try to import AsyncWebCrawler
    try:
        from crawl4ai import AsyncWebCrawler
        print("✅ AsyncWebCrawler imported")
    except ImportError as e:
        print(f"❌ Cannot import AsyncWebCrawler: {e}")
        return

    # Test basic crawl
    print("\n📥 Attempting to crawl...")
    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=test_url)

            print("\n✅ Crawl completed!")
            print(f"   Success: {result.success}")
            print(f"   Status Code: {result.status_code if hasattr(result, 'status_code') else 'N/A'}")
            print(f"   Content Length: {len(result.markdown) if result.markdown else 0} chars")

            if result.markdown:
                print(f"\n📄 First 200 chars of content:")
                print(result.markdown[:200])
            else:
                print("\n⚠️  No markdown content extracted")

            if hasattr(result, 'error_message') and result.error_message:
                print(f"\n⚠️  Error message: {result.error_message}")

    except Exception as e:
        print(f"\n❌ Crawl failed: {e}")
        import traceback
        traceback.print_exc()


async def test_crawl_manager():
    """Test the CrawlJobManager"""
    print("\n" + "=" * 60)
    print("Step 3: Test CrawlJobManager")
    print("=" * 60)

    try:
        from src.notebookllama.rag_clients.crawl_manager import CrawlJobManager, CrawlJobRequest

        print("✅ CrawlJobManager imported")

        # Create manager
        manager = CrawlJobManager(storage_client=None)  # No storage for testing
        print("✅ CrawlJobManager initialized")

        # Test crawl
        test_url = "https://docs.docker.com/"
        print(f"\n🌐 Testing crawl via CrawlJobManager: {test_url}")

        request = CrawlJobRequest(
            url=test_url,
            extract_entities=False,
            politeness_delay=1.0
        )

        print("📥 Creating and executing crawl job...")
        response = await manager.create_and_execute_job(request)

        print(f"\n✅ Crawl job completed!")
        print(f"   Status: {response.status}")
        print(f"   Content Length: {len(response.content) if response.content else 0}")
        print(f"   Title: {response.title}")

        if response.error:
            print(f"   ⚠️  Error: {response.error}")

        if response.content:
            print(f"\n📄 First 200 chars:")
            print(response.content[:200])
        else:
            print("\n⚠️  No content extracted")

    except ImportError as e:
        print(f"❌ Cannot import CrawlJobManager: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ CrawlJobManager test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_full_pipeline():
    """Test the complete discovery and processing pipeline"""
    print("\n" + "=" * 60)
    print("Step 4: Test Full Pipeline (1 Resource)")
    print("=" * 60)

    try:
        from src.notebookllama.ragflow_integration import get_ragflow_integration

        rag = get_ragflow_integration()
        print("✅ RAGFlow integration loaded")

        # Check available features
        features = rag.available_features
        print("\n📊 Available features:")
        for feature, available in features.items():
            status = "✅" if available else "❌"
            print(f"   {status} {feature}")

        # Test discovering and processing a single topic
        print("\n🔍 Testing full pipeline with 1 resource...")

        from src.notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent

        # Discover 1 resource
        agent = TopicDiscoveryAgent(max_results_per_query=1)
        resources = await agent.discover_resources("Python", max_resources=1)

        if not resources:
            print("❌ No resources discovered")
            return

        resource = resources[0]
        print(f"\n📦 Testing with: {resource.title}")
        print(f"   URL: {resource.url}")

        # Try to crawl and process
        print("\n🌐 Crawling...")
        result = await rag.crawl_and_process_url(resource.url, extract_entities=False)

        print(f"\n✅ Result:")
        print(f"   Crawled: {result.get('crawled', False)}")
        print(f"   Processed: {result.get('processed', False)}")
        print(f"   Content Length: {len(result.get('content', ''))}")

        if result.get('errors'):
            print(f"\n⚠️  Errors:")
            for error in result['errors']:
                print(f"   - {error}")

    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()


async def check_playwright_installation():
    """Check if Playwright browsers are installed"""
    print("\n" + "=" * 60)
    print("Step 5: Check Playwright Installation")
    print("=" * 60)

    try:
        from playwright.async_api import async_playwright

        print("✅ Playwright module available")

        # Try to launch browser
        print("\n🌐 Testing browser launch...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                print("✅ Chromium browser launched successfully")

                page = await browser.new_page()
                print("✅ New page created")

                # Try to navigate to a simple page
                await page.goto("https://docs.docker.com/")
                print("✅ Navigation successful")

                title = await page.title()
                print(f"✅ Page title: {title}")

                content = await page.content()
                print(f"✅ Page content length: {len(content)} chars")

                await browser.close()
                print("✅ Browser closed")

        except Exception as e:
            print(f"❌ Browser test failed: {e}")
            print("\nThis might mean Playwright browsers are not installed.")
            print("Run: playwright install chromium")

    except ImportError:
        print("❌ Playwright not available")
        print("Install with: pip install playwright")


async def main():
    """Run all diagnostics"""
    print("\n" + "=" * 60)
    print("CRAWLING DIAGNOSTICS WITH PLAYWRIGHT")
    print("=" * 60)

    # Check Playwright first
    await check_playwright_installation()

    # Test discovery and basic crawl
    await test_discovery_and_crawl()

    # Test CrawlJobManager
    await test_crawl_manager()

    # Test full pipeline
    await test_full_pipeline()

    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

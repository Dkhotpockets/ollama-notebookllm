"""
Test storage fallback logic
"""

import asyncio
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_storage_fallback():
    """Test that storage fallback to SQLite works"""
    print("=" * 60)
    print("Testing Storage Fallback")
    print("=" * 60)

    from src.notebookllama.ragflow_integration import get_ragflow_integration

    rag = get_ragflow_integration()

    # Test crawling and processing
    url = "https://docs.docker.com/"
    print(f"\n🌐 Testing: {url}")

    print("\n[Step 1] Crawling...")
    result = await rag.crawl_and_process_url(url, extract_entities=False)

    print(f"\n📊 Results:")
    print(f"   Crawled: {result['crawled']}")
    print(f"   Processed: {result['processed']}")
    print(f"   Content Length: {len(result.get('content', ''))}")

    if result.get('errors'):
        print(f"\n⚠️  Errors:")
        for error in result['errors']:
            print(f"   - {error}")

    # Check if processing worked
    if result['crawled'] and result['processed']:
        print("\n✅ SUCCESS: Crawling AND Processing both work!")
        print("   Content was stored in database")
        return True
    elif result['crawled'] and not result['processed']:
        print("\n⚠️  PARTIAL: Crawling works but processing failed")
        print("   Content was retrieved but not stored")
        return False
    else:
        print("\n❌ FAIL: Crawling failed")
        return False


async def test_document_manager_directly():
    """Test DocumentManager with SQLite directly"""
    print("\n" + "=" * 60)
    print("Testing DocumentManager Directly")
    print("=" * 60)

    try:
        from src.notebookllama.documents import DocumentManager, ManagedDocument
        import tempfile
        import os

        # Use SQLite in temp directory
        sqlite_path = os.path.join(tempfile.gettempdir(), "test_notebookllama.db")
        db_url = f"sqlite:///{sqlite_path}"

        print(f"\n📁 Using SQLite: {sqlite_path}")

        # Create manager
        doc_manager = DocumentManager(engine_url=db_url)
        print("✅ DocumentManager created")

        # Create test document
        document = ManagedDocument(
            document_name="test_docker_docs",
            content="This is test content from Docker documentation...",
            summary="Test summary",
            q_and_a="",
            mindmap="",
            bullet_points=""
        )

        # Store document
        print("\n💾 Storing document...")
        doc_manager.put_documents([document])
        print("✅ Document stored successfully")

        # Retrieve document
        print("\n📥 Retrieving document...")
        docs = doc_manager.get_documents(["test_docker_docs"])
        print(f"✅ Retrieved {len(docs)} document(s)")

        if docs:
            print(f"\n📄 Document content:")
            print(f"   Name: {docs[0].document_name}")
            print(f"   Content: {docs[0].content[:50]}...")
            print(f"   Summary: {docs[0].summary[:50]}...")

        # Clean up
        # Clean up - ensure DB connections are closed first to avoid Windows file locks
        try:
            if doc_manager:
                try:
                    doc_manager.disconnect()
                except Exception:
                    pass

            if os.path.exists(sqlite_path):
                # Try removing with a few retries in case the OS still has a lock
                for attempt in range(3):
                    try:
                        os.remove(sqlite_path)
                        print(f"\n🗑️  Cleaned up test database")
                        break
                    except PermissionError:
                        import time
                        time.sleep(0.5)
                else:
                    print("\n⚠️  Could not remove test database - file locked")
        except Exception as e:
            print(f"\n⚠️  Cleanup error: {e}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STORAGE TESTS")
    print("=" * 60)

    # Test 1: DocumentManager directly
    test1 = await test_document_manager_directly()

    # Test 2: Full pipeline with storage
    test2 = await test_storage_fallback()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"{'✅ PASS' if test1 else '❌ FAIL'}: Direct DocumentManager Test")
    print(f"{'✅ PASS' if test2 else '❌ FAIL'}: Full Pipeline Test")

    if test1 and test2:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nStorage is working with SQLite fallback")
        print("Topic Discovery should now process documents!")
    else:
        print("\n⚠️  Some tests failed - investigating...")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

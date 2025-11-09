#!/usr/bin/env python3
"""
Bootstrap learning topic - automatically find and ingest content

Usage: python scripts/bootstrap_topic.py "typescript basics"
"""

import sys
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def bootstrap_topic(topic: str):
    """Find and ingest content for a learning topic"""
    
    print(f"🔍 Bootstrapping topic: {topic}")
    print("=" * 60)
    
    # Common learning sources by topic
    topic_urls = {
        "typescript": [
            "https://www.typescriptlang.org/docs/handbook/intro.html",
            "https://www.typescriptlang.org/docs/handbook/2/basic-types.html",
            "https://www.typescriptlang.org/docs/handbook/2/everyday-types.html",
            "https://www.typescriptlang.org/docs/handbook/2/narrowing.html",
            "https://www.typescriptlang.org/docs/handbook/2/functions.html",
        ],
        "python": [
            "https://docs.python.org/3/tutorial/index.html",
            "https://docs.python.org/3/tutorial/introduction.html",
            "https://docs.python.org/3/tutorial/controlflow.html",
        ],
        "javascript": [
            "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
            "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps",
        ],
        "react": [
            "https://react.dev/learn",
            "https://react.dev/learn/thinking-in-react",
        ]
    }
    
    # Find matching URLs
    urls = []
    topic_lower = topic.lower()
    for key, url_list in topic_urls.items():
        if key in topic_lower:
            urls = url_list
            break
    
    if not urls:
        print(f"⚠️  No predefined URLs for '{topic}'")
        print("Please provide URLs manually or add them to the script")
        return
    
    print(f"\n📚 Found {len(urls)} URLs for {topic}:")
    for url in urls:
        print(f"  • {url}")
    
    # Import RAG components
    try:
        from src.notebookllama.documents import EnhancedDocumentManager
        
        manager = EnhancedDocumentManager()
        
        print("\n🌐 Starting to crawl and process URLs...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            try:
                result = await manager.crawl_and_add_url(
                    url=url,
                    extract_entities=True
                )
                
                if result:
                    print(f"  ✅ Success - Document ID: {result.get('id')}")
                else:
                    print(f"  ❌ Failed to process")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Bootstrap complete!")
        print("\nYou can now:")
        print("  1. Open http://localhost:8501")
        print("  2. Go to 'Enhanced RAG Chat'")
        print(f"  3. Ask questions about {topic}")
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nMake sure:")
        print("  1. Docker services are running")
        print("  2. Environment variables are set in .env")
        print("  3. Run: python scripts/setup_local_network.py")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/bootstrap_topic.py 'topic name'")
        print("\nExamples:")
        print("  python scripts/bootstrap_topic.py typescript")
        print("  python scripts/bootstrap_topic.py 'python basics'")
        print("  python scripts/bootstrap_topic.py javascript")
        sys.exit(1)
    
    topic = " ".join(sys.argv[1:])
    asyncio.run(bootstrap_topic(topic))

#!/usr/bin/env python3
"""
Simple script to discover and store TypeScript learning materials
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def learn_typescript():
    """Discover and store TypeScript learning resources"""
    print("🎓 TypeScript Learning Assistant")
    print("=" * 60)
    
    try:
        from notebookllama.ragflow_integration import RAGFlowIntegration
        
        # Initialize RAGFlow
        print("\n1️⃣  Initializing RAGFlow integration...")
        rag = RAGFlowIntegration()
        
        features = rag.available_features
        print(f"   ✅ Vector search: {features.get('vector_search', False)}")
        print(f"   ✅ Web crawling: {features.get('web_crawling', False)}")
        print(f"   ✅ Supabase storage: {features.get('supabase_vector', False)}")
        
        # Discover TypeScript resources
        print("\n2️⃣  Discovering TypeScript learning resources...")
        from notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent
        
        agent = TopicDiscoveryAgent()
        resources = await agent.discover_resources("typescript", max_resources=3)
        
        print(f"   ✅ Found {len(resources)} resources")
        for i, res in enumerate(resources, 1):
            title = getattr(res, 'title', 'Untitled')
            url = getattr(res, 'url', 'no url')
            print(f"      {i}. {title} ({url})")
        
        # Crawl and store each resource
        print("\n3️⃣  Crawling and storing content...")
        
        from notebookllama.rag_clients.crawl_manager import CrawlJobManager, CrawlJobRequest
        from supabase import create_client
        
        # Initialize crawl manager
        url_env = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url_env, key)
        
        crawl_manager = CrawlJobManager(storage_client=supabase)
        
        documents_stored = 0
        
        for i, resource in enumerate(resources, 1):
            url = getattr(resource, 'url', None)
            title = getattr(resource, 'title', 'Untitled')
            
            if not url:
                continue
            
            print(f"\n   📄 {i}. Crawling: {title[:50]}...")
            
            try:
                # Create crawl request (title goes in metadata)
                request = CrawlJobRequest(url=url, metadata={"title": title})
                
                # Execute crawl
                job = await crawl_manager.create_and_execute_job(request)
                
                if job.status.value == "completed" and job.content:
                    print(f"      ✅ Crawled {len(job.content)} characters")
                    
                    # Store in Supabase
                    from notebookllama.rag_clients.supabase_client import add_document_to_supabase
                    
                    success = await add_document_to_supabase(
                        supabase,
                        content=job.content,
                        metadata={
                            "url": url,
                            "content_type": "text/html",
                            "topic": "typescript",
                            "crawled_at": job.completed_at
                        },
                        title=title
                    )
                    
                    if success:
                        documents_stored += 1
                        print(f"      ✅ Stored in database")
                    else:
                        print(f"      ⚠️  Failed to store")
                else:
                    print(f"      ⚠️  Crawl failed: {job.error or 'Unknown error'}")
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎉 Complete! Stored {documents_stored} documents")
        print("\n📝 Next steps:")
        print("   • Query your documents in Supabase dashboard")
        print("   • Use Page 5 (Enhanced RAG Chat) in Streamlit to ask questions")
        print("   • Example: 'What are TypeScript interfaces?'")
        
        return documents_stored
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    result = asyncio.run(learn_typescript())
    exit(0 if result > 0 else 1)
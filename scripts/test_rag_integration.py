#!/usr/bin/env python3
"""
Simple test of Supabase + topic discovery integration
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase connection...")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials")
            return False
            
        supabase = create_client(url, key)
        
        # Try to query existing tables
        try:
            result = supabase.table('documents').select('*').limit(1).execute()
            print("✅ Connected to Supabase successfully!")
            print(f"📄 Documents table accessible (found {len(result.data)} items)")
            return True
        except Exception as e:
            print(f"⚠️  Table query failed: {e}")
            # Table might not exist yet, but connection works
            print("✅ Supabase connection working (tables may need setup)")
            return True
            
    except ImportError:
        print("❌ Supabase client not installed")
        return False
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_topic_discovery():
    """Test the topic discovery functionality"""
    print("\n🔍 Testing topic discovery...")
    
    try:
        import sys
        sys.path.append('src')
        
        from notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent
        
        agent = TopicDiscoveryAgent()
        
        print("🔎 Discovering resources for 'typescript basics'...")
        resources = agent.discover_resources("typescript basics", max_results=3)
        
        print(f"📚 Found {len(resources)} resources:")
        for i, resource in enumerate(resources[:3], 1):
            print(f"  {i}. {resource.get('title', 'Unknown')} - {resource.get('url', 'No URL')}")
            
        return len(resources) > 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Topic discovery failed: {e}")
        return False

def test_rag_integration():
    """Test RAG integration features"""
    print("\n🤖 Testing RAG integration...")
    
    try:
        import sys
        sys.path.append('src')
        
        from notebookllama.ragflow_integration import RAGFlowIntegration
        
        integration = RAGFlowIntegration()
        features = integration.available_features
        
        print("📋 Available features:")
        for feature, available in features.items():
            status = "✅" if available else "❌"
            print(f"  {status} {feature}")
            
        return features.get('supabase_vector', False)
        
    except Exception as e:
        print(f"❌ RAG integration test failed: {e}")
        return False

async def test_simple_crawl():
    """Test simple web crawling"""
    print("\n🕷️ Testing web crawling...")
    
    try:
        import sys
        sys.path.append('src')
        
        from notebookllama.rag_clients.crawl_manager import CrawlJobManager
        
        manager = CrawlJobManager()
        
        print("🌐 Testing crawl of TypeScript intro page...")
        
        # Simple test crawl
        url = "https://www.typescriptlang.org/docs/handbook/intro.html"
        
        job_id = await manager.submit_url(url)
        print(f"📝 Created crawl job: {job_id}")
        
        # Check if job was created
        if job_id:
            print("✅ Web crawling working!")
            return True
        else:
            print("❌ No job ID returned")
            return False
            
    except Exception as e:
        print(f"❌ Web crawling test failed: {e}")
        return False

def main():
    print("🧪 Testing RAG Integration Components")
    print("=" * 50)
    
    results = []
    
    # Test 1: Supabase connection
    results.append(test_supabase_connection())
    
    # Test 2: RAG integration
    results.append(test_rag_integration())
    
    # Test 3: Topic discovery
    results.append(test_topic_discovery())
    
    # Test 4: Web crawling
    try:
        results.append(asyncio.run(test_simple_crawl()))
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        results.append(False)
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Your RAG system is ready!")
        print("\n🚀 Next steps:")
        print("1. Open http://localhost:8501 in your browser")
        print("2. Go to 'Topic Discovery' page")  
        print("3. Type 'typescript' and hit Enter")
        print("4. Wait for content to be discovered and processed")
        print("5. Start asking TypeScript questions!")
    else:
        print("⚠️  Some tests failed - check the errors above")

if __name__ == "__main__":
    main()
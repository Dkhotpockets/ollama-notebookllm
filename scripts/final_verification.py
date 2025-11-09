#!/usr/bin/env python3
"""
Final verification after crawl_jobs table creation
Run this AFTER creating the crawl_jobs table in Supabase
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def verify_system():
    """Complete system verification"""
    print("🔍 Final System Verification")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Check environment
    print("\n1️⃣  Environment Variables:")
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'OLLAMA_HOST']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * 20}...")
        else:
            print(f"  ❌ {var}: NOT SET")
            all_passed = False
    
    # 2. Check Supabase tables
    print("\n2️⃣  Supabase Tables:")
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url, key)
        
        tables = ['documents', 'chunks', 'topics', 'crawl_jobs']
        for table in tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"  ✅ {table}: accessible")
            except Exception as e:
                print(f"  ❌ {table}: {str(e)[:50]}")
                all_passed = False
                
    except Exception as e:
        print(f"  ❌ Supabase connection failed: {e}")
        all_passed = False
    
    # 3. Test RAGFlow integration
    print("\n3️⃣  RAGFlow Integration:")
    try:
        from notebookllama.ragflow_integration import RAGFlowIntegration
        
        rag = RAGFlowIntegration()
        features = rag.get_available_features()
        
        critical_features = ['vector_search', 'supabase_vector', 'web_crawling', 'ollama']
        for feature in critical_features:
            if features.get(feature):
                print(f"  ✅ {feature}: available")
            else:
                print(f"  ⚠️  {feature}: not available")
                
    except Exception as e:
        print(f"  ❌ Integration failed: {e}")
        all_passed = False
    
    # 4. Test document CRUD
    print("\n4️⃣  Document Operations:")
    try:
        from notebookllama.rag_clients.supabase_client import add_document_to_supabase
        
        # Add test document
        test_title = "Test Document - Delete Me"
        test_doc = await add_document_to_supabase(
            supabase,
            content="This is a test document for verification.",
            metadata={
                "url": "https://test.example.com",
                "content_type": "text"
            },
            title=test_title
        )
        
        if test_doc:
            print(f"  ✅ Document insertion: working")
            
            # Try to retrieve
            result = supabase.table('documents').select('*').eq('title', test_title).execute()
            if result.data:
                print(f"  ✅ Document retrieval: working")
                
                # Clean up
                doc_id = result.data[0]['id']
                supabase.table('documents').delete().eq('id', doc_id).execute()
                print(f"  ✅ Document deletion: working")
            else:
                print(f"  ⚠️  Document retrieval: failed")
        else:
            print(f"  ❌ Document insertion: failed")
            all_passed = False
            
    except Exception as e:
        print(f"  ❌ Document operations failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # 5. Test topic discovery
    print("\n5️⃣  Topic Discovery:")
    try:
        from notebookllama.agents.topic_discovery_agent import TopicDiscoveryAgent
        
        agent = TopicDiscoveryAgent()
        print(f"  ✅ Agent initialized")
        
        # Try discovering TypeScript resources
        resources = await agent.discover_resources("python basics", max_results=2)
        if resources and len(resources) > 0:
            print(f"  ✅ Resource discovery: found {len(resources)} resources")
        else:
            print(f"  ⚠️  Resource discovery: no resources found")
            
    except Exception as e:
        print(f"  ❌ Topic discovery failed: {e}")
        all_passed = False
    
    # 6. Test Ollama
    print("\n6️⃣  Ollama LLM:")
    try:
        import requests
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f"  ✅ Ollama running: {len(models)} models")
            
            # Check for recommended models
            if any('mistral' in m or '7b' in m for m in model_names):
                print(f"  ✅ Chat model available")
            if any('embed' in m for m in model_names):
                print(f"  ✅ Embedding model available")
        else:
            print(f"  ⚠️  Ollama connection: status {response.status_code}")
            
    except Exception as e:
        print(f"  ⚠️  Ollama check failed: {e}")
    
    # 7. Test end-to-end workflow
    print("\n7️⃣  End-to-End Workflow:")
    try:
        # Try the full workflow with TypeScript topic
        print("  🔍 Testing TypeScript topic discovery...")
        
        rag = RAGFlowIntegration()
        result = await rag.discover_and_ingest_topic("typescript", max_urls=1)
        
        if result.get("success"):
            print(f"  ✅ Workflow completed successfully")
            print(f"     URLs processed: {result.get('urls_processed', 0)}")
            print(f"     Documents stored: {result.get('documents_stored', 0)}")
        else:
            print(f"  ⚠️  Workflow completed with issues: {result.get('error')}")
            
    except Exception as e:
        print(f"  ❌ End-to-end test failed: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n📝 Ready to use:")
        print("   python scripts/bootstrap_topic.py typescript")
        print("   streamlit run src/notebookllama/Home.py")
        return 0
    else:
        print("⚠️  Some issues detected - check messages above")
        return 1

if __name__ == "__main__":
    try:
        result = asyncio.run(verify_system())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n⚠️  Verification cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
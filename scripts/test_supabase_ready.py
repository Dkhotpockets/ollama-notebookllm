#!/usr/bin/env python3
"""
Test Supabase integration after tables are created
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_supabase_after_setup():
    """Test if Supabase tables were created and are accessible"""
    
    print("🧪 Testing Supabase Integration")
    print("=" * 50)
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials")
            return False
            
        supabase = create_client(url, key)
        print(f"📡 Connected to: {url}")
        
        # Test each table
        tables = ['documents', 'chunks', 'topics']
        
        for table in tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"  ✅ Table '{table}' is accessible")
            except Exception as e:
                print(f"  ❌ Table '{table}' error: {e}")
                return False
        
        # Try inserting a test document
        print("\n🔍 Testing document insertion...")
        
        test_doc = {
            'title': 'Test TypeScript Document',
            'content': 'TypeScript is a programming language developed by Microsoft.',
            'url': 'https://www.typescriptlang.org/docs/',
            'content_type': 'text',
            'metadata': {'test': True, 'topic': 'typescript'}
        }
        
        try:
            result = supabase.table('documents').insert(test_doc).execute()
            if result.data:
                doc_id = result.data[0]['id']
                print(f"  ✅ Test document inserted with ID: {doc_id}")
                
                # Test querying
                query_result = supabase.table('documents').select('*').eq('id', doc_id).execute()
                if query_result.data:
                    print(f"  ✅ Document retrieved successfully")
                    
                    # Clean up test document
                    supabase.table('documents').delete().eq('id', doc_id).execute()
                    print(f"  ✅ Test document cleaned up")
                else:
                    print(f"  ❌ Could not retrieve test document")
                    
            else:
                print(f"  ❌ No data returned from insert")
                return False
                
        except Exception as e:
            print(f"  ❌ Document insertion failed: {e}")
            return False
        
        # Test RAGFlow integration
        print("\n🤖 Testing RAGFlow integration...")
        
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
            
            if features.get('supabase_vector', False):
                print("\n🎯 SUCCESS! Supabase vector storage is ready!")
                print("\n🚀 Your system can now:")
                print("  1. Automatically discover TypeScript learning content")
                print("  2. Store it in Supabase cloud database")  
                print("  3. Search using vector embeddings")
                print("  4. Chat about the discovered content")
                
                print("\n📝 Try this command:")
                print("  streamlit run src/notebookllama/Home.py")
                print("  Then go to 'Topic Discovery' and enter 'typescript'")
                
                return True
            else:
                print("❌ Supabase vector storage not detected")
                return False
                
        except Exception as e:
            print(f"❌ RAGFlow integration test failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_supabase_after_setup())
    if success:
        print("\n🎉 All tests passed! Your automatic topic discovery system is ready!")
    else:
        print("\n⚠️  Some tests failed. Make sure you ran the SQL in Supabase dashboard.")
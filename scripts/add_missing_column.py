#!/usr/bin/env python3
"""
Add completed_at column using direct database connection
"""

import os
from dotenv import load_dotenv

load_dotenv()

def add_completed_at_column():
    """Add completed_at column to crawl_jobs table"""
    print("🔧 Adding completed_at column to crawl_jobs table...")
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Get Supabase connection details
        supabase_url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        
        # Extract project reference
        project_ref = supabase_url.split('//')[1].split('.')[0]
        
        # Construct PostgreSQL connection string
        # Supabase uses port 5432 for direct PostgreSQL connections
        db_host = f"db.{project_ref}.supabase.co"
        db_name = "postgres"
        db_user = "postgres"
        
        # For service role, we need the actual database password
        # This is typically found in Supabase dashboard under Settings > Database
        print(f"📡 Connecting to: {db_host}")
        print("\n⚠️  Note: Direct database connection requires database password")
        print("   This is different from the API keys.")
        print("   Find it in: Supabase Dashboard > Settings > Database > Connection string")
        print("\n   For now, let me try using the Supabase Python client with a workaround...")
        
        # Alternative: Use supabase-py with raw SQL via stored procedure
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        
        supabase = create_client(url, key)
        
        # Try using the SQL editor API endpoint
        import requests
        
        # Supabase SQL API endpoint (if available)
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        sql_query = "ALTER TABLE public.crawl_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;"
        
        # Try multiple endpoints
        endpoints = [
            f"{url}/rest/v1/rpc/exec_sql",
            f"{url}/rest/v1/rpc/query", 
            f"{url}/database/query"
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\n  Trying: {endpoint}")
                response = requests.post(
                    endpoint,
                    json={'query': sql_query, 'sql': sql_query},
                    headers=headers,
                    timeout=10
                )
                print(f"  Status: {response.status_code}")
                if response.status_code in [200, 201]:
                    print("  ✅ Success!")
                    return True
            except Exception as e:
                print(f"  ❌ {e}")
        
        print("\n⚠️  Could not execute SQL via API.")
        print("\n📋 Please run this in Supabase SQL Editor:")
        print("=" * 60)
        print(sql_query)
        print("=" * 60)
        print(f"\nURL: https://supabase.com/dashboard/project/{project_ref}/sql/new")
        
        return False
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    if not add_completed_at_column():
        print("\n💡 The column needs to be added manually via Supabase dashboard.")
        print("   It's just one line of SQL - takes 10 seconds!")
        sys.exit(1)
    
    print("\n🎉 Column added! Testing...")
    
    # Test the column
    from supabase import create_client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    sb = create_client(url, key)
    
    try:
        test = sb.table('crawl_jobs').insert({
            'job_id': 'test_with_completed',
            'url': 'https://test.com',
            'status': 'completed',
            'completed_at': '2025-01-01T00:00:00Z'
        }).execute()
        
        print("✅ Insert with completed_at works!")
        
        # Cleanup
        sb.table('crawl_jobs').delete().eq('job_id', 'test_with_completed').execute()
        
        print("\n🚀 Ready to run:")
        print("   python scripts/complete_test_suite.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
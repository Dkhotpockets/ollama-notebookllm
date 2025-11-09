#!/usr/bin/env python3
"""
Auto-setup Supabase tables using service role key
This script uses the service role key to create any missing tables
"""

import os
from dotenv import load_dotenv

load_dotenv()

def setup_crawl_jobs_table():
    """Create crawl_jobs table if it doesn't exist"""
    print("🔧 Setting up Supabase tables with service role key...")
    print("=" * 60)
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        # Use service role key for admin access
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials")
            return False
        
        print(f"📡 Connecting to: {url}")
        print(f"🔑 Using key type: {'service_role' if 'service_role' in key else 'anon'}")
        
        supabase = create_client(url, key)
        
        # Check if crawl_jobs table exists
        try:
            result = supabase.table('crawl_jobs').select('*').limit(1).execute()
            print("✅ crawl_jobs table already exists")
            return True
        except Exception as e:
            if 'PGRST205' in str(e):
                print("⚠️  crawl_jobs table not found, creating...")
            else:
                print(f"⚠️  Error checking table: {e}")
        
        # Create the table using PostgreSQL REST API
        create_sql = """
        CREATE TABLE IF NOT EXISTS public.crawl_jobs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            job_id TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result JSONB,
            error TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS crawl_jobs_job_id_idx ON public.crawl_jobs (job_id);
        CREATE INDEX IF NOT EXISTS crawl_jobs_status_idx ON public.crawl_jobs (status);
        CREATE INDEX IF NOT EXISTS crawl_jobs_url_idx ON public.crawl_jobs (url);
        
        ALTER TABLE public.crawl_jobs ENABLE ROW LEVEL SECURITY;
        CREATE POLICY IF NOT EXISTS "Enable all operations" ON public.crawl_jobs FOR ALL USING (true);
        """
        
        # Try to execute via direct SQL (requires service role)
        try:
            # Use the SQL editor endpoint
            import requests
            
            headers = {
                'apikey': key,
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json'
            }
            
            # Supabase SQL endpoint
            sql_url = f"{url}/rest/v1/rpc/exec_sql"
            
            # Try executing the SQL
            response = requests.post(
                sql_url,
                json={'query': create_sql},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ crawl_jobs table created successfully!")
                
                # Verify it was created
                result = supabase.table('crawl_jobs').select('*').limit(1).execute()
                print("✅ Verified: crawl_jobs table is accessible")
                return True
            else:
                print(f"⚠️  SQL execution returned: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"⚠️  Could not execute SQL directly: {e}")
        
        # Alternative: Try using Supabase Admin API
        print("\n💡 Alternative: Run this SQL in Supabase SQL Editor:")
        print("=" * 60)
        print(create_sql)
        print("=" * 60)
        
        return False
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run auto-setup"""
    print("\n🚀 Supabase Auto-Setup")
    print("This will create missing tables using the service role key")
    print()
    
    success = setup_crawl_jobs_table()
    
    if success:
        print("\n🎉 Setup complete! All tables ready.")
        print("\n📝 Test your system:")
        print("   python scripts/complete_test_suite.py")
    else:
        print("\n⚠️  Automatic setup couldn't complete.")
        print("   Please run the SQL manually in Supabase dashboard.")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
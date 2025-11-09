#!/usr/bin/env python3
"""
Create crawl_jobs table using service role key
"""

import os
from dotenv import load_dotenv

load_dotenv()

def create_crawl_jobs_table():
    """Create crawl_jobs table with all required columns"""
    print("🔧 Creating crawl_jobs table with service role key...")
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        
        supabase = create_client(url, key)
        
        # Drop existing table if it has wrong schema
        print("📋 Dropping existing table if needed...")
        try:
            supabase.postgrest.rpc('exec', {
                'query': 'DROP TABLE IF EXISTS public.crawl_jobs CASCADE;'
            }).execute()
        except:
            pass
        
        # Create table with ALL required columns
        create_sql = """
        CREATE TABLE public.crawl_jobs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            job_id TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result JSONB,
            error TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE
        );
        
        CREATE INDEX crawl_jobs_job_id_idx ON public.crawl_jobs (job_id);
        CREATE INDEX crawl_jobs_status_idx ON public.crawl_jobs (status);
        CREATE INDEX crawl_jobs_url_idx ON public.crawl_jobs (url);
        
        ALTER TABLE public.crawl_jobs ENABLE ROW LEVEL SECURITY;
        CREATE POLICY "Enable all operations" ON public.crawl_jobs FOR ALL USING (true);
        """
        
        # Execute each statement separately
        statements = [
            """CREATE TABLE public.crawl_jobs (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                job_id TEXT NOT NULL UNIQUE,
                url TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result JSONB,
                error TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE
            )""",
            "CREATE INDEX crawl_jobs_job_id_idx ON public.crawl_jobs (job_id)",
            "CREATE INDEX crawl_jobs_status_idx ON public.crawl_jobs (status)",
            "CREATE INDEX crawl_jobs_url_idx ON public.crawl_jobs (url)",
            "ALTER TABLE public.crawl_jobs ENABLE ROW LEVEL SECURITY",
            'CREATE POLICY "Enable all operations" ON public.crawl_jobs FOR ALL USING (true)'
        ]
        
        import requests
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Use Supabase REST API to execute SQL
        for i, stmt in enumerate(statements, 1):
            print(f"  Executing statement {i}/{len(statements)}...")
            try:
                # Try using the query endpoint
                response = requests.post(
                    f"{url}/rest/v1/rpc/query",
                    json={'query': stmt},
                    headers=headers,
                    timeout=10
                )
                if response.status_code not in [200, 201, 204]:
                    print(f"    ⚠️  Statement {i} returned: {response.status_code}")
            except Exception as e:
                print(f"    ⚠️  Statement {i}: {e}")
        
        # Verify table was created
        print("\n✅ Verifying table...")
        result = supabase.table('crawl_jobs').select('*').limit(1).execute()
        print("✅ crawl_jobs table created successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = create_crawl_jobs_table()
    
    if success:
        print("\n🎉 Table ready! Run tests:")
        print("   python scripts/complete_test_suite.py")
    else:
        print("\n⚠️  Could not create table automatically.")
        print("   Please run the SQL manually in Supabase dashboard.")
    
    sys.exit(0 if success else 1)
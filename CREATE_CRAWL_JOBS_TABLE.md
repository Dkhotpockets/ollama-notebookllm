# 🔧 Final Setup Step - Create crawl_jobs Table

## Quick Action Required
Copy and paste the SQL below into your Supabase SQL Editor:

### Go to: https://supabase.com/dashboard/project/ncapakerbdtnmrvvaqzc/sql/new

```sql
-- Create crawl_jobs table for web crawling job tracking
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS crawl_jobs_job_id_idx ON public.crawl_jobs (job_id);
CREATE INDEX IF NOT EXISTS crawl_jobs_status_idx ON public.crawl_jobs (status);
CREATE INDEX IF NOT EXISTS crawl_jobs_url_idx ON public.crawl_jobs (url);

-- Enable Row Level Security
ALTER TABLE public.crawl_jobs ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed for production)
CREATE POLICY "Enable all operations" ON public.crawl_jobs FOR ALL USING (true);
```

## After Running the SQL

Test your complete system:

```powershell
# Test all components
python scripts/complete_test_suite.py

# Try learning TypeScript (your use case!)
python scripts/bootstrap_topic.py typescript
```

## What This Table Does
- **job_id**: Unique identifier for each crawl job
- **url**: The web page being crawled
- **status**: pending/processing/completed/failed
- **result**: JSON data from successful crawl
- **error**: Error message if crawl failed
- **Indexes**: Speed up queries by job_id, status, url

## Why We Need This
The TopicDiscoveryAgent tracks web crawling jobs in this table so you can:
- Monitor crawl progress
- Avoid duplicate crawls
- Retry failed crawls
- See what resources were already discovered

---

**Note**: Once this table is created, ALL 6 tests should pass! ✅
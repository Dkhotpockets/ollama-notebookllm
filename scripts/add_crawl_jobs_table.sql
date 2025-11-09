-- Additional table needed for crawl job tracking
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
CREATE POLICY "Enable all operations" ON public.crawl_jobs FOR ALL USING (true);
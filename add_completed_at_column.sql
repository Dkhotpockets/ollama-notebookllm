-- Add missing completed_at column to crawl_jobs table
ALTER TABLE public.crawl_jobs 
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;

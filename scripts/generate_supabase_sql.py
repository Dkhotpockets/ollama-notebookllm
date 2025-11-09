#!/usr/bin/env python3
"""
Generate SQL for Supabase table creation

This script generates the exact SQL you need to run in your Supabase SQL Editor
to create all the necessary tables for RAGFlow integration.
"""

def generate_supabase_sql():
    """Generate complete SQL for Supabase setup"""
    
    sql = """-- RAGFlow Integration Tables for Supabase
-- Run this in your Supabase SQL Editor

-- Enable the vector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table - stores crawled web content and uploaded files
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    content_type TEXT DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),  -- OpenAI/similar embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chunks table - stores document segments for better search
CREATE TABLE IF NOT EXISTS public.chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Entities table - for knowledge graph functionality
CREATE TABLE IF NOT EXISTS public.entities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    entity_type TEXT NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Relationships table - connections between entities
CREATE TABLE IF NOT EXISTS public.relationships (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topics table - for topic-based content discovery
CREATE TABLE IF NOT EXISTS public.topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    resources_count INTEGER DEFAULT 0,
    last_crawled TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topic resources junction table
CREATE TABLE IF NOT EXISTS public.topic_resources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    topic_id UUID REFERENCES public.topics(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(topic_id, document_id)
);

-- Create vector similarity search indexes
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON public.documents USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
ON public.chunks USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS entities_embedding_idx 
ON public.entities USING ivfflat (embedding vector_cosine_ops);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS documents_url_idx ON public.documents (url);
CREATE INDEX IF NOT EXISTS documents_created_idx ON public.documents (created_at);
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON public.chunks (document_id);
CREATE INDEX IF NOT EXISTS entities_name_idx ON public.entities (name);
CREATE INDEX IF NOT EXISTS entities_type_idx ON public.entities (entity_type);
CREATE INDEX IF NOT EXISTS relationships_source_idx ON public.relationships (source_entity_id);
CREATE INDEX IF NOT EXISTS relationships_target_idx ON public.relationships (target_entity_id);
CREATE INDEX IF NOT EXISTS topics_name_idx ON public.topics (name);
CREATE INDEX IF NOT EXISTS topic_resources_topic_idx ON public.topic_resources (topic_id);

-- Create metadata indexes for flexible queries
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON public.documents USING gin (metadata);
CREATE INDEX IF NOT EXISTS chunks_metadata_idx ON public.chunks USING gin (metadata);
CREATE INDEX IF NOT EXISTS entities_metadata_idx ON public.entities USING gin (metadata);

-- Enable Row Level Security (RLS)
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topic_resources ENABLE ROW LEVEL SECURITY;

-- Create permissive policies for now (adjust based on your security needs)
CREATE POLICY "Enable all operations for authenticated users" ON public.documents
FOR ALL USING (true);

CREATE POLICY "Enable all operations for authenticated users" ON public.chunks
FOR ALL USING (true);

CREATE POLICY "Enable all operations for authenticated users" ON public.entities
FOR ALL USING (true);

CREATE POLICY "Enable all operations for authenticated users" ON public.relationships
FOR ALL USING (true);

CREATE POLICY "Enable all operations for authenticated users" ON public.topics
FOR ALL USING (true);

CREATE POLICY "Enable all operations for authenticated users" ON public.topic_resources
FOR ALL USING (true);

-- Verification query - run this to check tables were created
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('documents', 'chunks', 'entities', 'relationships', 'topics', 'topic_resources')
ORDER BY tablename;
"""
    return sql

def main():
    """Main function to display the SQL"""
    
    print("🗃️  Supabase Table Creation SQL")
    print("=" * 80)
    print()
    print("📋 Copy the SQL below and paste it into your Supabase SQL Editor:")
    print()
    print("1. Go to: https://supabase.com/dashboard/project/gixypiuqzhyungysoauh")
    print("2. Click 'SQL Editor' in the left sidebar")
    print("3. Click 'New Query'")
    print("4. Copy and paste the SQL below")
    print("5. Click 'Run' to execute")
    print()
    print("=" * 80)
    print()
    
    sql = generate_supabase_sql()
    print(sql)
    
    print()
    print("=" * 80)
    print("✅ After running the SQL, test with:")
    print("   python scripts/bootstrap_topic.py typescript")
    print()
    print("🎯 This will create tables for:")
    print("   • Document storage (crawled content)")
    print("   • Vector embeddings (semantic search)")
    print("   • Knowledge graph (entities & relationships)")
    print("   • Topic discovery (automatic content finding)")

if __name__ == "__main__":
    main()
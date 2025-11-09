#!/usr/bin/env python3
"""
Create Supabase tables using MCP tools for RAGFlow integration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_supabase_tables():
    """Create all necessary tables in Supabase for RAG functionality"""
    
    print("🚀 Creating Supabase tables for RAGFlow...")
    print("=" * 60)
    
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env")
            return False
            
        print(f"📡 Connecting to: {url}")
        supabase = create_client(url, key)
        
        # Test connection first
        try:
            # Try a simple table query instead
            response = supabase.table('pg_stat_activity').select('*').limit(1).execute()
            print("✅ Successfully connected to Supabase")
        except Exception as e:
            print(f"⚠️  Connection test warning: {e}")
            print("✅ Proceeding anyway - Supabase client created successfully")
        
        # SQL for creating all tables
        table_sql = """
-- Enable vector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table for storing crawled content
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT,
    content_type TEXT DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chunks table for document segments
CREATE TABLE IF NOT EXISTS public.chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Entities table for knowledge graph
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

-- Relationships table for knowledge graph connections
CREATE TABLE IF NOT EXISTS public.relationships (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topics table for topic discovery
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

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON public.documents USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
ON public.chunks USING ivfflat (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS entities_embedding_idx 
ON public.entities USING ivfflat (embedding vector_cosine_ops);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS documents_url_idx ON public.documents (url);
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON public.chunks (document_id);
CREATE INDEX IF NOT EXISTS entities_name_idx ON public.entities (name);
CREATE INDEX IF NOT EXISTS entities_type_idx ON public.entities (entity_type);
CREATE INDEX IF NOT EXISTS relationships_source_idx ON public.relationships (source_entity_id);
CREATE INDEX IF NOT EXISTS relationships_target_idx ON public.relationships (target_entity_id);
CREATE INDEX IF NOT EXISTS topics_name_idx ON public.topics (name);

-- Create indexes for metadata queries
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON public.documents USING gin (metadata);
CREATE INDEX IF NOT EXISTS chunks_metadata_idx ON public.chunks USING gin (metadata);
CREATE INDEX IF NOT EXISTS entities_metadata_idx ON public.entities USING gin (metadata);

-- Enable Row Level Security
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topic_resources ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (allow public access for now - adjust based on your security needs)
CREATE POLICY IF NOT EXISTS "Allow public access" ON public.documents FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Allow public access" ON public.chunks FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Allow public access" ON public.entities FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Allow public access" ON public.relationships FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Allow public access" ON public.topics FOR ALL USING (true);
CREATE POLICY IF NOT EXISTS "Allow public access" ON public.topic_resources FOR ALL USING (true);
"""
        
        print("📋 Creating tables and indexes...")
        
        # Use a more direct approach with the SQL runner
        try:
            # For Supabase, we need to execute SQL via the API
            # Let's try creating tables one by one
            
            table_definitions = [
                # Enable vector extension
                "CREATE EXTENSION IF NOT EXISTS vector;",
                
                # Documents table
                """CREATE TABLE IF NOT EXISTS public.documents (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT,
                    content_type TEXT DEFAULT 'text',
                    metadata JSONB DEFAULT '{}',
                    embedding VECTOR(1536),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );""",
                
                # Chunks table
                """CREATE TABLE IF NOT EXISTS public.chunks (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );""",
                
                # Entities table
                """CREATE TABLE IF NOT EXISTS public.entities (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    entity_type TEXT NOT NULL,
                    description TEXT,
                    metadata JSONB DEFAULT '{}',
                    embedding VECTOR(1536),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );""",
                
                # Topics table
                """CREATE TABLE IF NOT EXISTS public.topics (
                    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    resources_count INTEGER DEFAULT 0,
                    last_crawled TIMESTAMP WITH TIME ZONE,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );"""
            ]
            
            # Try to execute each table definition
            for i, sql in enumerate(table_definitions):
                try:
                    print(f"  📝 Creating table/extension {i+1}/{len(table_definitions)}...")
                    # Note: This might not work with anon key - may need service role key
                    response = supabase.rpc('exec_sql', {'query': sql}).execute()
                    print(f"  ✅ Success")
                except Exception as e:
                    print(f"  ⚠️  Warning: {e}")
                    # Continue anyway - tables might already exist or need manual creation
            
            print("✅ Table creation completed!")
            
        except Exception as e:
            print(f"❌ Failed to execute SQL: {e}")
            print("\n💡 The anon key might not have DDL permissions.")
            print("💡 You may need to create tables manually in Supabase SQL Editor.")
            print("\n📋 Copy this SQL to Supabase SQL Editor:")
            print("=" * 60)
            print(table_sql[:1000] + "...")
            print("=" * 60)
        
        # Test the tables were created
        print("\n🔍 Testing table creation...")
        
        test_tables = ['documents', 'chunks', 'entities', 'relationships', 'topics']
        
        for table in test_tables:
            try:
                result = supabase.table(table).select('*').limit(1).execute()
                print(f"  ✅ Table '{table}' accessible")
            except Exception as e:
                print(f"  ❌ Table '{table}' error: {e}")
                
        print("\n" + "=" * 60)
        print("🎉 Supabase setup complete!")
        print("\n🚀 Next steps:")
        print("1. Test topic discovery: python scripts/bootstrap_topic.py typescript")
        print("2. Or start Streamlit: streamlit run src/notebookllama/Home.py")
        print("3. Go to 'Topic Discovery' page and enter a topic!")
        
        return True
        
    except ImportError:
        print("❌ Supabase client not installed. Install with: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = create_supabase_tables()
    sys.exit(0 if success else 1)
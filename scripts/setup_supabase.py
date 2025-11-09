#!/usr/bin/env python3
"""
Setup Supabase database with required tables and extensions for RAGFlow

This script will:
1. Enable the vector extension in your Supabase database
2. Create the required tables for document storage and vector embeddings
3. Set up the knowledge graph integration tables
4. Configure security policies

Prerequisites:
- Supabase project created
- SUPABASE_URL and SUPABASE_KEY set in .env file
"""

import os
import sys
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_supabase_client() -> Optional[Client]:
    """Create and return Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        print("\nTo get your credentials:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Settings → API")
        print("4. Copy 'Project URL' and 'anon public' key")
        return None
    
    if 'your-supabase-anon-key-here' in key:
        print("❌ Please replace 'your-supabase-anon-key-here' with your actual Supabase anon key")
        return None
    
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return None

def setup_vector_extension(supabase: Client) -> bool:
    """Enable vector extension (requires SQL Editor or service role key)"""
    print("📦 Setting up vector extension...")
    
    # This requires service role key or SQL Editor access
    print("⚠️  Vector extension setup requires manual SQL execution")
    print("\nPlease run this SQL in your Supabase SQL Editor:")
    print("=" * 60)
    print("-- Enable the vector extension")
    print("CREATE EXTENSION IF NOT EXISTS vector;")
    print("")
    print("-- Verify extension is enabled")
    print("SELECT * FROM pg_extension WHERE extname = 'vector';")
    print("=" * 60)
    
    return True

def create_documents_table(supabase: Client) -> bool:
    """Create documents table for RAG storage"""
    print("📋 Creating documents table...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS documents (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        url TEXT,
        content_type TEXT DEFAULT 'text',
        metadata JSONB DEFAULT '{}',
        embedding VECTOR(1536),  -- OpenAI embedding dimension
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create index for vector similarity search
    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
    ON documents USING ivfflat (embedding vector_cosine_ops);
    
    -- Create index for metadata queries
    CREATE INDEX IF NOT EXISTS documents_metadata_idx 
    ON documents USING gin (metadata);
    
    -- Create index for content search
    CREATE INDEX IF NOT EXISTS documents_content_idx 
    ON documents USING gin (to_tsvector('english', content));
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': sql})
        print("✅ Documents table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create documents table: {e}")
        print("\nPlease run this SQL manually in Supabase SQL Editor:")
        print("=" * 60)
        print(sql)
        print("=" * 60)
        return False

def create_chunks_table(supabase: Client) -> bool:
    """Create chunks table for document segments"""
    print("🧩 Creating chunks table...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS chunks (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        embedding VECTOR(1536),
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create index for vector similarity search
    CREATE INDEX IF NOT EXISTS chunks_embedding_idx 
    ON chunks USING ivfflat (embedding vector_cosine_ops);
    
    -- Create index for document relationship
    CREATE INDEX IF NOT EXISTS chunks_document_id_idx 
    ON chunks (document_id);
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': sql})
        print("✅ Chunks table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create chunks table: {e}")
        return False

def create_entities_table(supabase: Client) -> bool:
    """Create entities table for knowledge graph"""
    print("🕸️ Creating entities table...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS entities (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        entity_type TEXT NOT NULL,
        description TEXT,
        metadata JSONB DEFAULT '{}',
        embedding VECTOR(1536),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create index for vector similarity search
    CREATE INDEX IF NOT EXISTS entities_embedding_idx 
    ON entities USING ivfflat (embedding vector_cosine_ops);
    
    -- Create index for name lookup
    CREATE INDEX IF NOT EXISTS entities_name_idx 
    ON entities (name);
    
    -- Create index for type filtering
    CREATE INDEX IF NOT EXISTS entities_type_idx 
    ON entities (entity_type);
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': sql})
        print("✅ Entities table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create entities table: {e}")
        return False

def create_relationships_table(supabase: Client) -> bool:
    """Create relationships table for knowledge graph connections"""
    print("🔗 Creating relationships table...")
    
    sql = """
    CREATE TABLE IF NOT EXISTS relationships (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        source_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
        target_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
        relationship_type TEXT NOT NULL,
        weight FLOAT DEFAULT 1.0,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create index for source entity lookup
    CREATE INDEX IF NOT EXISTS relationships_source_idx 
    ON relationships (source_entity_id);
    
    -- Create index for target entity lookup
    CREATE INDEX IF NOT EXISTS relationships_target_idx 
    ON relationships (target_entity_id);
    
    -- Create index for relationship type
    CREATE INDEX IF NOT EXISTS relationships_type_idx 
    ON relationships (relationship_type);
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': sql})
        print("✅ Relationships table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create relationships table: {e}")
        return False

def setup_rls_policies(supabase: Client) -> bool:
    """Set up Row Level Security policies"""
    print("🔒 Setting up security policies...")
    
    sql = """
    -- Enable RLS on all tables
    ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
    ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
    ALTER TABLE entities ENABLE ROW LEVEL SECURITY;
    ALTER TABLE relationships ENABLE ROW LEVEL SECURITY;
    
    -- Allow public read access (adjust based on your security needs)
    CREATE POLICY IF NOT EXISTS "Allow public read access" 
    ON documents FOR SELECT USING (true);
    
    CREATE POLICY IF NOT EXISTS "Allow public read access" 
    ON chunks FOR SELECT USING (true);
    
    CREATE POLICY IF NOT EXISTS "Allow public read access" 
    ON entities FOR SELECT USING (true);
    
    CREATE POLICY IF NOT EXISTS "Allow public read access" 
    ON relationships FOR SELECT USING (true);
    
    -- Allow public insert (adjust based on your security needs)
    CREATE POLICY IF NOT EXISTS "Allow public insert" 
    ON documents FOR INSERT WITH CHECK (true);
    
    CREATE POLICY IF NOT EXISTS "Allow public insert" 
    ON chunks FOR INSERT WITH CHECK (true);
    
    CREATE POLICY IF NOT EXISTS "Allow public insert" 
    ON entities FOR INSERT WITH CHECK (true);
    
    CREATE POLICY IF NOT EXISTS "Allow public insert" 
    ON relationships FOR INSERT WITH CHECK (true);
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': sql})
        print("✅ Security policies created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create security policies: {e}")
        print("⚠️  You may need to set these up manually in Supabase Dashboard")
        return False

def test_connection(supabase: Client) -> bool:
    """Test the connection by querying a simple table"""
    print("🔍 Testing connection...")
    
    try:
        # Try to query the documents table
        result = supabase.table('documents').select('id').limit(1).execute()
        print("✅ Connection test successful")
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Supabase for RAGFlow Integration")
    print("=" * 60)
    
    # Get Supabase client
    supabase = get_supabase_client()
    if not supabase:
        return
    
    print(f"📡 Connected to: {os.getenv('SUPABASE_URL')}")
    
    # Setup steps
    setup_vector_extension(supabase)
    print()
    
    input("Press Enter after you've run the vector extension SQL in Supabase...")
    
    # Create tables
    success = True
    success &= create_documents_table(supabase)
    success &= create_chunks_table(supabase)
    success &= create_entities_table(supabase)
    success &= create_relationships_table(supabase)
    success &= setup_rls_policies(supabase)
    
    # Test connection
    print()
    if test_connection(supabase):
        print("\n" + "=" * 60)
        print("🎉 Supabase setup complete!")
        print("\nYour database is ready for RAGFlow integration.")
        print("\nNext steps:")
        print("1. Update your .env file with the correct SUPABASE_KEY")
        print("2. Run: python scripts/test_integration.py")
        print("3. Start using the RAG system!")
    else:
        print("\n" + "=" * 60)
        print("❌ Setup incomplete - please check the errors above")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Test database connection for Document Management UI
"""

import sys
import os
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv()

from notebookllama.documents import DocumentManager

def test_connection():
    try:
        # Use PGVECTOR_PORT from environment (default to 5433 for Docker setup)
        port = os.getenv('PGVECTOR_PORT', '5433')
        engine_url = f"postgresql+psycopg2://{os.getenv('PGVECTOR_USER')}:{os.getenv('PGVECTOR_PASSWORD')}@localhost:{port}/{os.getenv('PGVECTOR_DATABASE')}"
        print('Engine URL:', engine_url.replace(os.getenv('PGVECTOR_PASSWORD'), '***'))

        document_manager = DocumentManager(engine_url=engine_url)
        print('[SUCCESS] DocumentManager created successfully')

        # Test connection
        names = document_manager.get_names()
        print('[SUCCESS] Database connection successful, found', len(names), 'documents')

    except Exception as e:
        print('[ERROR] Database connection failed:', e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
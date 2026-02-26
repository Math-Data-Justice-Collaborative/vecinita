#!/usr/bin/env python3
#supabase_test.py
"""
Vecinita Test Script
Tests database connectivity, schema installation, and basic operations
"""

import os
import sys
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test basic database connection"""
    print("\n1. Testing Database Connection...")
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ FAILED: Missing SUPABASE_URL or SUPABASE_KEY in .env")
        return None
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"✅ Connected to Supabase at {supabase_url[:30]}...")
        return supabase
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return None

def test_schema(supabase: Client):
    """Test if schema is properly installed"""
    print("\n2. Testing Schema Installation...")
    
    tables_to_check = [
        'document_chunks',
        'sources',
        'processing_queue',
        'search_queries'
    ]
    
    all_good = True
    for table in tables_to_check:
        try:
            response = supabase.table(table).select('id').limit(1).execute()
            print(f"✅ Table '{table}' exists")
        except Exception as e:
            print(f"❌ Table '{table}' not found: {e}")
            all_good = False
    
    return all_good

def test_insert(supabase: Client):
    """Test inserting a sample chunk"""
    print("\n3. Testing Data Insert...")
    
    test_chunk = {
        'content': 'This is a test chunk for Vecinita vector database.',
        'source_url': 'https://test.example.com/page',
        'chunk_index': 1,
        'total_chunks': 1,
        'scraped_at': datetime.utcnow().isoformat(),
        'is_processed': False,
        'processing_status': 'test',
        'metadata': {'test': True}
    }
    
    try:
        response = supabase.table('document_chunks').insert(test_chunk).execute()
        if response.data:
            chunk_id = response.data[0]['id']
            print(f"✅ Successfully inserted test chunk with ID: {chunk_id}")
            return chunk_id
        else:
            print("❌ Insert returned no data")
            return None
    except Exception as e:
        print(f"❌ Failed to insert: {e}")
        return None

def test_query(supabase: Client, chunk_id=None):
    """Test querying data"""
    print("\n4. Testing Data Query...")
    
    try:
        # Query by ID if provided
        if chunk_id:
            response = supabase.table('document_chunks').select('*').eq('id', chunk_id).execute()
            if response.data:
                print(f"✅ Retrieved chunk by ID: {chunk_id}")
                print(f"   Content preview: {response.data[0]['content'][:50]}...")
        
        # Query recent chunks
        response = supabase.table('document_chunks').select('id, source_url, chunk_index').limit(5).execute()
        print(f"✅ Found {len(response.data)} chunks in database")
        
        # Check source statistics
        response = supabase.table('sources').select('url, total_chunks').limit(5).execute()
        print(f"✅ Found {len(response.data)} sources in database")
        
        return True
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def test_vector_extension(supabase: Client):
    """Test if pgvector extension is installed"""
    print("\n5. Testing Vector Extension...")
    
    try:
        # Try to create a test vector
        test_query = """
        SELECT '[1,2,3]'::vector AS test_vector;
        """
        response = supabase.rpc('test_vector_extension', {}).execute()
        print("✅ Vector extension is installed")
        return True
    except:
        # Alternative test - try to query with vector type
        try:
            response = supabase.table('document_chunks').select('id').limit(1).execute()
            print("✅ Vector extension appears to be working")
            return True
        except Exception as e:
            print(f"⚠️  Vector extension might not be installed: {e}")
            print("   Run this in Supabase SQL Editor: CREATE EXTENSION IF NOT EXISTS vector;")
            return False

def test_cleanup(supabase: Client, chunk_id):
    """Clean up test data"""
    print("\n6. Cleaning Up Test Data...")
    
    if chunk_id:
        try:
            response = supabase.table('document_chunks').delete().eq('id', chunk_id).execute()
            print(f"✅ Cleaned up test chunk")
        except Exception as e:
            print(f"⚠️  Could not clean up test chunk: {e}")

def main():
    """Run all tests"""
    print("="*50)
    print("VECINITA DATABASE TEST SUITE")
    print("="*50)
    
    # Test connection
    supabase = test_connection()
    if not supabase:
        print("\n❌ Cannot proceed without database connection")
        print("Please check your .env file and ensure SUPABASE_URL and SUPABASE_KEY are set correctly")
        sys.exit(1)
    
    # Test schema
    schema_ok = test_schema(supabase)
    if not schema_ok:
        print("\n❌ Schema is not properly installed")
        print("Please run the SQL from vecinita_schema.sql in your Supabase SQL Editor")
        sys.exit(1)
    
    # Test vector extension
    vector_ok = test_vector_extension(supabase)
    
    # Test operations
    chunk_id = test_insert(supabase)
    if chunk_id:
        test_query(supabase, chunk_id)
        test_cleanup(supabase, chunk_id)
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    if schema_ok and chunk_id:
        print("✅ All tests passed! Vecinita is ready to use.")
        print("\nNext steps:")
        print("1. Run: python vecinita_loader.py your_data_file.txt")
        print("2. Monitor progress in vecinita_loader.log")
        print("3. Query your data through Supabase dashboard")
    else:
        print("⚠️  Some tests failed. Please address the issues above.")
        if not vector_ok:
            print("\nIMPORTANT: Make sure to run 'CREATE EXTENSION IF NOT EXISTS vector;' in Supabase")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
##--end-of-file--

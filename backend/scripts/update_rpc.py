#!/usr/bin/env python3
"""Update the search_similar_documents RPC function in Supabase."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')
load_dotenv('.env')

try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase package not installed. Run: pip install supabase")
    sys.exit(1)

# Updated RPC function SQL
RPC_SQL = """
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
    match_threshold REAL DEFAULT 0.3,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    source_url TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    similarity REAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.content,
        dc.source_url,
        dc.chunk_index,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE dc.embedding IS NOT NULL
        AND dc.is_processed = TRUE
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""


def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)

    print(f"Connecting to Supabase: {supabase_url}")
    client = create_client(supabase_url, supabase_key)

    print("Updating search_similar_documents RPC function...")
    try:
        # Execute the SQL using the REST API's query method
        result = client.rpc('query', {'query': RPC_SQL}).execute()
        print("✓ RPC function updated successfully!")
        print("\nThe database now returns metadata with position information.")
    except Exception as e:
        # Try alternative method using postgrest
        print(f"First method failed: {e}")
        print("\nAttempting alternative update method...")
        print("\n" + "="*60)
        print("MANUAL UPDATE REQUIRED:")
        print("="*60)
        print("\nPlease run this SQL in your Supabase SQL Editor:")
        print("\n" + RPC_SQL)
        print("\n" + "="*60)
        print("\nOr use psql:")
        print(f"  psql '{supabase_url.replace('https://', 'postgresql://postgres:YOUR_PASSWORD@').replace('.supabase.co', '.supabase.co:5432/postgres')}' -c \"{RPC_SQL.replace(chr(10), ' ')}\"")
        sys.exit(1)


if __name__ == "__main__":
    main()

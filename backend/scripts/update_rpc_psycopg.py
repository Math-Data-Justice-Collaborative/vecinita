#!/usr/bin/env python3
"""Update the search_similar_documents RPC function using direct PostgreSQL connection."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')
load_dotenv('.env')

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 package not installed. Run: pip install psycopg2-binary")
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
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        print("\nAlternative: Manually update via Supabase SQL Editor")
        print("\n1. Go to your Supabase project dashboard")
        print("2. Open SQL Editor")
        print("3. Run this SQL:\n")
        print(RPC_SQL)
        sys.exit(1)

    print(f"Connecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        print("Updating search_similar_documents RPC function...")
        cur.execute(RPC_SQL)
        conn.commit()

        print("✓ RPC function updated successfully!")
        print("\nThe database now returns metadata with position information.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"ERROR: Failed to update RPC function: {e}")
        print("\nPlease manually update via Supabase SQL Editor:")
        print(RPC_SQL)
        sys.exit(1)


if __name__ == "__main__":
    main()

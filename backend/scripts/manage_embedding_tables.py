"""
Script to create/drop/migrate embedding chunk tables for each provider/model combo.
"""
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

TABLE_TEMPLATE = """
CREATE TABLE IF NOT EXISTS {table_name} (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    embedding vector,
    embedding_provider TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    embedding_generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_url TEXT NOT NULL,
    source_domain TEXT,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER,
    chunk_size INTEGER,
    document_id UUID,
    document_title TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scraper_version TEXT,
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_content_source UNIQUE(content_hash, source_url, chunk_index)
);
"""

def create_embedding_table(conn, provider, model, dimension):
    safe_model = model.replace("/", "_").replace("-", "_").replace(".", "_")
    table_name = f"document_chunks_{provider}_{safe_model}"
    with conn.cursor() as cur:
        cur.execute(TABLE_TEMPLATE.format(table_name=table_name))
        print(f"Created table: {table_name}")
    return table_name

def main():
    if len(sys.argv) < 5:
        print("Usage: python manage_embedding_tables.py <db_url> <provider> <model> <dimension>")
        sys.exit(1)
    db_url, provider, model, dimension = sys.argv[1:5]
    conn = psycopg2.connect(db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    create_embedding_table(conn, provider, model, int(dimension))
    conn.close()

if __name__ == "__main__":
    main()

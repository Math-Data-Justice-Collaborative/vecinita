"""
Script to migrate document chunks from one embedding model to another.
"""
import os
import sys
from typing import Optional
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'shared', 'src'))
from providers import get_provider


def migrate_chunks_to_new_model(
    database_url: str,
    source_table: str,
    target_provider: str,
    target_model: str,
    batch_size: int = 100,
    limit: Optional[int] = None
):
    """
    Migrate chunks from source table to new embedding model.
    
    Example:
        migrate_chunks_to_new_model(
            db_url,
            "document_chunks_huggingface_miniLMv2",
            "openai",
            "text-embedding-3-small"
        )
    """
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    try:
        # Get provider
        provider = get_provider(target_provider)
        dimensions = provider.get_dimensions(target_model)

        # Create target table name
        safe_model = target_model.replace("/", "_").replace("-", "_").replace(".", "_")
        target_table = f"document_chunks_{target_provider}_{safe_model}"

        # Create table if not exists
        print(f"Creating target table: {target_table}")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {target_table} (
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
                metadata JSONB DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                CONSTRAINT unique_content_source UNIQUE(content_hash, source_url, chunk_index)
            );
        """)
        conn.commit()

        # Fetch chunks from source table
        query = f"SELECT id, content, source_url, chunk_index, total_chunks, chunk_size, document_id, document_title, scraped_at, scraper_version, metadata FROM {source_table}"
        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        chunks = cur.fetchall()
        print(f"Found {len(chunks)} chunks to migrate")

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk[1] for chunk in batch]  # content

            print(f"Processing batch {i // batch_size + 1}/{(len(chunks) + batch_size - 1) // batch_size}")

            # Generate embeddings
            embeddings = provider.embed_texts(texts, target_model)

            # Insert into target table
            insert_query = f"""
                INSERT INTO {target_table} 
                (id, content, content_hash, embedding, embedding_provider, embedding_model, 
                 embedding_dimensions, source_url, chunk_index, total_chunks, chunk_size, 
                 document_id, document_title, scraped_at, scraper_version, is_processed, 
                 processing_status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_hash, source_url, chunk_index) DO NOTHING
            """

            batch_data = []
            for chunk, embedding in zip(batch, embeddings):
                import hashlib
                content_hash = hashlib.sha256(chunk[1].encode()).hexdigest()
                batch_data.append((
                    chunk[0],  # id
                    chunk[1],  # content
                    content_hash,
                    str(embedding),  # embedding as string for pgvector
                    target_provider,
                    target_model,
                    dimensions,
                    chunk[2],  # source_url
                    chunk[3],  # chunk_index
                    chunk[4],  # total_chunks
                    chunk[5],  # chunk_size
                    chunk[6],  # document_id
                    chunk[7],  # document_title
                    chunk[8],  # scraped_at
                    chunk[9],  # scraper_version
                    True,  # is_processed
                    'completed',  # processing_status
                    chunk[10]  # metadata
                ))

            execute_batch(cur, insert_query, batch_data, page_size=50)
            conn.commit()
            print(f"  → Inserted {len(batch_data)} chunks")

        # Update embedding_metadata
        cur.execute("""
            INSERT INTO embedding_metadata (provider, model, dimension, table_name, is_active, first_used_at)
            VALUES (%s, %s, %s, %s, FALSE, NOW())
            ON CONFLICT (provider, model) DO UPDATE SET last_used_at = NOW();
        """, (target_provider, target_model, dimensions, target_table))
        conn.commit()

        print(f"✓ Migration completed: {len(chunks)} chunks migrated to {target_table}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python migrate_model.py <db_url> <source_table> <target_provider> <target_model>")
        print("Example: python migrate_model.py postgres://... document_chunks_huggingface_miniLMv2 openai text-embedding-3-small")
        sys.exit(1)

    db_url, source_table, target_provider, target_model = sys.argv[1:5]
    migrate_chunks_to_new_model(db_url, source_table, target_provider, target_model)

-- Render Postgres parity SQL for Vecinita vector cutover.
-- Scope: pgvector + loader/uploader-required tables.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) GENERATED ALWAYS AS (encode(digest(content::bytea, 'sha256'), 'hex')) STORED,
    embedding vector(384),
    source_url TEXT NOT NULL,
    source_domain TEXT GENERATED ALWAYS AS (
        CASE
            WHEN source_url LIKE 'http://%' THEN split_part(split_part(source_url, 'http://', 2), '/', 1)
            WHEN source_url LIKE 'https://%' THEN split_part(split_part(source_url, 'https://', 2), '/', 1)
            ELSE source_url
        END
    ) STORED,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER,
    chunk_size INTEGER GENERATED ALWAYS AS (char_length(content)) STORED,
    document_id UUID,
    document_title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    scraped_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status TEXT DEFAULT 'pending',
    error_message TEXT,
    CONSTRAINT unique_content_source UNIQUE(content_hash, source_url, chunk_index)
);

CREATE TABLE IF NOT EXISTS processing_queue (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    chunks_processed INTEGER DEFAULT 0,
    total_chunks INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_document_chunks_source_url ON document_chunks(source_url);
CREATE INDEX IF NOT EXISTS idx_document_chunks_processed ON document_chunks(is_processed, processing_status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_created ON processing_queue(created_at DESC);

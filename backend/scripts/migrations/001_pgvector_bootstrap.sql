-- =============================================================================
-- Migration 001: pgvector bootstrap — extensions + tables + indexes
-- Target: Render Postgres 16 (pgvector pre-installed as an extension)
-- Idempotent: all statements use IF NOT EXISTS / OR REPLACE
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID    DEFAULT uuid_generate_v4() PRIMARY KEY,
    content         TEXT    NOT NULL,
    content_hash    VARCHAR(64)
                    GENERATED ALWAYS AS (encode(sha256(content::bytea), 'hex')) STORED,
    embedding       vector(384),
    source_url      TEXT    NOT NULL,
    source_domain   TEXT    GENERATED ALWAYS AS (
                        CASE
                            WHEN source_url LIKE 'http://%'  THEN split_part(split_part(source_url, 'http://',  2), '/', 1)
                            WHEN source_url LIKE 'https://%' THEN split_part(split_part(source_url, 'https://', 2), '/', 1)
                            ELSE source_url
                        END
                    ) STORED,
    chunk_index     INTEGER NOT NULL,
    total_chunks    INTEGER,
    chunk_size      INTEGER GENERATED ALWAYS AS (char_length(content)) STORED,
    document_id     UUID,
    document_title  TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    scraped_at      TIMESTAMP WITH TIME ZONE,
    metadata        JSONB   DEFAULT '{}'::jsonb,
    is_processed    BOOLEAN DEFAULT FALSE,
    processing_status TEXT  DEFAULT 'pending',
    error_message   TEXT,
    CONSTRAINT unique_content_source UNIQUE (content_hash, source_url, chunk_index)
);

CREATE TABLE IF NOT EXISTS sources (
    id              UUID    DEFAULT uuid_generate_v4() PRIMARY KEY,
    url             TEXT    UNIQUE NOT NULL,
    domain          TEXT    GENERATED ALWAYS AS (
                        CASE
                            WHEN url LIKE 'http://%'  THEN split_part(split_part(url, 'http://',  2), '/', 1)
                            WHEN url LIKE 'https://%' THEN split_part(split_part(url, 'https://', 2), '/', 1)
                            ELSE url
                        END
                    ) STORED,
    title           TEXT,
    description     TEXT,
    author          TEXT,
    published_date  DATE,
    first_scraped_at  TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    last_scraped_at   TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    scrape_count    INTEGER DEFAULT 1,
    is_active       BOOLEAN DEFAULT TRUE,
    reliability_score DECIMAL(3,2) DEFAULT 1.0
                    CHECK (reliability_score >= 0 AND reliability_score <= 1),
    total_chunks    INTEGER DEFAULT 0,
    total_characters INTEGER DEFAULT 0,
    metadata        JSONB   DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

CREATE TABLE IF NOT EXISTS processing_queue (
    id              UUID    DEFAULT uuid_generate_v4() PRIMARY KEY,
    file_path       TEXT    NOT NULL,
    file_size       BIGINT,
    status          TEXT    DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    error_message   TEXT,
    chunks_processed INTEGER DEFAULT 0,
    total_chunks    INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

CREATE TABLE IF NOT EXISTS search_queries (
    id              UUID    DEFAULT uuid_generate_v4() PRIMARY KEY,
    query_text      TEXT    NOT NULL,
    query_embedding vector(384),
    results_count   INTEGER,
    top_result_id   UUID    REFERENCES document_chunks(id),
    similarity_score REAL,
    user_feedback   TEXT,
    search_metadata JSONB   DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

-- Primary vector similarity search index (IVFFlat cosine)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- document_chunks performance indexes
CREATE INDEX IF NOT EXISTS idx_document_chunks_source_url    ON document_chunks (source_url);
CREATE INDEX IF NOT EXISTS idx_document_chunks_source_domain ON document_chunks (source_domain);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id   ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_created_at    ON document_chunks (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_chunks_is_processed  ON document_chunks (is_processed);

-- GIN indexes
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin  ON document_chunks USING gin (metadata);
CREATE INDEX IF NOT EXISTS idx_sources_metadata_gin          ON sources         USING gin (metadata);

-- Full-text search
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_gin
    ON document_chunks USING gin (to_tsvector('english', content));

-- Trigram partial matching
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_trgm
    ON document_chunks USING gin (content gin_trgm_ops);

-- sources indexes
CREATE INDEX IF NOT EXISTS idx_sources_domain       ON sources (domain);
CREATE INDEX IF NOT EXISTS idx_sources_is_active    ON sources (is_active);
CREATE INDEX IF NOT EXISTS idx_sources_last_scraped ON sources (last_scraped_at DESC);

-- processing_queue indexes
CREATE INDEX IF NOT EXISTS idx_processing_queue_status  ON processing_queue (status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_created ON processing_queue (created_at DESC);

-- search_queries index
CREATE INDEX IF NOT EXISTS idx_search_queries_created ON search_queries (created_at DESC);

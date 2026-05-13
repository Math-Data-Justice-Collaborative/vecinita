-- One-shot schema for Render Postgres (gateway + Modal scraper control plane).
--
-- Use when MODAL_SCRAPER_PERSIST_VIA_GATEWAY is enabled on the gateway and
-- DATABASE_URL points at Render-managed Postgres. Do NOT use 001_create_scraping_jobs.sql
-- as-is on Render: it enables RLS policies that reference auth.uid() (Supabase-only).
--
-- Apply from a trusted shell. From outside Render, use the Postgres **External** connection
-- string (host …REGION-postgres.render.com); internal hostnames dpg-… alone do not resolve.
-- From Render Shell on a service, the Internal URL works. Use SSL (e.g. sslmode=require):
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f services/scraper/migrations/render_gateway_scraper_schema.sql
--
-- Or: ./services/scraper/migrations/apply_render_gateway_schema.sh
--
-- Idempotent: safe to re-run.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

-- scraping_jobs (matches services/scraper/migrations/001_create_scraping_jobs.sql structure; no RLS)
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    url TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    crawl_config JSONB,
    chunking_config JSONB,
    metadata JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scraping_jobs_user_id ON scraping_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_at ON scraping_jobs(created_at);

-- Pipeline tables (from 002_create_content_tables.sql)
CREATE TABLE IF NOT EXISTS crawled_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    raw_content_hash VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    error_message TEXT,
    crawled_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(job_id, url)
);

CREATE INDEX IF NOT EXISTS idx_crawled_urls_job_id ON crawled_urls(job_id);
CREATE INDEX IF NOT EXISTS idx_crawled_urls_status ON crawled_urls(status);

CREATE TABLE IF NOT EXISTS extracted_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crawled_url_id UUID NOT NULL REFERENCES crawled_urls(id) ON DELETE CASCADE,
    content_type VARCHAR NOT NULL,
    raw_content TEXT NOT NULL,
    processing_status VARCHAR NOT NULL DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_extracted_content_crawled_url_id ON extracted_content(crawled_url_id);
CREATE INDEX IF NOT EXISTS idx_extracted_content_processing_status ON extracted_content(processing_status);

CREATE TABLE IF NOT EXISTS processed_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_content_id UUID NOT NULL REFERENCES extracted_content(id) ON DELETE CASCADE,
    markdown_content TEXT NOT NULL,
    tables_json TEXT,
    metadata_json JSONB
);

CREATE INDEX IF NOT EXISTS idx_processed_documents_extracted_content_id ON processed_documents(extracted_content_id);

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processed_doc_id UUID NOT NULL REFERENCES processed_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    position INTEGER NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    semantic_boundary BOOLEAN NOT NULL DEFAULT false,
    raw_text TEXT,
    enriched_text TEXT
);

CREATE INDEX IF NOT EXISTS idx_chunks_processed_doc_id ON chunks(processed_doc_id);

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding_vector vector(384),
    model_name VARCHAR NOT NULL DEFAULT 'BAAI/bge-small-en-v1.5',
    dimensions INTEGER NOT NULL DEFAULT 384,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_job_id ON embeddings(job_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model_name ON embeddings(model_name);

CREATE UNIQUE INDEX IF NOT EXISTS uq_embeddings_chunk_id_model_name
    ON embeddings (chunk_id, model_name);

COMMIT;

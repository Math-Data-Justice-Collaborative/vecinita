-- Migration: Create content tables for pipeline stages

-- crawled_urls table: stores raw crawled URL data
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

CREATE INDEX idx_crawled_urls_job_id ON crawled_urls(job_id);
CREATE INDEX idx_crawled_urls_status ON crawled_urls(status);

-- extracted_content table: raw extracted content before processing
CREATE TABLE IF NOT EXISTS extracted_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crawled_url_id UUID NOT NULL REFERENCES crawled_urls(id) ON DELETE CASCADE,
    content_type VARCHAR NOT NULL,
    raw_content TEXT NOT NULL,
    processing_status VARCHAR NOT NULL DEFAULT 'pending'
);

CREATE INDEX idx_extracted_content_crawled_url_id ON extracted_content(crawled_url_id);
CREATE INDEX idx_extracted_content_processing_status ON extracted_content(processing_status);

-- processed_documents table: after Docling processing
CREATE TABLE IF NOT EXISTS processed_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_content_id UUID NOT NULL REFERENCES extracted_content(id) ON DELETE CASCADE,
    markdown_content TEXT NOT NULL,
    tables_json TEXT,
    metadata_json JSONB
);

CREATE INDEX idx_processed_documents_extracted_content_id ON processed_documents(extracted_content_id);

-- chunks table: semantic chunks of processed content
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processed_doc_id UUID NOT NULL REFERENCES processed_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    position INTEGER NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    semantic_boundary BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_chunks_processed_doc_id ON chunks(processed_doc_id);

-- embeddings table: final embeddings with metadata
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    chunk_id UUID NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding_vector vector(384),
    model_name VARCHAR NOT NULL DEFAULT 'BAAI/bge-small-en-v1.5',
    dimensions INTEGER NOT NULL DEFAULT 384,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_embeddings_job_id ON embeddings(job_id);
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model_name ON embeddings(model_name);

-- Enable vector search (pgvector extension)
-- This should be run separately: CREATE EXTENSION IF NOT EXISTS vector;

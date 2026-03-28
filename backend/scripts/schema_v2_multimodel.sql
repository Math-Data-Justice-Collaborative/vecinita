-- Multi-model/multi-provider schema extension for Vecinita

-- Embedding metadata registry
CREATE TABLE IF NOT EXISTS embedding_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    dimension INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_used_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    chunks_count INTEGER DEFAULT 0,
    total_characters BIGINT DEFAULT 0,
    config JSONB DEFAULT '{}'::jsonb
);

-- Example: document_chunks_huggingface_miniLMv2
-- Use a script to create a new table for each provider/model combo
-- Table template:
-- CREATE TABLE document_chunks_{provider}_{model_safe_name} (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     content TEXT NOT NULL,
--     content_hash VARCHAR(64),
--     embedding vector,
--     embedding_provider TEXT NOT NULL,
--     embedding_model TEXT NOT NULL,
--     embedding_dimensions INTEGER NOT NULL,
--     embedding_generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--     source_url TEXT NOT NULL,
--     source_domain TEXT,
--     chunk_index INTEGER NOT NULL,
--     total_chunks INTEGER,
--     chunk_size INTEGER,
--     document_id UUID,
--     document_title TEXT,
--     scraped_at TIMESTAMP WITH TIME ZONE,
--     last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--     scraper_version TEXT,
--     is_processed BOOLEAN DEFAULT FALSE,
--     processing_status TEXT DEFAULT 'pending',
--     error_message TEXT,
--     metadata JSONB DEFAULT '{}'::jsonb,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--     CONSTRAINT unique_content_source UNIQUE(content_hash, source_url, chunk_index)
-- );

-- Add last_scraped_at and last_scrape_by_model to document_sources
ALTER TABLE IF EXISTS document_sources ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE IF EXISTS document_sources ADD COLUMN IF NOT EXISTS last_scrape_by_model JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS document_sources ADD COLUMN IF NOT EXISTS current_embedding_model TEXT;

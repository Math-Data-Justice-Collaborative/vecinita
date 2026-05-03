-- Vecinita Vector Database Installation
-- Run these commands in order against your PostgreSQL database

-- ============================================
-- STEP 1: Enable Required Extensions
-- ============================================
-- Run this first and wait for it to complete:

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- STEP 2: Create Main Tables
-- ============================================
-- After extensions are enabled, run this:

-- Drop tables if they exist (careful in production!)
-- Uncomment these lines if you want to start fresh:
-- DROP TABLE IF EXISTS document_chunks CASCADE;
-- DROP TABLE IF EXISTS sources CASCADE;
-- DROP TABLE IF EXISTS processing_queue CASCADE;
-- DROP TABLE IF EXISTS search_queries CASCADE;

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) GENERATED ALWAYS AS (encode(sha256(content::bytea), 'hex')) STORED,
    embedding vector(384),
    source_url TEXT NOT NULL,
    source_domain TEXT GENERATED ALWAYS AS (
        CASE 
            WHEN source_url LIKE 'http://%' THEN 
                split_part(split_part(source_url, 'http://', 2), '/', 1)
            WHEN source_url LIKE 'https://%' THEN 
                split_part(split_part(source_url, 'https://', 2), '/', 1)
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

-- Create sources table
CREATE TABLE IF NOT EXISTS sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain TEXT GENERATED ALWAYS AS (
        CASE 
            WHEN url LIKE 'http://%' THEN 
                split_part(split_part(url, 'http://', 2), '/', 1)
            WHEN url LIKE 'https://%' THEN 
                split_part(split_part(url, 'https://', 2), '/', 1)
            ELSE url
        END
    ) STORED,
    title TEXT,
    description TEXT,
    author TEXT,
    published_date DATE,
    first_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    last_scraped_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    scrape_count INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    reliability_score DECIMAL(3,2) DEFAULT 1.0 CHECK (reliability_score >= 0 AND reliability_score <= 1),
    total_chunks INTEGER DEFAULT 0,
    total_characters INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create processing_queue table
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

-- Create search_queries table
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    query_text TEXT NOT NULL,
    query_embedding vector(384),
    results_count INTEGER,
    top_result_id UUID REFERENCES document_chunks(id),
    similarity_score REAL,
    user_feedback TEXT,
    search_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- ============================================
-- STEP 3: Create Indexes
-- ============================================
-- Run this after tables are created:

-- Vector similarity search index (important!)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Other performance indexes
CREATE INDEX IF NOT EXISTS idx_document_chunks_source_url ON document_chunks(source_url);
CREATE INDEX IF NOT EXISTS idx_document_chunks_source_domain ON document_chunks(source_domain);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_created_at ON document_chunks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_chunks_is_processed ON document_chunks(is_processed);
CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin ON document_chunks USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_sources_metadata_gin ON sources USING gin(metadata);

-- Full text search
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_gin 
    ON document_chunks USING gin(to_tsvector('english', content));

-- Trigram index for partial matching
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_trgm 
    ON document_chunks USING gin(content gin_trgm_ops);

-- Source indexes
CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_is_active ON sources(is_active);
CREATE INDEX IF NOT EXISTS idx_sources_last_scraped ON sources(last_scraped_at DESC);

-- Queue indexes
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_created ON processing_queue(created_at DESC);

-- Search history index
CREATE INDEX IF NOT EXISTS idx_search_queries_created ON search_queries(created_at DESC);

-- ============================================
-- STEP 4: Create Functions and Triggers
-- ============================================

-- Update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers
CREATE TRIGGER update_document_chunks_updated_at 
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at 
    BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to search similar documents
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
    match_threshold REAL DEFAULT 0.3,
    match_count INTEGER DEFAULT 5,
    tag_filter TEXT[] DEFAULT NULL,
    tag_match_mode TEXT DEFAULT 'any',
    include_untagged_fallback BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    source_url TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    similarity DOUBLE PRECISION
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
        AND (
            tag_filter IS NULL
            OR cardinality(tag_filter) = 0
            OR (
                (
                    LOWER(COALESCE(tag_match_mode, 'any')) = 'all'
                    AND COALESCE(dc.metadata->'tags', '[]'::jsonb) ?& tag_filter
                )
                OR (
                    LOWER(COALESCE(tag_match_mode, 'any')) <> 'all'
                    AND COALESCE(dc.metadata->'tags', '[]'::jsonb) ?| tag_filter
                )
                OR (
                    include_untagged_fallback = TRUE
                    AND jsonb_array_length(COALESCE(dc.metadata->'tags', '[]'::jsonb)) = 0
                )
            )
        )
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to update source statistics
CREATE OR REPLACE FUNCTION update_source_statistics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sources
    SET 
        total_chunks = (
            SELECT COUNT(*) 
            FROM document_chunks 
            WHERE source_url = NEW.source_url
        ),
        total_characters = (
            SELECT SUM(chunk_size) 
            FROM document_chunks 
            WHERE source_url = NEW.source_url
        ),
        last_scraped_at = COALESCE(NEW.scraped_at, TIMEZONE('utc', NOW()))
    WHERE url = NEW.source_url;
    
    INSERT INTO sources (url)
    VALUES (NEW.source_url)
    ON CONFLICT (url) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply source statistics trigger
CREATE TRIGGER update_source_stats_on_insert
    AFTER INSERT ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION update_source_statistics();

-- ============================================
-- STEP 5: Create Views
-- ============================================

CREATE OR REPLACE VIEW v_chunk_statistics AS
SELECT 
    source_domain,
    COUNT(*) as chunk_count,
    AVG(chunk_size) as avg_chunk_size,
    SUM(chunk_size) as total_size,
    COUNT(DISTINCT document_id) as document_count,
    MAX(created_at) as latest_chunk
FROM document_chunks
GROUP BY source_domain
ORDER BY chunk_count DESC;

CREATE OR REPLACE VIEW v_processing_status AS
SELECT 
    status,
    COUNT(*) as job_count,
    SUM(chunks_processed) as total_chunks_processed,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_processing_time_seconds
FROM processing_queue
GROUP BY status;

-- ============================================
-- STEP 6: Enable Row Level Security (RLS)
-- ============================================

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_queries ENABLE ROW LEVEL SECURITY;

-- Create basic policies (adjust based on your needs)
CREATE POLICY "Enable read for all" ON document_chunks FOR SELECT USING (true);
CREATE POLICY "Enable insert for all" ON document_chunks FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for all" ON document_chunks FOR UPDATE USING (true);
CREATE POLICY "Enable read for all" ON sources FOR SELECT USING (true);
CREATE POLICY "Enable all for all" ON processing_queue FOR ALL USING (true);
CREATE POLICY "Enable insert for all" ON search_queries FOR INSERT WITH CHECK (true);

-- ============================================
-- STEP 7: Grant Permissions
-- ============================================

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- After installation, run these to verify:

-- Check if tables exist:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('document_chunks', 'sources', 'processing_queue', 'search_queries');

-- Check if vector extension is working:
SELECT '[1,2,3]'::vector AS test_vector;

-- Test insert (will create a test record):
INSERT INTO document_chunks (content, source_url, chunk_index)
VALUES ('Test chunk for Vecinita', 'https://test.example.com', 1)
RETURNING id;

-- =============================================================================
-- Migration 002: RPC functions, triggers, views
-- Target: Render Postgres 16 (pgvector)
-- Idempotent: all statements use CREATE OR REPLACE
-- Depends on: 001_pgvector_bootstrap.sql
-- =============================================================================

-- ---------------------------------------------------------------------------
-- updated_at maintenance trigger
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc', NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Idempotent trigger creation via DO block
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_document_chunks_updated_at'
    ) THEN
        CREATE TRIGGER update_document_chunks_updated_at
            BEFORE UPDATE ON document_chunks
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_sources_updated_at'
    ) THEN
        CREATE TRIGGER update_sources_updated_at
            BEFORE UPDATE ON sources
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- source statistics maintenance trigger
-- ---------------------------------------------------------------------------

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
            SELECT COALESCE(SUM(chunk_size), 0)
            FROM document_chunks
            WHERE source_url = NEW.source_url
        ),
        last_scraped_at = COALESCE(NEW.scraped_at, TIMEZONE('utc', NOW()))
    WHERE url = NEW.source_url;

    -- Auto-create source record if missing
    INSERT INTO sources (url)
    VALUES (NEW.source_url)
    ON CONFLICT (url) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = 'update_source_stats_on_insert'
    ) THEN
        CREATE TRIGGER update_source_stats_on_insert
            AFTER INSERT ON document_chunks
            FOR EACH ROW EXECUTE FUNCTION update_source_statistics();
    END IF;
END;
$$;

-- ---------------------------------------------------------------------------
-- Vector similarity search RPC
-- Supports tag filtering with 'any'/'all' mode and untagged fallback
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding          vector,
    match_threshold          REAL    DEFAULT 0.3,
    match_count              INTEGER DEFAULT 5,
    tag_filter               TEXT[]  DEFAULT NULL,
    tag_match_mode           TEXT    DEFAULT 'any',
    include_untagged_fallback BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    id            UUID,
    content       TEXT,
    source_url    TEXT,
    chunk_index   INTEGER,
    metadata      JSONB,
    similarity    DOUBLE PRECISION
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
                    AND COALESCE(dc.metadata -> 'tags', '[]'::jsonb) ?& tag_filter
                )
                OR (
                    LOWER(COALESCE(tag_match_mode, 'any')) <> 'all'
                    AND COALESCE(dc.metadata -> 'tags', '[]'::jsonb) ?| tag_filter
                )
                OR (
                    include_untagged_fallback = TRUE
                    AND jsonb_array_length(COALESCE(dc.metadata -> 'tags', '[]'::jsonb)) = 0
                )
            )
        )
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_chunk_statistics AS
SELECT
    source_domain,
    COUNT(*)                           AS chunk_count,
    AVG(chunk_size)                    AS avg_chunk_size,
    SUM(chunk_size)                    AS total_size,
    COUNT(DISTINCT document_id)        AS document_count,
    MAX(created_at)                    AS latest_chunk
FROM document_chunks
GROUP BY source_domain
ORDER BY chunk_count DESC;

CREATE OR REPLACE VIEW v_processing_status AS
SELECT
    status,
    COUNT(*)                           AS job_count,
    SUM(chunks_processed)              AS total_chunks_processed,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) AS avg_processing_time_seconds
FROM processing_queue
GROUP BY status;

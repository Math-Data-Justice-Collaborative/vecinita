-- Admin Helper Functions Migration
-- Adds RPC functions for admin statistics and operations
-- Run this after the session isolation migration

-- ============================================================================
-- Function: get_unique_sources_count
-- Returns the count of unique source URLs in document_chunks
-- ============================================================================

CREATE OR REPLACE FUNCTION get_unique_sources_count()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    source_count INTEGER;
BEGIN
    SELECT COUNT(DISTINCT source) INTO source_count
    FROM document_chunks;
    
    RETURN COALESCE(source_count, 0);
END;
$$;

-- ============================================================================
-- Function: get_average_chunk_size
-- Returns the average character length of content in document_chunks
-- ============================================================================

CREATE OR REPLACE FUNCTION get_average_chunk_size()
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
DECLARE
    avg_size FLOAT;
BEGIN
    SELECT AVG(LENGTH(content)) INTO avg_size
    FROM document_chunks
    WHERE content IS NOT NULL;
    
    RETURN COALESCE(avg_size, 0.0);
END;
$$;

-- ============================================================================
-- Function: get_database_size
-- Returns the total size of the database in bytes
-- ============================================================================

CREATE OR REPLACE FUNCTION get_database_size()
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    db_size BIGINT;
BEGIN
    -- Get current database size
    SELECT pg_database_size(current_database()) INTO db_size;
    
    RETURN COALESCE(db_size, 0);
END;
$$;

-- ============================================================================
-- Function: get_sources_with_counts
-- Returns list of unique sources with chunk counts and timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION get_sources_with_counts()
RETURNS TABLE (
    url TEXT,
    chunk_count BIGINT,
    created_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        source AS url,
        COUNT(*) AS chunk_count,
        MIN(document_chunks.created_at) AS created_at,
        MAX(document_chunks.updated_at) AS last_updated
    FROM document_chunks
    WHERE source IS NOT NULL
    GROUP BY source
    ORDER BY chunk_count DESC;
END;
$$;

-- ============================================================================
-- Function: count_session_documents (if not exists from session isolation)
-- Returns count of documents for a specific session
-- ============================================================================

CREATE OR REPLACE FUNCTION count_session_documents(session_filter TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    doc_count INTEGER;
BEGIN
    IF session_filter IS NULL OR session_filter = '' THEN
        -- Count all documents
        SELECT COUNT(*) INTO doc_count FROM document_chunks;
    ELSE
        -- Count documents for specific session
        SELECT COUNT(*) INTO doc_count 
        FROM document_chunks 
        WHERE session_id = session_filter;
    END IF;
    
    RETURN COALESCE(doc_count, 0);
END;
$$;

-- ============================================================================
-- Function: list_active_sessions
-- Returns list of active sessions with document counts
-- ============================================================================

CREATE OR REPLACE FUNCTION list_active_sessions()
RETURNS TABLE (
    session_id TEXT,
    document_count BIGINT,
    first_document TIMESTAMP WITH TIME ZONE,
    last_document TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        document_chunks.session_id,
        COUNT(*) AS document_count,
        MIN(document_chunks.created_at) AS first_document,
        MAX(document_chunks.created_at) AS last_document
    FROM document_chunks
    WHERE document_chunks.session_id IS NOT NULL
    GROUP BY document_chunks.session_id
    ORDER BY last_document DESC;
END;
$$;

-- ============================================================================
-- Grant execute permissions to service role
-- ============================================================================

GRANT EXECUTE ON FUNCTION get_unique_sources_count() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_average_chunk_size() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_database_size() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_sources_with_counts() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION count_session_documents(TEXT) TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION list_active_sessions() TO anon, authenticated, service_role;

-- ============================================================================
-- Verification queries
-- ============================================================================

-- Test the functions (uncomment to run manually):
-- SELECT get_unique_sources_count();
-- SELECT get_average_chunk_size();
-- SELECT get_database_size();
-- SELECT * FROM get_sources_with_counts();
-- SELECT count_session_documents(NULL);
-- SELECT * FROM list_active_sessions();

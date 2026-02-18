-- Migration: Add Session Isolation for Single-Tenant Data Security
-- Date: 2026-02-13
-- Description: Adds session_id columns and updates RPC functions for thread-level data isolation

-- ============================================
-- STEP 1: Add session_id columns
-- ============================================

-- Add session_id to document_chunks table
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT NULL;

-- Add session_id to search_queries table  
ALTER TABLE search_queries
ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT NULL;

-- Add comments explaining the purpose
COMMENT ON COLUMN document_chunks.session_id IS 
    'Session identifier for data isolation. In single-tenant mode, used for thread/conversation isolation. NULL = publicly accessible data.';

COMMENT ON COLUMN search_queries.session_id IS
    'Session identifier linking search queries to specific conversations/threads.';

-- ============================================
-- STEP 2: Create indexes for performance
-- ============================================

-- Index for session-based filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_session 
    ON document_chunks(session_id) 
    WHERE session_id IS NOT NULL;

-- Composite index for session + processed status
CREATE INDEX IF NOT EXISTS idx_document_chunks_session_processed 
    ON document_chunks(session_id, is_processed) 
    WHERE session_id IS NOT NULL;

-- Index for search queries by session
CREATE INDEX IF NOT EXISTS idx_search_queries_session 
    ON search_queries(session_id)
    WHERE session_id IS NOT NULL;

-- ============================================
-- STEP 3: Update search_similar_documents function
-- ============================================

-- Enhanced version with optional session filtering
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
    match_threshold REAL DEFAULT 0.3,
    match_count INTEGER DEFAULT 5,
    session_filter TEXT DEFAULT NULL
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
        -- Session filtering: NULL session_filter = all public data (session_id IS NULL)
        -- Specific session_filter = only that session's data OR public data
        AND (
            session_filter IS NULL AND dc.session_id IS NULL  -- Public data only
            OR session_filter IS NOT NULL AND (dc.session_id = session_filter OR dc.session_id IS NULL)  -- Session + public
        )
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION search_similar_documents IS 
    'Search for similar documents with optional session isolation. 
    - session_filter=NULL: Returns only public data (session_id IS NULL)
    - session_filter=<value>: Returns session-specific data + public data';

-- ============================================
-- STEP 4: Create strict session-only search function
-- ============================================

-- This version ONLY returns data for the specified session (no public fallback)
CREATE OR REPLACE FUNCTION search_similar_documents_by_session(
    query_embedding vector,
    session_filter TEXT,
    match_threshold REAL DEFAULT 0.3,
    match_count INTEGER DEFAULT 5
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
    IF session_filter IS NULL THEN
        RAISE EXCEPTION 'session_filter cannot be NULL for strict session search';
    END IF;

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
        AND dc.session_id = session_filter  -- STRICT: Only this session's data
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION search_similar_documents_by_session IS
    'Strict session-isolated search. Only returns documents explicitly tagged with the given session_id. Does not include public data.';

-- ============================================
-- STEP 5: Create helper functions for session management
-- ============================================

-- Function to count documents in a session
CREATE OR REPLACE FUNCTION count_session_documents(session_filter TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    doc_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO doc_count
    FROM document_chunks
    WHERE session_id = session_filter;
    
    RETURN doc_count;
END;
$$;

COMMENT ON FUNCTION count_session_documents IS 
    'Count how many document chunks belong to a specific session';

-- Function to list all active sessions
CREATE OR REPLACE FUNCTION list_active_sessions()
RETURNS TABLE (
    session_id TEXT,
    document_count BIGINT,
    first_document_date TIMESTAMP WITH TIME ZONE,
    last_document_date TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.session_id,
        COUNT(*) AS document_count,
        MIN(dc.created_at) AS first_document_date,
        MAX(dc.created_at) AS last_document_date
    FROM document_chunks dc
    WHERE dc.session_id IS NOT NULL
    GROUP BY dc.session_id
    ORDER BY MAX(dc.created_at) DESC;
END;
$$;

COMMENT ON FUNCTION list_active_sessions IS
    'List all sessions that have documents, with counts and date ranges';

-- ============================================
-- STEP 6: Create cleanup function for old sessions
-- ============================================

-- Function to delete all data for a session (admin/cleanup)
CREATE OR REPLACE FUNCTION delete_session_data(session_filter TEXT)
RETURNS TABLE (
    chunks_deleted INTEGER,
    queries_deleted INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    chunks_count INTEGER;
    queries_count INTEGER;
BEGIN
    -- Delete document chunks
    WITH deleted_chunks AS (
        DELETE FROM document_chunks
        WHERE session_id = session_filter
        RETURNING id
    )
    SELECT COUNT(*) INTO chunks_count FROM deleted_chunks;
    
    -- Delete search queries
    WITH deleted_queries AS (
        DELETE FROM search_queries
        WHERE session_id = session_filter
        RETURNING id
    )
    SELECT COUNT(*) INTO queries_count FROM deleted_queries;
    
    RETURN QUERY SELECT chunks_count, queries_count;
END;
$$;

COMMENT ON FUNCTION delete_session_data IS
    'Delete all document chunks and search queries for a specific session. Use with caution.';

-- ============================================
-- Migration Complete
-- ============================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Session isolation migration completed successfully';
    RAISE NOTICE 'Added session_id columns to: document_chunks, search_queries';
    RAISE NOTICE 'Created indexes: idx_document_chunks_session, idx_document_chunks_session_processed, idx_search_queries_session';
    RAISE NOTICE 'Updated functions: search_similar_documents (now supports session_filter)';
    RAISE NOTICE 'New functions: search_similar_documents_by_session, count_session_documents, list_active_sessions, delete_session_data';
END $$;

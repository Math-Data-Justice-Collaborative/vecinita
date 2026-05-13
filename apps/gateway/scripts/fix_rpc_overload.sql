-- Fix for "Could not choose the best candidate function" error
-- This script drops all versions of search_similar_documents and recreates 
-- a single canonical version with REAL type (matches schema_install.sql)

-- ============================================
-- STEP 1: Drop ALL versions of the function
-- ============================================
-- This removes both REAL and DOUBLE PRECISION versions
DROP FUNCTION IF EXISTS search_similar_documents(vector, DOUBLE PRECISION, INTEGER);
DROP FUNCTION IF EXISTS search_similar_documents(vector, REAL, INTEGER);

-- ============================================
-- STEP 2: Create the canonical version
-- ============================================
-- Using REAL for match_threshold (matches schema_install.sql line 179)
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
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
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================
-- VERIFICATION
-- ============================================
-- Check that only ONE version exists
SELECT 
    p.parameter_name,
    p.data_type,
    p.parameter_mode
FROM information_schema.routines r
JOIN information_schema.parameters p 
    ON r.specific_name = p.specific_name
WHERE r.routine_schema = 'public'
    AND r.routine_name = 'search_similar_documents'
ORDER BY p.ordinal_position;

-- Expected output:
-- Should show exactly ONE function with parameters:
-- - query_embedding (vector)
-- - match_threshold (real)  
-- - match_count (integer)

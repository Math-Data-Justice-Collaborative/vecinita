-- Resolve RPC overloads and expose a safe graphql_public wrapper
--
-- Why this script:
-- 1) Keep exactly one canonical public.search_similar_documents(vector, real, integer)
-- 2) Expose an RPC callable from PostgREST when only graphql_public is exposed
-- 3) Preserve least-privilege grants

BEGIN;

CREATE SCHEMA IF NOT EXISTS graphql_public;

-- ============================================================
-- STEP 1: Remove overload conflicts in public
-- ============================================================
DROP FUNCTION IF EXISTS public.search_similar_documents(vector, double precision, integer);
DROP FUNCTION IF EXISTS public.search_similar_documents(vector, real, integer);

-- ============================================================
-- STEP 2: Canonical public function (REAL threshold)
-- ============================================================
CREATE OR REPLACE FUNCTION public.search_similar_documents(
  query_embedding vector,
  match_threshold real DEFAULT 0.3,
  match_count integer DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  content text,
  source_url text,
  chunk_index integer,
  metadata jsonb,
  similarity double precision
)
LANGUAGE plpgsql
STABLE
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
  FROM public.document_chunks dc
  WHERE dc.embedding IS NOT NULL
    AND COALESCE(dc.is_processed, false) = true
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ============================================================
-- STEP 3: graphql_public wrapper for PostgREST RPC
--
-- IMPORTANT:
-- - PostgREST currently resolves /rpc/search_similar_documents in graphql_public.
-- - This wrapper keeps the same vector signature expected by backend db_search.
-- ============================================================
DROP FUNCTION IF EXISTS graphql_public.search_similar_documents(vector, real, integer);

CREATE OR REPLACE FUNCTION graphql_public.search_similar_documents(
  query_embedding vector,
  match_threshold real DEFAULT 0.3,
  match_count integer DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  content text,
  source_url text,
  chunk_index integer,
  metadata jsonb,
  similarity double precision
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT *
  FROM public.search_similar_documents(query_embedding, match_threshold, match_count);
$$;

-- ============================================================
-- STEP 4: Minimal grants
-- ============================================================
REVOKE ALL ON FUNCTION public.search_similar_documents(vector, real, integer) FROM anon, authenticated;
GRANT EXECUTE ON FUNCTION graphql_public.search_similar_documents(vector, real, integer) TO anon, authenticated;

-- Optional: keep service role access explicit
GRANT EXECUTE ON FUNCTION public.search_similar_documents(vector, real, integer) TO service_role;
GRANT EXECUTE ON FUNCTION graphql_public.search_similar_documents(vector, real, integer) TO service_role;

-- ============================================================
-- STEP 5: Backfill processing flags for retrievable rows
-- ============================================================
UPDATE public.document_chunks
SET
  is_processed = true,
  processing_status = 'completed'
WHERE embedding IS NOT NULL
  AND COALESCE(is_processed, false) = false;

COMMIT;

-- ============================================================
-- VERIFICATION
-- ============================================================
-- 1) Should return one public signature (vector, real, integer)
-- 2) Should return one graphql_public wrapper signature (vector, real, integer)

SELECT
  n.nspname AS schema_name,
  p.proname AS function_name,
  pg_get_function_identity_arguments(p.oid) AS args,
  pg_get_function_result(p.oid) AS returns
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE p.proname = 'search_similar_documents'
  AND n.nspname IN ('public', 'graphql_public')
ORDER BY n.nspname, args;

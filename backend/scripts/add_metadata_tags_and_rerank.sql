-- Metadata tags + tag-restricted vector search migration

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin
    ON document_chunks USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_sources_metadata_gin
    ON sources USING gin (metadata);

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

CREATE OR REPLACE FUNCTION get_all_metadata_tags(
    limit_count INTEGER DEFAULT 100,
    tag_prefix TEXT DEFAULT NULL
)
RETURNS TABLE (tag TEXT)
LANGUAGE sql
AS $$
    WITH source_tags AS (
        SELECT DISTINCT LOWER(TRIM(value)) AS tag
        FROM sources s,
             LATERAL jsonb_array_elements_text(COALESCE(s.metadata->'tags', '[]'::jsonb)) AS value
        WHERE TRIM(value) <> ''
    ),
    chunk_tags AS (
        SELECT DISTINCT LOWER(TRIM(value)) AS tag
        FROM document_chunks d,
             LATERAL jsonb_array_elements_text(COALESCE(d.metadata->'tags', '[]'::jsonb)) AS value
        WHERE TRIM(value) <> ''
    ),
    all_tags AS (
        SELECT tag FROM source_tags
        UNION
        SELECT tag FROM chunk_tags
    )
    SELECT t.tag
    FROM all_tags t
    WHERE tag_prefix IS NULL OR t.tag ILIKE tag_prefix || '%'
    ORDER BY t.tag ASC
    LIMIT GREATEST(1, LEAST(limit_count, 500));
$$;

GRANT EXECUTE ON FUNCTION search_similar_documents(vector, REAL, INTEGER, TEXT[], TEXT, BOOLEAN)
    TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_all_metadata_tags(INTEGER, TEXT)
    TO anon, authenticated, service_role;

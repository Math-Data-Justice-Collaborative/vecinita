-- View to query chunks from all embedding models
CREATE OR REPLACE FUNCTION fn_document_chunks_latest()
RETURNS SETOF document_chunks_huggingface_miniLMv2 AS $$
DECLARE
    sql_query TEXT := '';
BEGIN
    IF to_regclass('public.document_chunks_huggingface_miniLMv2') IS NOT NULL THEN
        sql_query := sql_query || 'SELECT * FROM document_chunks_huggingface_miniLMv2';
    END IF;

    IF to_regclass('public.document_chunks_huggingface_bge_small') IS NOT NULL THEN
        IF sql_query <> '' THEN
            sql_query := sql_query || ' UNION ALL ';
        END IF;
        sql_query := sql_query || 'SELECT * FROM document_chunks_huggingface_bge_small';
    END IF;

    IF to_regclass('public.document_chunks_openai_text_embedding_3_small') IS NOT NULL THEN
        IF sql_query <> '' THEN
            sql_query := sql_query || ' UNION ALL ';
        END IF;
        sql_query := sql_query || 'SELECT * FROM document_chunks_openai_text_embedding_3_small';
    END IF;

    IF sql_query = '' THEN
        RETURN;
    END IF;

    RETURN QUERY EXECUTE sql_query;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE VIEW v_document_chunks_latest AS
SELECT * FROM fn_document_chunks_latest();

-- RPC function for searching across active embedding model
CREATE OR REPLACE FUNCTION search_similar_documents_by_model(
    query_embedding vector,
    embedding_model TEXT DEFAULT 'huggingface_miniLMv2',
    match_threshold REAL DEFAULT 0.3,
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    source_url TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    similarity REAL
) AS $$
BEGIN
    -- Dynamically build table name from model identifier
    CASE embedding_model
        WHEN 'huggingface_miniLMv2' THEN
            RETURN QUERY
            SELECT d.id, d.content, d.source_url, d.chunk_index, d.metadata,
                   1 - (d.embedding <=> query_embedding)::real as similarity
            FROM document_chunks_huggingface_miniLMv2 d
            WHERE d.is_processed = TRUE
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
        WHEN 'huggingface_bge_small' THEN
            RETURN QUERY
            SELECT d.id, d.content, d.source_url, d.chunk_index, d.metadata,
                   1 - (d.embedding <=> query_embedding)::real as similarity
            FROM document_chunks_huggingface_bge_small d
            WHERE d.is_processed = TRUE
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
        WHEN 'openai_text_embedding_3_small' THEN
            RETURN QUERY
            SELECT d.id, d.content, d.source_url, d.chunk_index, d.metadata,
                   1 - (d.embedding <=> query_embedding)::real as similarity
            FROM document_chunks_openai_text_embedding_3_small d
            WHERE d.is_processed = TRUE
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
        ELSE
            RETURN QUERY
            SELECT d.id, d.content, d.source_url, d.chunk_index, d.metadata,
                   1 - (d.embedding <=> query_embedding)::real as similarity
            FROM document_chunks_huggingface_miniLMv2 d
            WHERE d.is_processed = TRUE
            ORDER BY d.embedding <=> query_embedding
            LIMIT match_count;
    END CASE;
END;
$$ LANGUAGE plpgsql;

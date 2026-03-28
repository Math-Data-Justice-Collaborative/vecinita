-- pgTAP Test Suite: Database Functions
-- Tests verify RPC functions work correctly with sample vectors
-- Run with: supabase test db

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap;

SELECT plan(15);  -- Adjust based on number of tests

-- ============================================
-- SEARCH_SIMILAR_DOCUMENTS FUNCTION TESTS
-- ============================================

-- Test function exists
SELECT has_function('search_similar_documents', 
    ARRAY['vector', 'real', 'integer'], 
    'search_similar_documents function should exist with correct signature');

-- Test function return type
SELECT function_returns('search_similar_documents', 
    ARRAY['vector', 'real', 'integer'],
    'TABLE', 
    'function should return TABLE');

-- Create test data
INSERT INTO document_chunks (content, source_url, chunk_index, embedding, is_processed)
VALUES 
    ('Test vector one', 'https://test1.example.com', 1, '[0.1, 0.2, 0.3, 0.4]'::vector, TRUE),
    ('Test vector two', 'https://test2.example.com', 1, '[0.1, 0.2, 0.3, 0.4]'::vector, TRUE),
    ('Different vector', 'https://test3.example.com', 1, '[0.9, 0.8, 0.7, 0.6]'::vector, TRUE),
    ('Unprocessed chunk', 'https://test4.example.com', 1, '[0.1, 0.2, 0.3, 0.4]'::vector, FALSE);

-- Test search with valid vector
SELECT is(
    (SELECT COUNT(*) FROM search_similar_documents('[0.1, 0.2, 0.3, 0.4]'::vector, 0.0, 5)),
    2,
    'search_similar_documents should return 2 processed chunks with matching vector'
);

-- Test search with high threshold (should return fewer results)
SELECT is(
    (SELECT COUNT(*) FROM search_similar_documents('[0.1, 0.2, 0.3, 0.4]'::vector, 0.99, 5)),
    0,
    'search_similar_documents with high threshold should return 0 results'
);

-- Test search result structure
SELECT results_eq(
    'SELECT COUNT(DISTINCT id) FROM search_similar_documents(''[0.1, 0.2, 0.3, 0.4]''::vector, 0.0, 5)',
    'SELECT 2'::text,
    'search_similar_documents should return distinct results'
);

-- ============================================
-- UPDATE_UPDATED_AT_COLUMN TRIGGER TESTS
-- ============================================

-- Test trigger function exists
SELECT has_function('update_updated_at_column', 'update_updated_at_column trigger function should exist');

-- Insert new document and check updated_at is set
INSERT INTO sources (url)
VALUES ('https://test.example.com');

SELECT ok(
    (SELECT updated_at IS NOT NULL FROM sources WHERE url = 'https://test.example.com'),
    'updated_at should be set on sources insert'
);

-- Test update trigger sets updated_at to current time
UPDATE sources SET title = 'Updated Title' WHERE url = 'https://test.example.com';

SELECT ok(
    (SELECT updated_at > NOW() - INTERVAL '10 seconds' FROM sources WHERE url = 'https://test.example.com'),
    'updated_at should be updated on sources record update'
);

-- ============================================
-- UPDATE_SOURCE_STATISTICS TRIGGER TESTS
-- ============================================

-- Test trigger function exists
SELECT has_function('update_source_statistics', 'update_source_statistics trigger function should exist');

-- Insert chunk for a source and verify source is created with statistics
INSERT INTO document_chunks (content, source_url, chunk_index, embedding, is_processed)
VALUES ('Stat update test', 'https://stattest.example.com', 1, NULL, FALSE);

SELECT ok(
    (SELECT EXISTS(SELECT 1 FROM sources WHERE url = 'https://stattest.example.com')),
    'update_source_statistics should create source record on chunk insert'
);

SELECT is(
    (SELECT total_chunks FROM sources WHERE url = 'https://stattest.example.com'),
    1,
    'total_chunks should be updated correctly'
);

-- Finish tests
SELECT * FROM finish();

ROLLBACK;

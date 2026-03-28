-- pgTAP Test Suite: Database Constraints
-- Tests verify constraints enforce data integrity
-- Run with: supabase test db

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap;

SELECT plan(16);  -- Total number of constraint tests

-- ============================================
-- PRIMARY KEY CONSTRAINTS
-- ============================================

SELECT has_pk('document_chunks',
    'document_chunks should have primary key on id');

SELECT has_pk('sources',
    'sources should have primary key on id');

SELECT has_pk('processing_queue',
    'processing_queue should have primary key on id');

SELECT has_pk('search_queries',
    'search_queries should have primary key on id');

-- ============================================
-- UNIQUE CONSTRAINTS
-- ============================================

-- Content uniqueness (prevent duplicate chunks from same source)
SELECT has_constraint('document_chunks', 'unique_content_source',
    'document_chunks should have UNIQUE constraint on content_source');

-- URL uniqueness in sources
SELECT has_unique('sources', ARRAY['url'],
    'sources should have UNIQUE constraint on url');

-- ============================================
-- CHECK CONSTRAINTS
-- ============================================

-- Reliability score check
SELECT has_check('sources', 'sources should have CHECK constraint on reliability_score');

-- Processing queue status check
SELECT has_check('processing_queue', 'processing_queue should have CHECK constraint on status');

-- ============================================
-- NOT NULL CONSTRAINTS
-- ============================================

SELECT col_not_null('document_chunks', 'content',
    'document_chunks.content should NOT NULL');

SELECT col_not_null('document_chunks', 'source_url',
    'document_chunks.source_url should NOT NULL');

SELECT col_not_null('document_chunks', 'chunk_index',
    'document_chunks.chunk_index should NOT NULL');

SELECT col_not_null('sources', 'url',
    'sources.url should NOT NULL');

SELECT col_not_null('processing_queue', 'file_path',
    'processing_queue.file_path should NOT NULL');

-- ============================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================

-- search_queries references document_chunks
SELECT has_fk('search_queries', ARRAY['top_result_id'], 'table_name, column_info',
    'search_queries should have foreign key to document_chunks(id)');

-- Test constraint is properly configured
SELECT fk_ok(
    'search_queries', ARRAY['top_result_id'],
    'document_chunks', ARRAY['id'],
    'search_queries.top_result_id should reference document_chunks.id'
);

-- Finish tests
SELECT * FROM finish();

ROLLBACK;

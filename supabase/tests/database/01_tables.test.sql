-- pgTAP Test Suite: Table Schema Verification
-- Tests that verify the structure of all Vecinita tables
-- Run with: supabase test db

BEGIN;

-- Load pgTAP extension
CREATE EXTENSION IF NOT EXISTS pgtap;

-- Plan the number of tests (adjust as you add more)
SELECT plan(45);  -- Total number of assertions

-- ============================================
-- DOCUMENT_CHUNKS TABLE TESTS
-- ============================================

-- Test table exists
SELECT has_table('document_chunks', 'document_chunks table should exist');

-- Test columns exist with correct types
SELECT has_column('document_chunks', 'id', 'id column exists');
SELECT col_type_is('document_chunks', 'id', 'uuid', 'id should be UUID');
SELECT col_is_pk('document_chunks', 'id', 'id is primary key');

SELECT has_column('document_chunks', 'content', 'content column exists');
SELECT col_type_is('document_chunks', 'content', 'text', 'content should be TEXT');
SELECT col_not_null('document_chunks', 'content', 'content should NOT NULL');

SELECT has_column('document_chunks', 'embedding', 'embedding column exists');
SELECT col_type_is('document_chunks', 'embedding', 'vector', 'embedding should be vector type');

SELECT has_column('document_chunks', 'source_url', 'source_url column exists');
SELECT col_type_is('document_chunks', 'source_url', 'text', 'source_url should be TEXT');
SELECT col_not_null('document_chunks', 'source_url', 'source_url should NOT NULL');

SELECT has_column('document_chunks', 'source_domain', 'source_domain column exists');
SELECT col_is_generated('document_chunks', 'source_domain', 'source_domain is generated');

SELECT has_column('document_chunks', 'content_hash', 'content_hash column exists');
SELECT col_is_generated('document_chunks', 'content_hash', 'content_hash is generated (SHA256)');

SELECT has_column('document_chunks', 'chunk_index', 'chunk_index column exists');
SELECT col_type_is('document_chunks', 'chunk_index', 'integer', 'chunk_index should be INTEGER');
SELECT col_not_null('document_chunks', 'chunk_index', 'chunk_index should NOT NULL');

SELECT has_column('document_chunks', 'is_processed', 'is_processed column exists');
SELECT col_type_is('document_chunks', 'is_processed', 'boolean', 'is_processed should be BOOLEAN');

SELECT has_column('document_chunks', 'processing_status', 'processing_status column exists');
SELECT col_type_is('document_chunks', 'processing_status', 'text', 'processing_status should be TEXT');

SELECT has_column('document_chunks', 'created_at', 'created_at timestamp exists');
SELECT has_column('document_chunks', 'updated_at', 'updated_at timestamp exists');

SELECT has_column('document_chunks', 'metadata', 'metadata JSONB column exists');
SELECT col_type_is('document_chunks', 'metadata', 'jsonb', 'metadata should be JSONB');

-- Test constraints
SELECT has_constraint('document_chunks', 'unique_content_source', 'unique constraint on content_source exists');

-- ============================================
-- SOURCES TABLE TESTS
-- ============================================

SELECT has_table('sources', 'sources table should exist');

SELECT has_column('sources', 'id', 'id column exists');
SELECT col_is_pk('sources', 'id', 'id is primary key');

SELECT has_column('sources', 'url', 'url column exists');
SELECT col_not_null('sources', 'url', 'url should NOT NULL');

SELECT has_column('sources', 'domain', 'domain column exists');
SELECT col_is_generated('sources', 'domain', 'domain is generated');

SELECT has_column('sources', 'reliability_score', 'reliability_score column exists');

-- ============================================
-- PROCESSING_QUEUE TABLE TESTS
-- ============================================

SELECT has_table('processing_queue', 'processing_queue table should exist');

SELECT has_column('processing_queue', 'id', 'id column exists');
SELECT col_is_pk('processing_queue', 'id', 'id is primary key');

SELECT has_column('processing_queue', 'file_path', 'file_path column exists');
SELECT has_column('processing_queue', 'status', 'status column exists');

-- ============================================
-- SEARCH_QUERIES TABLE TESTS
-- ============================================

SELECT has_table('search_queries', 'search_queries table should exist');

SELECT has_column('search_queries', 'id', 'id column exists');
SELECT col_is_pk('search_queries', 'id', 'id is primary key');

SELECT has_column('search_queries', 'query_text', 'query_text column exists');
SELECT has_column('search_queries', 'query_embedding', 'query_embedding column exists');
SELECT has_column('search_queries', 'top_result_id', 'top_result_id FK column exists');

-- Test foreign key relationship
SELECT has_fk('search_queries', ARRAY['top_result_id'], 'foreign key to document_chunks exists');

-- Finish tests
SELECT * FROM finish();

ROLLBACK;

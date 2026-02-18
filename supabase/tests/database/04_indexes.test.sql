-- pgTAP Test Suite: Database Indexes
-- Tests verify all important indexes exist and are configured correctly
-- Run with: supabase test db

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap;

SELECT plan(20);  -- Total number of index tests

-- ============================================
-- DOCUMENT_CHUNKS INDEXES
-- ============================================

-- Vector similarity search index (critical for search performance)
SELECT has_index('document_chunks', 'idx_document_chunks_embedding',
    'document_chunks should have index on embedding column for vector search');

-- Other performance indexes
SELECT has_index('document_chunks', 'idx_document_chunks_source_url',
    'document_chunks should have index on source_url for filtering');

SELECT has_index('document_chunks', 'idx_document_chunks_source_domain',
    'document_chunks should have index on source_domain for domain-based queries');

SELECT has_index('document_chunks', 'idx_document_chunks_document_id',
    'document_chunks should have index on document_id');

SELECT has_index('document_chunks', 'idx_document_chunks_created_at',
    'document_chunks should have index on created_at for time-based sorting');

SELECT has_index('document_chunks', 'idx_document_chunks_is_processed',
    'document_chunks should have index on is_processed for status filtering');

-- Full-text search index
SELECT has_index('document_chunks', 'idx_document_chunks_content_gin',
    'document_chunks should have GIN index on content for full-text search');

-- Trigram index for partial matching
SELECT has_index('document_chunks', 'idx_document_chunks_content_trgm',
    'document_chunks should have trigram index on content for partial matching');

-- ============================================
-- SOURCES INDEXES
-- ============================================

SELECT has_index('sources', 'idx_sources_domain',
    'sources should have index on domain');

SELECT has_index('sources', 'idx_sources_is_active',
    'sources should have index on is_active for filtering');

SELECT has_index('sources', 'idx_sources_last_scraped',
    'sources should have index on last_scraped_at');

-- ============================================
-- PROCESSING_QUEUE INDEXES
-- ============================================

SELECT has_index('processing_queue', 'idx_processing_queue_status',
    'processing_queue should have index on status');

SELECT has_index('processing_queue', 'idx_processing_queue_created',
    'processing_queue should have index on created_at');

-- ============================================
-- SEARCH_QUERIES INDEXES
-- ============================================

SELECT has_index('search_queries', 'idx_search_queries_created',
    'search_queries should have index on created_at');

-- Foreign key index (Supabase Advisor 0001)
SELECT has_index('search_queries', 'idx_search_queries_top_result_id',
    'search_queries should have index on top_result_id (foreign key optimization)');

-- ============================================
-- INDEX TYPE VERIFICATION
-- ============================================

-- Verify vector index type is IVFFLAT
SELECT is_indexed_with(
    'idx_document_chunks_embedding', 'ivfflat',
    'embedding index should use IVFFLAT for vector similarity search'
);

-- Verify GIN indexes for text search
SELECT is_indexed_with(
    'idx_document_chunks_content_gin', 'gin',
    'content index for full-text search should use GIN'
);

SELECT is_indexed_with(
    'idx_document_chunks_content_trgm', 'gin',
    'trigram index should use GIN'
);

-- Finish tests
SELECT * FROM finish();

ROLLBACK;

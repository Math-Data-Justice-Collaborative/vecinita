-- pgTAP Test Suite: Row Level Security (RLS) Policies
-- Tests that verify RLS policies are correctly enforcing access control
-- Run with: supabase test db

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgtap;

SELECT plan(18);  -- Total number of RLS policy tests

-- ============================================
-- RLS POLICY VERIFICATION
-- ============================================

-- Verify RLS is enabled on tables
SELECT ok(
    (SELECT row_security_active('document_chunks')),
    'RLS should be enabled on document_chunks'
);

SELECT ok(
    (SELECT row_security_active('sources')),
    'RLS should be enabled on sources'
);

SELECT ok(
    (SELECT row_security_active('processing_queue')),
    'RLS should be enabled on processing_queue'
);

SELECT ok(
    (SELECT row_security_active('search_queries')),
    'RLS should be enabled on search_queries'
);

-- ============================================
-- POLICY EXISTENCE TESTS
-- ============================================

-- document_chunks policies
SELECT has_policy('document_chunks', 'Enable read for anon',
    'document_chunks should have read policy for anon role');

SELECT has_policy('document_chunks', 'Enable read for authenticated',
    'document_chunks should have read policy for authenticated role');

SELECT has_policy('document_chunks', 'Enable insert for authenticated',
    'document_chunks should have insert policy for authenticated role');

SELECT has_policy('document_chunks', 'Enable all for service_role',
    'document_chunks should have unrestricted policy for service_role');

-- sources policies
SELECT has_policy('sources', 'Enable read for anon',
    'sources should have read policy for anon role');

SELECT has_policy('sources', 'Enable read for authenticated',
    'sources should have read policy for authenticated role');

SELECT has_policy('sources', 'Enable all for service_role',
    'sources should have full access policy for service_role');

-- processing_queue policies
SELECT has_policy('processing_queue', 'Enable read for authenticated',
    'processing_queue should have read policy for authenticated');

SELECT has_policy('processing_queue', 'Enable all for service_role',
    'processing_queue should have full access for service_role');

-- search_queries policies
SELECT has_policy('search_queries', 'Enable insert for anon',
    'search_queries should have insert policy for anon');

SELECT has_policy('search_queries', 'Enable insert for authenticated',
    'search_queries should have insert policy for authenticated');

SELECT has_policy('search_queries', 'Enable read for authenticated',
    'search_queries should have read policy for authenticated');

SELECT has_policy('search_queries', 'Enable all for service_role',
    'search_queries should have full access for service_role');

-- ============================================
-- POLICY ACTION VERIFICATION
-- ============================================

-- Verify policy types (SELECT, INSERT, UPDATE, DELETE)
SELECT policy_action_ok('document_chunks', 'Enable read for anon', ARRAY['SELECT'],
    'read policy should allow SELECT only');

SELECT policy_action_ok('document_chunks', 'Enable insert for authenticated', ARRAY['INSERT'],
    'insert policy should allow INSERT only');

SELECT policy_action_ok('search_queries', 'Enable all for service_role', ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
    'service_role policy should allow all operations');

-- Finish tests
SELECT * FROM finish();

ROLLBACK;

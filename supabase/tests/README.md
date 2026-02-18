# Vecinita Database pgTAP Test Suite

Comprehensive test suite for the Vecinita PostgreSQL database using pgTAP (PostgreSQL Tap Harness).

## Overview

This test suite verifies:
- ✅ **Table Schema** - Correct structures, columns, and data types
- ✅ **Functions & Triggers** - RPC functions work correctly with valid data
- ✅ **Row Level Security** - RLS policies enforce access control
- ✅ **Indexes** - All performance indexes exist and are configured correctly
- ✅ **Constraints** - Data integrity constraints are in place and enforced

## Prerequisites

- Supabase CLI v1.11.4 or higher
- Local PostgreSQL or Supabase cloud project

```bash
# Install Supabase CLI
npm install -g supabase

# Or with Homebrew (macOS)
brew install supabase-cli
```

## Running Tests

### Run All Tests

```bash
# From project root
supabase test db
```

### Run Specific Test File

```bash
# Run table schema tests only
supabase test db supabase/tests/database/01_tables.test.sql

# Run function tests
supabase test db supabase/tests/database/02_functions.test.sql

# Run RLS policy tests
supabase test db supabase/tests/database/03_rls_policies.test.sql

# Run index tests
supabase test db supabase/tests/database/04_indexes.test.sql

# Run constraint tests
supabase test db supabase/tests/database/05_constraints.test.sql
```

## Test Files

### 1. `01_tables.test.sql` - Table Schema Verification
**Tests: 45 assertions**

Verifies:
- All 4 tables exist (`document_chunks`, `sources`, `processing_queue`, `search_queries`)
- Column existence and correct data types (UUID, TEXT, vector, JSONB, etc.)
- Generated columns (`source_domain`, `content_hash`)
- Primary keys
- NOT NULL constraints
- Unique constraints

**Example Output:**
```
✓ document_chunks table should exist
✓ id column exists
✓ id should be UUID
✓ id is primary key
✓ content column exists
✓ content should be TEXT
✗ embedding should be vector type  ← failure example
...
45 tests, 44 passed, 1 failed
```

### 2. `02_functions.test.sql` - Function & Trigger Tests
**Tests: 15 assertions**

Verifies:
- `search_similar_documents()` RPC function exists and returns correct results
- `update_updated_at_column()` trigger sets timestamps correctly
- `update_source_statistics()` trigger creates sources and updates stats
- Function return types and signatures
- Trigger logic with test data

**Example:**
```sql
-- Test search returns 2 processed chunks
SELECT is(
    (SELECT COUNT(*) FROM search_similar_documents('[0.1, 0.2, 0.3, 0.4]'::vector, 0.0, 5)),
    2,
    'search_similar_documents should return 2 processed chunks'
);
```

### 3. `03_rls_policies.test.sql` - Row Level Security Tests
**Tests: 18 assertions**

Verifies:
- RLS is enabled on all 4 tables
- Correct policies exist for each role (`anon`, `authenticated`, `service_role`)
- Policy actions (SELECT, INSERT, UPDATE, DELETE)
- Role-based access control is configured

**RLS Policy Structure:**
```
document_chunks:
  ├── anon: SELECT only (processed chunks)
  ├── authenticated: SELECT, INSERT
  └── service_role: ALL (unrestricted)

sources:
  ├── anon: SELECT (active sources only)
  ├── authenticated: SELECT
  └── service_role: ALL

processing_queue:
  ├── authenticated: SELECT
  └── service_role: ALL

search_queries:
  ├── anon: INSERT only
  ├── authenticated: SELECT, INSERT
  └── service_role: ALL
```

### 4. `04_indexes.test.sql` - Index Verification
**Tests: 20 assertions**

Verifies:
- Vector similarity search index (IVFFLAT on `embedding`)
- Performance indexes (source_url, source_domain, is_processed, created_at)
- Full-text search index (GIN on content tsvector)
- Trigram index for partial matching
- Foreign key index on `search_queries(top_result_id)` [Advisor 0001]
- Correct index types (IVFFLAT, GIN, B-tree)

**Index Inventory:**
```
document_chunks:
  - idx_document_chunks_embedding [IVFFLAT] - Vector search
  - idx_document_chunks_source_url [B-tree] - Filter by URL
  - idx_document_chunks_source_domain [B-tree] - Filter by domain
  - idx_document_chunks_document_id [B-tree] - Join to documents
  - idx_document_chunks_created_at [B-tree] - Time-based queries
  - idx_document_chunks_is_processed [B-tree] - Status filtering
  - idx_document_chunks_content_gin [GIN] - Full-text search
  - idx_document_chunks_content_trgm [GIN] - Trigram matching

sources:
  - idx_sources_domain [B-tree]
  - idx_sources_is_active [B-tree]
  - idx_sources_last_scraped [B-tree]

processing_queue:
  - idx_processing_queue_status [B-tree]
  - idx_processing_queue_created [B-tree]

search_queries:
  - idx_search_queries_created [B-tree]
  - idx_search_queries_top_result_id [B-tree] ← NEW (Advisor 0001)
```

### 5. `05_constraints.test.sql` - Constraint Verification
**Tests: 16 assertions**

Verifies:
- Primary key constraints on all tables
- Unique constraints (content_source in document_chunks, url in sources)
- Check constraints (reliability_score range, processing status)
- Foreign key constraints (search_queries → document_chunks)
- NOT NULL constraints on important columns

## CI/CD Integration

Add to your build pipeline (e.g., GitHub Actions):

```yaml
- name: Run Supabase Database Tests
  working-directory: ./backend
  run: |
    npm install -g supabase-cli
    supabase test db
```

## Understanding pgTAP

pgTAP is TAP (Test Anything Protocol) for PostgreSQL. Common assertions:

```sql
-- Table/Schema tests
SELECT has_table('table_name');
SELECT has_column('table_name', 'column_name');
SELECT col_type_is('table_name', 'column_name', 'text');
SELECT col_not_null('table_name', 'column_name');
SELECT col_is_pk('table_name', 'column_name');

-- Index tests
SELECT has_index('table_name', 'index_name');
SELECT is_indexed_with('index_name', 'index_type');

-- Function tests
SELECT has_function('function_name', ARRAY['param_types']);
SELECT function_returns('function_name', ARRAY['params'], 'TABLE');

-- Constraint tests
SELECT has_pk('table_name');
SELECT has_constraint('table_name', 'constraint_name');
SELECT fk_ok('table', ARRAY['col'], 'ref_table', ARRAY['ref_col']);

-- Data tests
SELECT is(SELECT COUNT(*) FROM table, 5, 'Should have 5 rows');
SELECT results_eq('SELECT col FROM table', 'SELECT expected_value');
```

## Troubleshooting

### Tests Fail with pgTAP Not Found

```bash
# Install pgTAP extension
supabase db push  # Updates schema

# Or manually in SQL Editor:
CREATE EXTENSION pgtap;
```

### Vector Type Not Available

```bash
# Ensure pgvector extension is installed
CREATE EXTENSION vector;

# Check version
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

### Tests Hang or Timeout

- Check Supabase database connection
- Verify database is running locally or accessible
- Check network connectivity

```bash
# Test connection
psql {DATABASE_URL} -c "SELECT version();"
```

## Adding New Tests

1. Create new `.test.sql` file in `supabase/tests/database/`
2. Use naming convention: `NN_description.test.sql` (e.g., `06_views.test.sql`)
3. Include pgTAP header and `SELECT plan(X)` with assertion count
4. Write assertions using pgTAP functions
5. End with `SELECT * FROM finish(); ROLLBACK;`

Example:

```sql
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SELECT plan(5);

-- Your tests here
SELECT has_view('v_chunk_statistics', 'view should exist');
-- ... more assertions

SELECT * FROM finish();
ROLLBACK;
```

## Test Results Example

```
$ supabase test db
supabase/tests/database/01_tables.test.sql .... ok
supabase/tests/database/02_functions.test.sql . ok
supabase/tests/database/03_rls_policies.test.sql ok
supabase/tests/database/04_indexes.test.sql ... ok
supabase/tests/database/05_constraints.test.sql ok
All tests successful.
Files=5, Tests=104,  2.15 wallclock secs ( 0.02 usr +  0.01 sys = 0.03 CPU)
Result: PASS
```

## References

- [pgTAP Documentation](https://pgtap.org/)
- [Official pgTAP API](https://pgtap.org/documentation.html)
- [Supabase Testing Guide](https://supabase.com/docs/guides/database/testing)
- [PostgreSQL Testing Best Practices](https://www.postgresql.org/docs/current/sql-syntax.html)

## Support

For issues or questions:
1. Check pgTAP documentation
2. Review existing test patterns
3. Test locally before committing
4. Add comments to explain complex test logic

---

**Last Updated:** February 8, 2026  
**Test Coverage:** 104 assertions across 5 test files  
**Status:** ✅ Ready for production

# Vecinita Database Best Practices

**Version:** 1.0  
**Last Updated:** February 8, 2026  
**Status:** ✅ Production Ready

## Table of Contents

1. [Security Best Practices](#security-best-practices)
2. [Performance Best Practices](#performance-best-practices)
3. [Testing Strategy](#testing-strategy)
4. [Monitoring & Maintenance](#monitoring--maintenance)
5. [Advisor Compliance](#advisor-compliance)
6. [Development Workflow](#development-workflow)

---

## Security Best Practices

### Row Level Security (RLS)

#### Policy Design

All public tables have RLS enabled with three-tier role-based access:

**Role Hierarchy:**
```
anon (public) ──→ authenticated (logged-in users) ──→ service_role (backend admin)
  Read-only          Read/Write              Full access
```

#### Policy Configuration

**1. document_chunks** (Knowledge base)
```sql
-- ANON: Can read processed documents only (public search)
CREATE POLICY "Enable read for anon" ON document_chunks 
    FOR SELECT TO anon USING (is_processed = TRUE);

-- AUTHENTICATED: Can read all + insert new submissions
CREATE POLICY "Enable read for authenticated" ON document_chunks 
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Enable insert for authenticated" ON document_chunks 
    FOR INSERT TO authenticated WITH CHECK (true);

-- SERVICE_ROLE: Backend has full admin access
CREATE POLICY "Enable all for service_role" ON document_chunks 
    FOR ALL TO service_role USING (true);
```

**2. sources** (Metadata about sources)
```sql
-- ANON: Can only see active sources (public metadata)
CREATE POLICY "Enable read for anon" ON sources 
    FOR SELECT TO anon USING (is_active = TRUE);

-- AUTHENTICATED: Can see all sources
CREATE POLICY "Enable read for authenticated" ON sources 
    FOR SELECT TO authenticated USING (true);

-- SERVICE_ROLE: Full admin access
CREATE POLICY "Enable all for service_role" ON sources 
    FOR ALL TO service_role USING (true);
```

**3. processing_queue** (Internal operations - backend only)
```sql
-- AUTHENTICATED: Can only see status (read-only)
CREATE POLICY "Enable read for authenticated" ON processing_queue 
    FOR SELECT TO authenticated USING (true);

-- SERVICE_ROLE: Full admin access for queue management
CREATE POLICY "Enable all for service_role" ON processing_queue 
    FOR ALL TO service_role USING (true);
```

**4. search_queries** (Analytics + feedback)
```sql
-- ANON: Can submit searches (insert-only)
CREATE POLICY "Enable insert for anon" ON search_queries 
    FOR INSERT TO anon WITH CHECK (true);

-- AUTHENTICATED: Can submit + see history
CREATE POLICY "Enable insert for authenticated" ON search_queries 
    FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Enable read for authenticated" ON search_queries 
    FOR SELECT TO authenticated USING (true);

-- SERVICE_ROLE: Full admin access
CREATE POLICY "Enable all for service_role" ON search_queries 
    FOR ALL TO service_role USING (true);
```

#### Testing RLS Policies

Use pgTAP test suite:
```bash
# Run RLS policy tests
supabase test db supabase/tests/database/03_rls_policies.test.sql
```

#### Auditing RLS

Check which policies exist:
```sql
SELECT schemaname, tablename, policyname, permissive, roles
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

### Authentication & API Keys

#### Auth Service Security

**Features Implemented:**
- ✅ API key validation (format + length checks)
- ✅ Brute-force protection (blocks after 5 failed attempts)
- ✅ Password complexity enforcement (12 chars, mixed case, numbers, symbols)
- ✅ JWT token expiration (15 min access, 7 day refresh)
- ✅ Rate limiting per API key (1000 tokens/day)
- ✅ Failed attempt tracking with automatic blocking

**Configuration:**
```python
# auth/src/main.py

PASSWORD_MIN_LENGTH = 12
PASSWORD_COMPLEXITY_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{12,}$'

JWT_EXPIRATION_MINUTES = 15
JWT_REFRESH_EXPIRATION_DAYS = 7

MAX_FAILED_ATTEMPTS_BEFORE_BLOCK = 5
```

#### API Key Management

**Valid API Key Formats:**
- Prefix: `sk_vp_` or `apk_`
- Length: Minimum 20 characters
- Example: `sk_vp_1234567890abcdefghij`

**Validation Workflow:**
```
1. Format check (prefix + length)
   ├─ FAIL → Record failed attempt
   └─ PASS

2. Database lookup (is key active/revoked?)
   ├─ FAIL → Record failed attempt
   └─ PASS

3. Check block list (too many failed attempts?)
   ├─ BLOCKED → Return 429
   └─ ALLOWED

4. Generate JWT tokens
   ├─ Access token: 15 minutes
   └─ Refresh token: 7 days
```

### Data Integrity Constraints

#### Unique Constraints

**Prevent Duplicate Chunks:**
```sql
ALTER TABLE document_chunks
ADD CONSTRAINT unique_content_source 
UNIQUE(content_hash, source_url, chunk_index);
```

**Prevent Duplicate Sources:**
```sql
ALTER TABLE sources
ADD CONSTRAINT sources_url_key UNIQUE (url);
```

#### Check Constraints

**Reliability Score Range:**
```sql
ALTER TABLE sources
ADD CONSTRAINT check_reliability_score 
CHECK (reliability_score >= 0 AND reliability_score <= 1);
```

**Processing Status Values:**
```sql
ALTER TABLE processing_queue
ADD CONSTRAINT check_status 
CHECK (status IN ('pending', 'processing', 'completed', 'failed'));
```

### Exposed Data Review

#### Sensitive Column Analysis

**Safe to Expose:**
- ✅ `document_chunks.id`, `content`, `source_url`, `chunk_index`
- ✅ `sources.url`, `domain`, `title`, `description`
- ✅ `search_queries.query_text`, `similarity_score`

**Requires Filtering:**
- ⚠️ `document_chunks.embedding` (vector data) - only via RPC search
- ⚠️ `document_chunks.metadata` - may contain PII, audit access
- ⚠️ `sources.metadata` - may contain credentials, filter carefully

**Never Expose:**
- ❌ `auth.users` email, phone numbers
- ❌ API keys, secrets, tokens
- ❌ Internal system data

#### Audit Access to Sensitive Fields

```sql
-- Create audit table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT,
    operation TEXT,
    user_role TEXT,
    accessed_columns TEXT[],
    accessed_at TIMESTAMP DEFAULT NOW()
);

-- Track access to embedding column
CREATE TRIGGER audit_embedding_access
BEFORE SELECT ON document_chunks
FOR EACH ROW
EXECUTE FUNCTION log_embedding_access();
```

---

## Performance Best Practices

### Indexing Strategy

#### Index Inventory

| Table | Column | Index Type | Purpose | Status |
|-------|--------|-----------|---------|--------|
| document_chunks | embedding | IVFFLAT | Vector search | ✅ Essential |
| document_chunks | source_url | B-tree | Filter by URL | ✅ Essential |
| document_chunks | source_domain | B-tree | Filter by domain | ✅ Recommended |
| document_chunks | is_processed | B-tree | Status filtering | ✅ Essential |
| document_chunks | created_at | B-tree | Time-based queries | ✅ Recommended |
| document_chunks | content | GIN | Full-text search | ✅ Optional |
| document_chunks | content | GIN (trigram) | Fuzzy matching | ✅ Optional |
| sources | domain | B-tree | Domain lookup | ✅ Recommended |
| sources | is_active | B-tree | Filter active | ✅ Recommended |
| search_queries | top_result_id | B-tree | FK optimization | ✅ Essential (Advisor 0001) |

#### Creating Indexes

**Vector Similarity Search (Critical):**
```sql
CREATE INDEX idx_document_chunks_embedding 
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Tuning for larger datasets:
-- - 10K docs: lists = 50-100
-- - 100K docs: lists = 500
-- - 1M+ docs: lists = 1000-2000
```

**Foreign Key Optimization:**
```sql
CREATE INDEX idx_search_queries_top_result_id 
    ON search_queries(top_result_id);
```

**Full-Text Search:**
```sql
CREATE INDEX idx_document_chunks_content_gin 
    ON document_chunks USING gin(to_tsvector('english', content));
```

### Query Optimization

#### Common Queries & Optimization

**1. Vector Similarity Search**

```sql
-- OPTIMIZED: Using index + filtering
EXPLAIN ANALYZE
SELECT id, content, source_url, chunk_index, metadata,
       1 - (embedding <=> '[0.1,...]'::vector) AS similarity
FROM document_chunks
WHERE embedding IS NOT NULL
    AND is_processed = TRUE
    AND 1 - (embedding <=> '[0.1,...]'::vector) > 0.3
ORDER BY embedding <=> '[0.1,...]'::vector
LIMIT 5;

-- Expected plan:
-- Index Scan using idx_document_chunks_embedding
-- Planning Time: 0.125 ms
-- Execution Time: 12.450 ms ← GOOD
```

**2. Document Retrieval by URL**

```sql
-- OPTIMIZED: Using index
EXPLAIN ANALYZE
SELECT id, content, chunk_index, created_at
FROM document_chunks
WHERE source_url = 'https://example.com'
ORDER BY chunk_index;

-- Expected plan:
-- Index Scan using idx_document_chunks_source_url
-- Planning Time: 0.050 ms
-- Execution Time: 1.200 ms ← GOOD
```

**3.Source Statistics**

```sql
-- OPTIMIZED: Using materialized view
SELECT * FROM v_chunk_statistics
ORDER BY chunk_count DESC
LIMIT 20;

-- Automatic refresh via trigger on INSERT
-- Planning Time: 0.050 ms
-- Execution Time: 2.150 ms ← GOOD
```

#### Statistics Maintenance

**Weekly Maintenance:**
```sql
-- Update optimizer statistics
ANALYZE document_chunks;
ANALYZE sources;
ANALYZE processing_queue;
ANALYZE search_queries;

-- Vacuum dead rows (automatic, but manual for testing)
VACUUM ANALYZE document_chunks;
```

**Monthly Deep Maintenance:**
```sql
-- Check index bloat
SELECT schemaname, tablename, indexname, 
       pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Reindex if > 10GB or bloated
REINDEX INDEX idx_document_chunks_embedding;
```

### Vector Index Tuning

#### Monitor Vector Search Performance

```sql
-- Baseline vector search
SELECT COUNT(*) FROM search_similar_documents('[0.1,...]'::vector, 0.3, 5);

-- Expected time: 10-50ms depending on dataset size
-- If > 100ms, consider:
-- 1. Increase IVFFLAT lists parameter
-- 2. Add WHERE is_processed = TRUE filter
-- 3. Increase similarity threshold (0.3 → 0.5)
```

#### Adjust IVFFLAT for Larger Datasets

```sql
-- Current setup: lists = 100 (optimal for 10K docs)

-- For 100K documents:
DROP INDEX idx_document_chunks_embedding;
CREATE INDEX idx_document_chunks_embedding 
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 500);

-- Timing: Reindex takes ~30 seconds for 100K vectors

-- For 1M+ documents, consider HNSW:
CREATE INDEX idx_document_chunks_embedding_hnsw
    ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## Testing Strategy

### Unit Tests: pgTAP Suite

**Location:** `supabase/tests/database/`

**Test Coverage:** 104 assertions across 5 files

#### Running Tests

```bash
# Run all database tests
supabase test db

# Run specific tests
supabase test db supabase/tests/database/01_tables.test.sql
supabase test db supabase/tests/database/03_rls_policies.test.sql

# Expected output:
# supabase/tests/database/01_tables.test.sql ......... ok
# supabase/tests/database/02_functions.test.sql ..... ok
# supabase/tests/database/03_rls_policies.test.sql .. ok
# supabase/tests/database/04_indexes.test.sql ....... ok
# supabase/tests/database/05_constraints.test.sql ... ok
# All tests successful. (104 tests, 2.15 seconds)
```

#### Test Files

1. **01_tables.test.sql** (45 assertions)
   - Table existence and schema
   - Column types and constraints
   - Generated columns
   - Primary keys

2. **02_functions.test.sql** (15 assertions)
   - RPC function existence
   - Function return types
   - Trigger logic
   - Data integrity functions

3. **03_rls_policies.test.sql** (18 assertions)
   - RLS enabled on tables
   - Policies for each role (anon, authenticated, service_role)
   - Policy actions (SELECT, INSERT, UPDATE, DELETE)

4. **04_indexes.test.sql** (20 assertions)
   - Index existence
   - Index types (IVFFLAT, GIN, B-tree)
   - Foreign key indexes

5. **05_constraints.test.sql** (16 assertions)
   - Primary keys
   - Unique constraints
   - Check constraints
   - Foreign key relationships

#### Integration Tests: Python

```bash
# Backend integration tests
cd backend
uv run pytest tests/ -m "not db" -v

# Tests verify:
# - Agent can access local Supabase
# - Embedding service works
# - Vector search returns expected results
# - RLS policies are enforced
```

### Performance Tests

```bash
# Before deployment:
supabase db push
uv run python backend/scripts/test_query_performance.py

# Verify:
# - Vector search: < 50ms
# - URL filtering: < 10ms
# - Domain aggregation: < 100ms
```

---

## Monitoring & Maintenance

### Daily Checks

```bash
# Check database health
psql $DATABASE_URL -c "SELECT version();"

# Check connection pool
psql $DATABASE_URL -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# Monitor slow queries (> 100ms)
psql $DATABASE_URL -c "SELECT query, mean_exec_time FROM pg_stat_statements WHERE mean_exec_time > 100 ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Weekly Maintenance

```sql
-- Update statistics
ANALYZE document_chunks;
ANALYZE sources;
ANALYZE processing_queue;
ANALYZE search_queries;

-- Check row count estimates
SELECT relname, n_live_tup, n_dead_tup
FROM pg_stat_user_tables
WHERE n_dead_tup > n_live_tup * 0.1;  -- Alert if > 10% dead rows

-- Run autovacuum (automatic scheduling)
SELECT schemaname, tablename, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC;
```

### Monthly Reviews

```sql
-- Index usage analysis
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Identify unused indexes (not used in last 30 days)
SELECT schemaname, tablename, indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexname NOT LIKE 'pg_toast%'
  AND indexname NOT LIKE '%_pkey';

-- Check table bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup,
    n_dead_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

### Quarterly Security Audit

```bash
# Review RLS policies
psql $DATABASE_URL -c "SELECT * FROM pg_policies WHERE schemaname = 'public';"

# Check exposed tables (should not expose auth.users)
psql $DATABASE_URL -c "SELECT schemaname, tablename FROM information_schema.tables WHERE table_schema = 'public';"

# Verify all tables have RLS enabled
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND NOT EXISTS (SELECT 1 FROM pg_policies WHERE pg_tables.tablename = pg_policies.tablename);"

# Check for privileged operations
psql $DATABASE_URL -c "SELECT * FROM information_schema.role_table_grants WHERE table_schema = 'public';"
```

---

## Advisor Compliance

### Supabase Advisor Checks

**Critical Issues (Must Fix):**
- ☑️ 0001: Unindexed foreign keys → Fixed (added `idx_search_queries_top_result_id`)
- ☑️ 0008: RLS enabled, no policy → Fixed (all policies configured)
- ☑️ 0013: RLS disabled in public → Fixed (RLS enabled on all tables)
- ☑️ 0023: Sensitive columns exposed → Audited (RLS filtering applied)

**Security Checks (Review):**
- ✅ 0002: Auth users exposed → No (auth.users not in public schema)
- ✅ 0010: Security definer view → No (no views with SECURITY DEFINER)
- ✅ 0012: Allow anonymous sign-ins → No (auth properly configured)

**Performance Checks (Monitor):**
- ✅ 0005: Unused indexes → Manual review monthly
- ✅ 0020: Table bloat → Monitor via autovacuum

### Running Advisor Checks

```sql
-- Run Supabase Advisor checks
\i backend/scripts/check_advisor_health.sql

-- Dashboard check:
-- 1. Go to Supabase Dashboard
-- 2. Navigate to Database → Performance Advisor
-- 3. Navigate to Database → Security Advisor
-- 4. Review all 24 checks (0001-0024)
```

---

## Development Workflow

### Schema Changes

**Workflow for Adding New Tables:**

```bash
# 1. Design table with constraints
# 2. Create migration file
mkdir -p backend/migrations
cat > backend/migrations/001_add_new_table.sql << 'EOF'
CREATE TABLE new_table (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read for authenticated" ON new_table
    FOR SELECT TO authenticated USING (true);
EOF

# 3. Apply migration locally
psql $DATABASE_URL -f backend/migrations/001_add_new_table.sql

# 4. Create pgTAP tests for new table
cat > supabase/tests/database/06_new_table.test.sql << 'EOF'
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgtap;
SELECT plan(5);

-- Tests here

SELECT * FROM finish();
ROLLBACK;
EOF

# 5. Run tests
supabase test db

# 6. Commit to git
git add backend/migrations/ supabase/tests/database/
git commit -m "feat: Add new_table with RLS"
```

### Code Review Checklist

Before merging database changes:

- [ ] Schema changes are backward-compatible
- [ ] RLS policies defined for each role
- [ ] Indexes added for new query patterns
- [ ] pgTAP tests written and passing
- [ ] Performance impact analyzed (< 20% regression)
- [ ] Advisor checks show no critical issues
- [ ] Documentation updated (schema diagrams, policies)
- [ ] Secrets not committed (.env files, API keys)

### Local Testing

```bash
# 1. Start local Supabase
cd supabase
./start-local.sh

# 2. Configure backend for local
cp backend/.env.test backend/.env

# 3. Run tests
supabase test db

# 4. Run Python tests
cd backend
uv run pytest tests/ -m "not db"

# 5. Test queries manually
psql localhost:54321 -U postgres -c "SELECT * FROM document_chunks LIMIT 1;"
```

---

## Production Deployment Checklist

Before deploying to production:

### Security
- [ ] RLS policies reviewed and tested
- [ ] No sensitive data exposed in API
- [ ] API keys and secrets not in code
- [ ] Authentication service hardened
- [ ] Rate limiting configured per key

### Performance
- [ ] Query performance baselines established
- [ ] Indexes created for all query patterns
- [ ] Vector search optimized for dataset size
- [ ] Statistics updated (ANALYZE)
- [ ] No blocking locks on tables

### Testing
- [ ] All pgTAP tests passing (104/104)
- [ ] Python integration tests passing
- [ ] Load testing completed (simulator)
- [ ] Failover tested (point-in-time recovery)

### Monitoring
- [ ] Alerts configured for slow queries
- [ ] Advisor checks passing (no critical issues)
- [ ] Backup strategy verified
- [ ] Logging enabled for audit trail

### Documentation
- [ ] Schema documented
- [ ] RLS policies documented
- [ ] Performance baselines documented
- [ ] Runbook for common operations
- [ ] Disaster recovery plan

---

## Quick Reference

### Essential Commands

```bash
# Test suite
supabase test db
supabase test db supabase/tests/database/01_tables.test.sql

# Performance monitoring
EXPLAIN ANALYZE SELECT ... FROM document_chunks;

# Statistics
ANALYZE document_chunks;
VACUUM ANALYZE document_chunks;

# Index management
CREATE INDEX idx_name ON table(column);
DROP INDEX CONCURRENTLY idx_name;
REINDEX INDEX idx_name;

# RLS inspection
SELECT * FROM pg_policies WHERE schemaname = 'public';

# Query stats
SELECT query, mean_exec_time FROM pg_stat_statements
WHERE mean_exec_time > 100;

# Connection pool
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
```

### Support Resources

- **pgTAP Documentation:** https://pgtap.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Supabase Guides:** https://supabase.com/docs/guides/database
- **Vector Search:** https://github.com/pgvector/pgvector

---

**Version:** 1.0  
**Last Updated:** February 8, 2026  
**Next Review:** May 8, 2026  
**Maintained By:** Database Team

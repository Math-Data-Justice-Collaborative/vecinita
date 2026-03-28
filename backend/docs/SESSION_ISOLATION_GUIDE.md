# Session Isolation Implementation Guide

## Overview

The Vecinita database schema now supports session-level data isolation for single-tenant deployments. This allows thread-based conversation isolation without requiring full multi-tenancy infrastructure.

## Database Schema Changes

### New Columns

**document_chunks table:**
- `session_id TEXT DEFAULT NULL` - Session identifier for data isolation
  - `NULL` = Public data (accessible to all)
  - `<value>` = Session-specific data (isolated)

**search_queries table:**
- `session_id TEXT DEFAULT NULL` - Links queries to specific sessions/threads

### New Indexes

- `idx_document_chunks_session` - Session filtering
- `idx_document_chunks_session_processed` - Session + processing status
- `idx_search_queries_session` - Query session filtering

### Updated RPC Functions

**search_similar_documents()**
- Added optional `session_filter TEXT DEFAULT NULL` parameter
- `session_filter=NULL`: Returns only public data (session_id IS NULL)
- `session_filter='value'`: Returns session data + public data

**New Functions:**
- `search_similar_documents_by_session()` - Strict session-only search (no public fallback)
- `count_session_documents()` - Count documents in a session
- `list_active_sessions()` - List all sessions with document counts
- `delete_session_data()` - Delete all data for a session (admin/cleanup)

## Implementation Status

### ✅ Completed

1. **Database Schema** - Migration script and updated init-local-db.sql
2. **RPC Functions** - Enhanced vector search with session filtering
3. **db_search Tool** - Updated to accept optional session_id parameter
4. **Helper Functions** - Session management utilities

### 🚧 In Progress

1. **API Gateway Middleware** - Thread isolation middleware for request-level session management
2. **Document Uploader** - Support for tagging scraped content with session_id

### 📋 Todo

1. **Session Management API** - Endpoints for creating/managing sessions
2. **Admin Tools** - UI for viewing and managing session data
3. **Cleanup Jobs** - Automated session expiration/cleanup

## Usage

### Single-Tenant Mode (Current)

By default, all data has `session_id=NULL` (public). The agent searches all public data:

```python
# All searches return public data only
db_search_tool = create_db_search_tool(
    supabase, 
    embedding_model, 
    session_id=None  # Default: public data only
)
```

### Thread Isolation (Optional)

To isolate conversations, pass thread_id as session_id:

```python
# Per-request tool creation with thread isolation
db_search_tool = create_db_search_tool(
    supabase,
    embedding_model,
    session_id=thread_id  # Isolate to this thread
)
```

### SQL Examples

**Search with session filtering:**
```sql
-- Search public data only
SELECT * FROM search_similar_documents(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_threshold := 0.3,
    match_count := 5,
    session_filter := NULL
);

-- Search session + public data
SELECT * FROM search_similar_documents(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_threshold := 0.3,
    match_count := 5,
    session_filter := 'thread-abc123'
);

-- Strict session-only search (no public)
SELECT * FROM search_similar_documents_by_session(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    session_filter := 'thread-abc123',
    match_threshold := 0.3,
    match_count := 5
);
```

**Session management:**
```sql
-- Count documents in a session
SELECT count_session_documents('thread-abc123');

-- List all active sessions
SELECT * FROM list_active_sessions();

-- Delete session data (careful!)
SELECT * FROM delete_session_data('thread-abc123');
```

## Migration

### For Existing Databases

Run the migration script:
```bash
# Via psql
psql -U postgres -d vecinita -f backend/scripts/add_session_isolation.sql

# Via Supabase SQL Editor
# Copy and paste contents of add_session_isolation.sql
```

### For New Installations

The schema is included in `supabase/init-local-db.sql` - no separate migration needed.

## Security Considerations

### Single-Tenant Mode

- All data defaults to public (session_id=NULL)
- Thread isolation is optional and controlled at application level
- No cross-tenant data leakage possible (only one tenant)

### Future Multi-Tenant Considerations

- Session IDs should be cryptographically random (UUID v4)
- API gateway must validate session ownership before queries
- Consider RLS (Row Level Security) policies for defense in depth
- Audit logging for session access

## Configuration

### Environment Variables

```bash
# Enable session isolation (future)
ENABLE_SESSION_ISOLATION=false  # Currently optional

# Session expiration (future)
SESSION_TTL_HOURS=24

# Default to public data
DEFAULT_SESSION_FILTER=null
```

## Performance

### Index Strategy

- Partial indexes on `session_id` (WHERE session_id IS NOT NULL) minimize overhead for public data
- Composite indexes optimize common query patterns

### Query Performance

- Public-only queries: No performance impact (session_id=NULL)
- Session-filtered queries: Uses btree index on session_id
- Combined queries: Index scan + sequential scan merge

### Monitoring

```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexname LIKE '%session%';

-- Check session data distribution
SELECT 
    session_id,
    COUNT(*) as chunk_count,
    SUM(char_length(content)) as total_chars
FROM document_chunks
GROUP BY session_id
ORDER BY chunk_count DESC;
```

## Troubleshooting

### RPC Function Overload Conflict

If you see "PGRST203: Could not choose best candidate function":

```bash
# Remove old function versions
psql -U postgres -d vecinita -f backend/scripts/fix_rpc_overload.sql
```

### Session Data Not Isolated

1. Check session_id is being passed to RPC function
2. Verify session_id in database: `SELECT DISTINCT session_id FROM document_chunks;`
3. Check logs for session filter value

### Performance Degradation

1. Verify indexes exist: `\di+ idx_document_chunks_session*`
2. Run ANALYZE: `ANALYZE document_chunks;`
3. Check for many small sessions (consider cleanup)

## References

- Migration Script: `backend/scripts/add_session_isolation.sql`
- Schema Definition: `supabase/init-local-db.sql`
- Tool Implementation: `backend/src/services/agent/tools/db_search.py`
- API Middleware: `backend/src/api/middleware.py` (planned)

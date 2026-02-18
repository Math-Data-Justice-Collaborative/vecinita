# Admin Endpoints Implementation Guide

## Overview

The admin router (`backend/src/api/router_admin.py`) provides 8 fully-implemented endpoints for system management, monitoring, and diagnostics. All endpoints require proper authentication (configured via `AuthenticationMiddleware`).

## Endpoints

### 1. Health Check
**GET `/api/admin/health`**

Checks the health of all backend services: agent service, embedding service, and database.

**Response:**
```json
{
  "status": "healthy|degraded",
  "agent_service": {
    "status": "ok|error",
    "response_time_ms": 45,
    "last_check": "2024-02-09T10:30:00Z"
  },
  "embedding_service": {
    "status": "ok|error",
    "response_time_ms": 32,
    "last_check": "2024-02-09T10:30:00Z"
  },
  "database": {
    "status": "ok|error",
    "last_check": "2024-02-09T10:30:00Z"
  },
  "timestamp": "2024-02-09T10:30:00Z"
}
```

**Usage:**
```bash
curl -X GET 'http://localhost:8002/api/admin/health' \
  -H 'Authorization: Bearer <api-key>'
```

### 2. Database Statistics
**GET `/api/admin/stats`**

Returns comprehensive database and system statistics.

**Response:**
```json
{
  "database": {
    "total_chunks": 45230,
    "unique_sources": 892,
    "total_embeddings": 45230,
    "average_chunk_size": 2048.5,
    "db_size_bytes": 92593156,
    "last_updated": "2024-02-09T10:30:00Z"
  },
  "services": {
    "agent_service": {
      "url": "http://localhost:8000",
      "status": "configured"
    },
    "embedding_service": {
      "url": "http://localhost:8001",
      "status": "configured"
    }
  }
}
```

**Usage:**
```bash
curl -X GET 'http://localhost:8002/api/admin/stats' \
  -H 'Authorization: Bearer <api-key>'
```

**Database Requirements:**
- RPC function `get_unique_sources_count()`
- RPC function `get_average_chunk_size()`
- RPC function `get_database_size()`

These functions are created by running `backend/scripts/add_admin_helper_functions.sql` or are included in `supabase/init-local-db.sql` for new installations.

### 3. List Documents
**GET `/api/admin/documents`**

Lists indexed document chunks with pagination and optional filtering.

**Query Parameters:**
- `limit` (int, default 50, max 100): Results per page
- `offset` (int, default 0): Results to skip
- `source_filter` (string, optional): Filter by source URL (case-insensitive)

**Response:**
```json
{
  "documents": [
    {
      "chunk_id": "uuid-here",
      "source_url": "https://example.com/doc",
      "content_preview": "First 200 characters of content...",
      "embedding_dimension": 384,
      "created_at": "2024-02-09T10:00:00Z",
      "updated_at": "2024-02-09T12:00:00Z"
    }
  ],
  "total": 45230,
  "page": 1,
  "limit": 50
}
```

**Usage:**
```bash
# List first 20 documents
curl -X GET 'http://localhost:8002/api/admin/documents?limit=20' \
  -H 'Authorization: Bearer <api-key>'

# Filter by source
curl -X GET 'http://localhost:8002/api/admin/documents?source_filter=example.com' \
  -H 'Authorization: Bearer <api-key>'

# Pagination (page 3, 50 per page)
curl -X GET 'http://localhost:8002/api/admin/documents?limit=50&offset=100' \
  -H 'Authorization: Bearer <api-key>'
```

### 4. Delete Document Chunk
**DELETE `/api/admin/documents/{chunk_id}`**

Deletes a specific document chunk from the database and vector store.

**Path Parameters:**
- `chunk_id` (string): UUID of the chunk to delete

**Response:**
```json
{
  "success": true,
  "deleted_chunk_id": "uuid-here",
  "message": "Successfully deleted chunk uuid-here"
}
```

**Error Responses:**
- `404`: Chunk not found
- `500`: Internal server error

**Usage:**
```bash
curl -X DELETE 'http://localhost:8002/api/admin/documents/abc-123-def' \
  -H 'Authorization: Bearer <api-key>'
```

### 5. Request Database Cleanup Token
**GET `/api/admin/database/clean-request`**

Generates a one-time confirmation token for database cleanup. This is the first step of the two-step cleanup process.

**Response:**
```json
{
  "token": "secure-token-here",
  "expires_at": "2024-02-09T10:35:00Z",
  "endpoint": "POST /api/admin/database/clean"
}
```

**Token Properties:**
- Valid for 5 minutes
- One-time use (consumed on successful cleanup)
- Stored in-memory (use Redis for production)

**Usage:**
```bash
curl -X GET 'http://localhost:8002/api/admin/database/clean-request' \
  -H 'Authorization: Bearer <api-key>'
```

### 6. Clean Database
**POST `/api/admin/database/clean`**

Deletes all document chunks from the database. **DESTRUCTIVE OPERATION** requiring confirmation token from step 5.

**Request Body:**
```json
{
  "confirmation_token": "token-from-step-5"
}
```

**Response:**
```json
{
  "success": true,
  "deleted_chunks": 45230,
  "message": "Database cleaned: 45230 chunks deleted"
}
```

**Error Responses:**
- `403`: Invalid or expired token
- `500`: Internal server error

**Behavior:**
- Validates confirmation token
- Deletes chunks in batches (default 1000 per batch, configurable via `ADMIN_CONFIG["delete_chunk_batch_size"]`)
- Attempts to clean `search_queries` table if it exists
- Consumes the token (one-time use)

**Usage:**
```bash
# Step 1: Get token
TOKEN=$(curl -X GET 'http://localhost:8002/api/admin/database/clean-request' \
  -H 'Authorization: Bearer <api-key>' | jq -r '.token')

# Step 2: Use token to clean database
curl -X POST 'http://localhost:8002/api/admin/database/clean' \
  -H 'Authorization: Bearer <api-key>' \
  -H 'Content-Type: application/json' \
  -d "{\"confirmation_token\": \"$TOKEN\"}"
```

### 7. List Sources
**GET `/api/admin/sources`**

Lists all unique source URLs in the database with chunk counts and timestamps.

**Response:**
```json
{
  "sources": [
    {
      "url": "https://example.com/docs",
      "chunk_count": 125,
      "created_at": "2024-02-09T10:00:00Z",
      "last_updated": "2024-02-09T12:00:00Z"
    }
  ],
  "total": 892
}
```

**Behavior:**
- Tries to use RPC function `get_sources_with_counts()` first
- Falls back to Python-side aggregation if RPC doesn't exist
- Sources sorted by chunk count (descending)

**Usage:**
```bash
curl -X GET 'http://localhost:8002/api/admin/sources' \
  -H 'Authorization: Bearer <api-key>'
```

### 8. Validate Source
**POST `/api/admin/sources/validate`**

Tests HTTP connectivity and scrapability for a source URL.

**Request Body:**
```json
{
  "url": "https://example.com",
  "loader_type": "auto|playwright|recursive|unstructured"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "is_accessible": true,
  "is_scrapeable": true,
  "http_status": 200,
  "message": "URL is accessible and scrapeable"
}
```

**Behavior:**
- Attempts HTTP HEAD request first (lightweight)
- Falls back to GET if HEAD not allowed (405)
- Checks Content-Type header for scrapability
- Scrapeable types: HTML, XML, PDF, plain text
- 10-second timeout
- Follows redirects

**Common Messages:**
- `"URL is accessible and scrapeable"`: Success
- `"URL is accessible but content type (image/png) may not be scrapeable"`: Accessible but wrong type
- `"URL returned HTTP 404"`: Not found
- `"Request timed out after 10 seconds"`: Timeout
- `"HTTP error: ..."`: Connection error

**Usage:**
```bash
curl -X POST 'http://localhost:8002/api/admin/sources/validate' \
  -H 'Authorization: Bearer <api-key>' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com", "loader_type": "auto"}'
```

## Configuration Endpoints (Already Implemented)

### Get Admin Config
**GET `/api/admin/config`**

Returns current admin configuration.

### Update Admin Config
**POST `/api/admin/config`**

Updates admin configuration (currently only `require_confirmation` setting).

## Database Setup

### For New Installations
Run `supabase/init-local-db.sql` which includes all necessary helper functions.

### For Existing Installations
Run these migrations in order:
1. `backend/scripts/add_session_isolation.sql` (if not already applied)
2. `backend/scripts/add_admin_helper_functions.sql`

### Required RPC Functions
```sql
-- Count unique sources
CREATE OR REPLACE FUNCTION get_unique_sources_count() RETURNS INTEGER;

-- Average chunk size
CREATE OR REPLACE FUNCTION get_average_chunk_size() RETURNS FLOAT;

-- Database size in bytes
CREATE OR REPLACE FUNCTION get_database_size() RETURNS BIGINT;

-- Sources with counts and timestamps
CREATE OR REPLACE FUNCTION get_sources_with_counts() 
RETURNS TABLE (...);
```

## Environment Variables

```bash
# Service URLs (defined in main.py, also used in router_admin.py)
AGENT_SERVICE_URL=http://localhost:8000
EMBEDDING_SERVICE_URL=http://localhost:8001

# Database credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

## Configuration

Admin configuration is stored in `ADMIN_CONFIG` dict in `router_admin.py`:

```python
ADMIN_CONFIG = {
    "require_confirmation": True,  # Require token for database cleanup
    "delete_chunk_batch_size": 1000,  # Chunks per batch during cleanup
}
```

Can be updated via `POST /api/admin/config`.

## Security Considerations

1. **Authentication**: All admin endpoints should be protected by `AuthenticationMiddleware`
2. **Token Storage**: Currently in-memory; use Redis for production multi-instance deployments
3. **Rate Limiting**: Consider adding stricter rate limits for destructive operations
4. **Audit Logging**: Log all admin actions (especially deletions) for compliance
5. **Confirmation Tokens**: 5-minute expiry, one-time use, automatically cleaned up

## Error Handling

All endpoints use consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common status codes:
- `200`: Success
- `403`: Forbidden (invalid token, insufficient permissions)
- `404`: Not found
- `500`: Internal server error
- `501`: Not implemented (should not occur with current implementation)

## Production Recommendations

1. **Token Storage**: Replace in-memory `_cleanup_tokens` dict with Redis
2. **Connection Pooling**: Use connection pooling for database client
3. **Async Client**: Initialize httpx.AsyncClient once and reuse (in `app.state`)
4. **Metrics**: Add Prometheus/StatsD metrics for monitoring
5. **Audit Logs**: Log all destructive operations to separate audit table
6. **Batch Operations**: Consider chunking large queries for documents endpoint
7. **Caching**: Cache stats response with 1-5 minute TTL

## Testing

See `backend/tests/` for test coverage:
- Unit tests: Mock Supabase client and httpx responses
- Integration tests: Test with real local Supabase instance
- API tests: Test via FastAPI TestClient

Example test:
```python
def test_admin_health_check(client, mock_supabase):
    response = client.get("/api/admin/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
```

## Troubleshooting

### Health check returns all services as "error"
- Verify `AGENT_SERVICE_URL` and `EMBEDDING_SERVICE_URL` are correct
- Check services are running: `curl http://localhost:8000/health`
- Check firewall/network connectivity

### Stats endpoint fails with RPC function not found
- Run `backend/scripts/add_admin_helper_functions.sql`
- Verify functions exist: `SELECT proname FROM pg_proc WHERE proname LIKE 'get_%';`

### Database cleanup token expired immediately
- Check system clock synchronization
- Verify `datetime.now(timezone.utc)` returns correct time
- Increase token expiry in code if needed

### Sources list returns empty despite having data
- Check `source` column is populated (not NULL)
- Verify RPC function or fallback aggregation logic
- Test query manually: `SELECT DISTINCT source FROM document_chunks;`

## Future Enhancements

- [ ] Bulk delete by source URL
- [ ] Export/import functionality
- [ ] Database vacuum/analyze after cleanup
- [ ] Scheduled cleanup jobs
- [ ] Webhook notifications for admin actions
- [ ] Role-based access control for different admin levels
- [ ] Activity/audit trail table

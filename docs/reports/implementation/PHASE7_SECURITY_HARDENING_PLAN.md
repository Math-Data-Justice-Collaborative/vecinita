# Phase 7: Security Hardening - Quick Reference

## Overview
Phase 7 focuses on production security patterns: auth fail-closed, rate limiting, connection pooling, and secure database query patterns.

## Tasks

### Task 1: Auth Fail-Closed Pattern
**Challenge:** Agent endpoints currently have placeholder auth that defaults to allow

**Implementation Strategy:**
1. Audit all authentication decorators (@auth_required, @admin_only)
2. Verify they raise exceptions on auth failure (not just log)
3. Add auth middleware to deny-by-default pattern
4. Test that unauthenticated requests get 401/403

**Key Files:**
- `backend/src/api/middleware.py` - Add auth fail-closed pattern
- `backend/src/api/dependencies.py` - Update auth decorators
- `backend/src/main.py` - Register auth middleware

### Task 2: Rate Limiting
**Challenge:** No rate limiting on any endpoints

**Implementation Strategy:**
1. Add slowapi or similar rate limiting library
2. Configure per-endpoint rates (e.g., /ask: 60/min, /scrape: 10/min, /admin: 1/min)
3. Implement distributed rate limiting using Redis
4. Return proper 429 (Too Many Requests) responses

**Key Files:**
- `backend/src/api/middleware.py` - Add rate limiting middleware
- `backend/src/api/config.py` - Define rate limit configs
- `backend/pyproject.toml` - Add slowapi dependency

**Suggested Rates:**
- /ask: 60 req/min (free tier)
- /scrape: 10 req/min (resource intensive)
- /admin/*: 1 req/min (sensitive operations)
- /embed/*: 100 req/min (batch processing)

### Task 3: Connection Pooling
**Challenge:** Direct Supabase queries without pooling

**Implementation Strategy:**
1. Implement connection pool for Supabase PostgreSQL
2. Configure pool size (min=5, max=20 typical)
3. Add health check endpoints for connections
4. Implement connection timeout/retry logic

**Key Files:**
- `backend/src/services/db/pool.py` - NEW: Connection pool manager
- `backend/src/services/db/client.py` - Use pooled connections
- `backend/src/api/health.py` - Add pool health checks

**Configuration:**
```python
POOL_MIN_SIZE = 5
POOL_MAX_SIZE = 20
POOL_TIMEOUT = 10  # seconds
```

### Task 4: Database Query Security
**Challenge:** Potential SQL injection or N+1 query patterns

**Implementation Strategy:**
1. Audit all database queries for parameterization
2. Add query timeout enforcement
3. Implement prepared statements where needed
4. Add database logging for debugging
5. Create index analysis for slow queries

**Key Files to Audit:**
- `backend/src/api/router_admin.py` - Document listing/deletion
- `backend/src/api/router_embed.py` - Similarity search
- `backend/src/services/agent/tools/db_search.py` - Vector search

**Security Checklist:**
- [ ] All queries use parameterized values (no string interpolation)
- [ ] All queries have timeout (max 30 seconds)
- [ ] Indexes exist on frequently queried columns
- [ ] Query plans reviewed for efficiency
- [ ] Logging captures slow queries (>5s)

## Implementation Order

**Recommended sequence (with dependencies):**
1. **Auth Fail-Closed** (independent) - Most critical, no dependencies
2. **Database Query Security** (independent) - Low-level, required before pooling
3. **Connection Pooling** (depends on #2) - Needs secure query patterns first
4. **Rate Limiting** (independent) - Can be added anytime

## Testing Strategy

### Unit Tests
```bash
# Test auth decorators
pytest tests/test_api/test_auth_decorators.py -v

# Test database queries
pytest tests/test_services/test_db_queries.py -v

# Test rate limiting
pytest tests/test_api/test_rate_limiting.py -v
```

### Integration Tests
```bash
# Test full auth flow
pytest tests/test_api/test_auth_flow.py -v

# Test under load (rate limiting)
pytest tests/test_api/test_load.py -v

# Test connection pooling behavior
pytest tests/test_services/test_connection_pool.py -v
```

### Manual Testing
```bash
# Test auth fail-closed
curl -X GET http://localhost:8002/admin/health
# Should return 401 Unauthorized

# Test rate limiting
for i in {1..70}; do
  curl -X POST http://localhost:8002/ask \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"query":"test"}'
done
# Should get 429 after 60 requests

# Test connection pool stats
curl -X GET http://localhost:8002/admin/health/pool
# Should show pool utilization
```

## Security Best Practices

### Auth Fail-Closed
✅ Do:
- Raise 401 on missing auth
- Raise 403 on insufficient permissions
- Log auth failures
- Use secure token validation

❌ Don't:
- Default to allowing requests
- Log sensitive tokens
- Use hardcoded credentials
- Skip auth on "safe" endpoints

### Rate Limiting
✅ Do:
- Implement per-endpoint rates
- Use distributed (Redis-backed) for multi-instance
- Return proper 429 responses
- Include Retry-After headers

❌ Don't:
- Use simple in-memory counters
- Allow unlimited burst traffic
- Block IPs permanently
- Use overly restrictive rates

### Connection Pooling
✅ Do:
- Set bounds (min/max pool size)
- Implement health checks
- Log connection issues
- Test connection exhaustion

❌ Don't:
- Use unbounded connection counts
- Ignore connection timeouts
- Leak connections
- Mix pooled and unpooled connections

### Database Security
✅ Do:
- Use parameterized queries
- Add query timeouts
- Log slow queries
- Review query plans

❌ Don't:
- Concatenate user input into queries
- Allow infinite query runtime
- Ignore database errors
- Skip index optimization

## Documentation to Update

After Phase 7 completion:
- [ ] `docs/SECURITY.md` - New security hardening guide
- [ ] `backend/README.md` - Update with security features
- [ ] `CHANGELOG.md` - Add Phase 7 completion notes
- [ ] `.env.example` - Add new config variables

## Rollback Strategy

Each task should be independently revertible:
- Auth changes: Revert middleware registration
- Rate limiting: Disable slowapi middleware
- Connection pooling: Switch to direct Supabase client
- Query audit: Revert to original queries

## Success Criteria

Phase 7 is complete when:
1. ✅ All unauthenticated requests to /admin/* get 401
2. ✅ All unauthorized requests to /admin/* get 403
3. ✅ Rate limiting returns 429 after limits exceeded
4. ✅ Connection pool metrics available via /admin/health/pool
5. ✅ All database queries use parameters
6. ✅ Slow query logging enabled (>5s threshold)
7. ✅ 100% of tests pass
8. ✅ Documentation updated

## Estimated Effort
- Auth Fail-Closed: ~2 hours
- Rate Limiting: ~3 hours
- Connection Pooling: ~4 hours
- Database Security: ~3 hours
- **Total: ~12 hours**

---

**Status:** Ready to begin Phase 7
**Previous Phase:** Phase 6 ✅ Complete (VecinaScraper integration)
**Next Phase:** Phase 8 (Tool & config cleanup)


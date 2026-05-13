# Technical Decisions: Gateway
> Auto-generated: 2026-05-12

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Web framework | FastAPI | Flask, Django, Starlette | Pre-2026 | Moderate |
| TD-002 | HTTP client | httpx (async) | aiohttp, requests | Pre-2026 | Easy |
| TD-003 | Modal invocation pattern | `Function.from_name().remote()` | HTTP to *.modal.run | 2026 | Easy |
| TD-004 | Database driver | psycopg2 (sync) | asyncpg, SQLAlchemy async | Pre-2026 | Moderate |
| TD-005 | Rate limiting | In-memory per-process | Redis, PostgreSQL | Pre-2026 | Easy |
| TD-006 | Auth model | Local Bearer token validation | Supabase Auth, OAuth2 | Pre-2026 | Easy |
| TD-007 | Correlation tracking | Middleware-injected X-Correlation-ID | OpenTelemetry trace context | 2026 | Easy |
| TD-008 | Scraper job persistence | Gateway-owned Postgres rows | Modal-only state | 2026 | Moderate |
| TD-009 | SSE streaming | Raw byte forwarding (no parsing) | Event parsing + re-serialization | Pre-2026 | Easy |

### TD-001: FastAPI over Flask/Django
**Context**: Need async HTTP framework with automatic OpenAPI generation.
**Decision**: FastAPI for native async, Pydantic validation, auto-generated docs.
**Rationale**: Aligns with async httpx client and SSE streaming. Auto-OpenAPI critical for Schemathesis contract testing.
**Consequences**: Tightly coupled to Pydantic v2 and Starlette internals.

### TD-003: Modal Function Invocation over HTTP
**Context**: Embedding/scraper services deployed on Modal. Initially called via HTTP to `*.modal.run` endpoints.
**Decision**: Use Modal SDK `Function.from_name()` for direct function invocation.
**Rationale**: Avoids cold-start latency of HTTP endpoints, better auth model, function-level error handling. Policy enforcement at startup ensures consistency.
**Consequences**: Requires Modal tokens on Render, adds `asyncio.to_thread()` wrapper for sync SDK.

### TD-004: psycopg2 (sync) over asyncpg
**Context**: Database access needed for documents and job persistence.
**Decision**: Use synchronous psycopg2 with per-request connections.
**Rationale**: Simpler integration, no connection pool management. Documents endpoints are read-heavy with bounded queries.
**Consequences**: Blocks event loop during queries (mitigated by 30s statement timeout).

### TD-005: In-memory Rate Limiting
**Context**: Need per-endpoint rate limiting.
**Decision**: In-memory dict tracking per API key.
**Rationale**: Simple, no infrastructure dependency. Acceptable for single-instance deployment.
**Consequences**: State lost on restart, not shared across multiple instances.

### TD-008: Gateway-Owned Scraper Job Persistence
**Context**: Modal scraper workers need persistent job state visible to frontends.
**Decision**: Gateway persists `scraping_jobs` to Postgres, Modal workers call back via internal pipeline endpoints.
**Rationale**: Centralizes job state in Render Postgres (always reachable), avoids Modal Dict latency for status polling.
**Consequences**: Requires `DATABASE_URL` and `SCRAPER_API_KEYS` on gateway.

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | Connection pooling | asyncpg pool, psycopg2 pool | Performance under load | Medium — per-request connect adds latency | asyncpg with pool |
| PTD-002 | Rate limit backend | Redis, PostgreSQL | Multi-instance scaling | High — current in-memory won't work with scale-out | Redis |
| PTD-003 | HTTP client lifecycle | Lifespan-managed, lazy singleton | Resource leaks | Low — current singleton works | Lifespan-managed |
| PTD-004 | Scrape router optional deps | Separate package, feature flag | Import errors on minimal installs | Low | Feature flag |

### PTD-001: Database Connection Pooling
**Context**: `psycopg2.connect()` per request in `router_documents.py`. TODO in `main.py` lifespan mentions "Database connection pool".
**Why it matters**: Under load, per-request TCP connections add ~5-10ms overhead and risk exhausting Postgres connection limits.
**Options researched**:
- **asyncpg pool**: Native async, connection pooling built-in. Requires rewriting SQL to use `$1` params. Effort: medium.
- **psycopg2 pool** (`psycopg2.pool.ThreadedConnectionPool`): Drop-in, but still sync. Effort: low.
- **SQLAlchemy async**: Full ORM, heaviest lift. Effort: high.
**Recommendation**: asyncpg with pool for long-term, psycopg2 pool as interim.
**Risk of continued deferral**: Connection exhaustion under concurrent document queries.
**Decision deadline**: Before multi-instance scaling on Render.

### PTD-002: Rate Limit Backend
**Context**: `RateLimitingMiddleware` uses `self.rate_limit_state: dict` (in-memory). Comment in middleware: "TODO: Move to Redis for production/multi-instance deployment".
**Why it matters**: Multiple Render instances won't share rate limit state, allowing limit bypass.
**Options researched**:
- **Redis**: Fast, standard for rate limiting, supports sliding windows. Effort: medium.
- **PostgreSQL**: Already available, but adds write load. Effort: low.
**Recommendation**: Redis (add as Render Redis instance).
**Risk of continued deferral**: Rate limits ineffective once gateway scales beyond one instance.
**Decision deadline**: Before scaling to 2+ instances.

### PTD-003: HTTP Client Lifecycle
**Context**: `_AGENT_CLIENT` is a lazy singleton with a thread lock. TODO in lifespan: "Initialize service clients" and "Close HTTP clients".
**Why it matters**: Proper lifecycle prevents connection pool leaks on shutdown.
**Options researched**:
- **Lifespan-managed**: Create in startup, close in shutdown. Clean but requires refactoring global.
- **Current lazy singleton**: Works but never explicitly closed.
**Recommendation**: Lifespan-managed with dependency injection.
**Risk of continued deferral**: Low — httpx handles cleanup reasonably.
**Decision deadline**: Next refactoring pass.

### PTD-004: Optional Scraper Dependencies
**Context**: `router_scrape.py` import is wrapped in `try/except ModuleNotFoundError` because `langchain_community` is optional.
**Why it matters**: Import-time error handling is fragile; affects startup reliability.
**Options researched**:
- **Separate package**: Move scraper to its own service entirely.
- **Feature flag**: `ENABLE_SCRAPE_ROUTER=true` env var to skip import.
**Recommendation**: Feature flag (aligns with Modal-first scraping direction).
**Risk of continued deferral**: Low — current `try/except` works.

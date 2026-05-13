# Data Management API — Technical Decisions

> Auto-generated: 2026-05-12

## Overview

Key architectural and technical decisions for the data-management API, including
both resolved decisions and pending choices identified from the codebase.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Service architecture pattern | Thin proxy / BFF | Full CRUD service, GraphQL gateway | 2024 | moderate |
| TD-002 | Runtime image for Render | Scraper Dockerfile (not DM API's own) | DM API Dockerfile, separate image | 2024 | easy |
| TD-003 | Modal vs HTTP routing | Dual-mode via `MODAL_FUNCTION_INVOCATION` | Modal-only, HTTP-only | 2024 | easy |
| TD-004 | Conflict resolution strategy | Deterministic last-writer-wins | CRDT, vector clocks, manual merge | 2024 | moderate |
| TD-005 | Submodule removal (003-consolidate) | Remote HTTP clients replace nested submodules | Keep submodules, monorepo copy | 2024 | hard |

### TD-001: Thin Proxy / BFF Architecture

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2024 |
| Context | The SPA needs a single HTTP origin for CORS-safe access to scraper, embedding, and model services |
| Decision | Build a lightweight FastAPI proxy that forwards requests rather than implementing domain logic |
| Rationale | Minimizes code duplication; all business logic lives in the upstream services |
| Alternatives considered | Full CRUD service with its own Postgres access (rejected: duplicates scraper logic), GraphQL gateway (rejected: over-engineering for current scale) |
| Consequences | DM API is tightly coupled to scraper API shape; any scraper API change requires proxy updates |
| Reversibility | moderate — migration to full service would require extracting logic from scraper |

### TD-002: Scraper Dockerfile for Render

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2024 |
| Context | After removing nested submodules (003-consolidate), the DM API image needs the scraper codebase |
| Decision | Build the Render image from `modal-apps/scraper/Dockerfile` and run `vecinita_scraper.api.server:create_app` |
| Rationale | Avoids maintaining a separate Dockerfile that clones the scraper repo at build time; the monorepo already has the scraper source |
| Alternatives considered | DM API's own `Dockerfile` which clones scraper at build time (exists but used for standalone repo clones) |
| Consequences | The Render service runs the scraper's FastAPI app, not the DM API app factory — DM API's `apps/backend/` code is only used in standalone/test contexts |
| Reversibility | easy — switch `dockerfilePath` in `render.yaml` |

### TD-003: Dual-Mode Modal/HTTP Routing

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2024 |
| Context | Services can run on Modal (serverless) or as standalone HTTP services; the DM API needs to call either |
| Decision | `MODAL_FUNCTION_INVOCATION` env var controls routing: `auto` checks for token pair, `1` forces SDK, `0`/`http` forces HTTP |
| Rationale | Supports local development (HTTP) and production (Modal SDK) without code changes |
| Alternatives considered | Modal-only (rejected: breaks local dev), HTTP-only (rejected: loses Modal benefits) |
| Consequences | Extra complexity in each service client; must keep both paths tested |
| Reversibility | easy — can lock to either mode via env var |

### TD-004: Corpus Conflict Resolution

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2024 |
| Context | Multiple writers (scraper workers) can produce overlapping corpus updates |
| Decision | Deterministic last-writer-wins by `updated_at`, tie-break by `document_id` |
| Rationale | Simple, predictable, no coordination overhead |
| Alternatives considered | CRDTs (rejected: overkill for current scale), vector clocks (rejected: complexity) |
| Consequences | Concurrent writes may lose data if timestamps collide (mitigated by `document_id` tie-break) |
| Reversibility | moderate |

### TD-005: Submodule Consolidation (003)

| Property | Value |
|----------|-------|
| Status | accepted |
| Date | 2024 |
| Context | Nested git submodules for scraper/embedding/model under `apps/backend/` caused checkout and CI complexity |
| Decision | Remove submodules; use `service-clients` package with typed HTTP clients pointing at remote URLs (`SCRAPER_SERVICE_BASE_URL`, etc.) |
| Rationale | Simplifies repo layout, reduces checkout time, enables independent deployment |
| Alternatives considered | Keep submodules (rejected: CI pain), copy source into monorepo (rejected: duplication) |
| Consequences | Cross-service calls require network connectivity even in local dev; `docker-compose` needed for full-stack testing |
| Reversibility | hard — would require re-adding submodules and rewiring imports |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | Unify DM API and scraper runtime images | A: Keep separate, B: Merge into one app | Maintainability, deployment simplicity | Medium — two app factories serve overlapping surfaces | B: Merge |
| PTD-002 | Add retry logic to service clients | A: Client-side retries, B: Proxy-level retries, C: Leave to caller | Reliability under transient failures | Low-medium — currently a single failure = 503 | A: Client-side with tenacity |
| PTD-003 | API versioning strategy | A: URL prefix (`/v2/`), B: Header-based, C: Defer | Breaking change management | Low now, high at scale | A: URL prefix |

### PTD-001: Unify DM API and Scraper Runtime Images

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | `render.yaml` builds from `modal-apps/scraper/Dockerfile` and runs `vecinita_scraper.api.server:create_app`, while `apis/data-management-api/apps/backend/` has its own app factory that is only used in tests |
| Impact | Maintainability — two FastAPI apps serve overlapping concerns; risk of divergence |
| Decision deadline | Before next major feature addition |

**Options researched:**

**Option A: Keep separate** — DM API app factory remains for standalone/test use; Render runs scraper image
- Pros: No migration effort; clear separation of concerns
- Cons: DM API `apps/backend/` code is effectively dead in production
- Effort: S
- Reversibility: easy

**Option B: Merge into single app** — Combine DM API proxy routes into the scraper's FastAPI app
- Pros: Single source of truth; fewer deployment artifacts
- Cons: Larger scraper codebase; harder to reason about responsibilities
- Effort: M
- Reversibility: moderate

**Recommendation:** Option B — the current situation has two apps with overlapping `/jobs` surfaces, which is confusing.
**Risk of continued deferral:** DM API `apps/backend/` code drifts from production behavior.

### PTD-002: Add Retry Logic to Service Clients

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | `ScraperClient`, `EmbeddingClient`, `ModelClient` all use a single `httpx.AsyncClient` request with no retries — any transient failure returns an error immediately |
| Impact | Reliability — Modal cold starts and network blips cause 503s |
| Decision deadline | Before production traffic increases |

**Options researched:**

**Option A: Client-side retries with tenacity**
- Pros: Simple, per-client retry policies, well-tested library
- Cons: Adds latency on failure paths
- Effort: S
- Reversibility: easy

**Option B: Proxy-level retries (middleware)**
- Pros: Centralized policy
- Cons: May retry non-idempotent POSTs unsafely
- Effort: M
- Reversibility: moderate

**Option C: Leave to caller**
- Pros: No code changes
- Cons: SPA gets raw 503s on transient failures
- Effort: none
- Reversibility: n/a

**Recommendation:** Option A — client-side retries with exponential backoff for GET and idempotent operations.
**Risk of continued deferral:** Users see intermittent failures during Modal cold starts.

### PTD-003: API Versioning Strategy

| Property | Value |
|----------|-------|
| Status | pending |
| Identified | 2026-05-12 |
| Evidence | Service name includes `v1` but no code-level versioning; no strategy for breaking changes |
| Impact | Breaking change management as API evolves |
| Decision deadline | Before first breaking API change |

**Recommendation:** Option A (URL prefix `/v2/`) — simple, explicit, compatible with Render routing.
**Risk of continued deferral:** Low risk now, high risk when the first breaking change arrives.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)

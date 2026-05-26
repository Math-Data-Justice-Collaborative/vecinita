# ADR-017: EV-002 Implementation Decisions

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-05-26 |
| Stage | 04-tech-plan (EV-002) |
| Deciders | User (product owner) |
| Context | F23–F29 (Admin overhaul, bulk ops, usage stats, audit log) |

## Context

EV-002 introduces six features (F23–F29) covering admin UI modernization, bulk operations,
serving statistics, and an audit log with version history. This ADR records the 12 technical
decisions made during the 04-tech-plan interview for EV-002.

## Decisions

### TP-018: Tailwind CSS v3

**Decision:** Use Tailwind CSS v3 with PostCSS plugin + `tailwind.config.js`.

**Rationale:** Mature ecosystem; well-documented shadcn/ui integration recipes; stable API.
Tailwind v4 (CSS-first config) is too new for production shadcn/ui templates.

**Consequences:** Requires `postcss.config.js` + `tailwind.config.js` in the admin frontend.

### TP-019: Health aggregator on internal-write-api

**Decision:** Single `GET /internal/v1/health/all` endpoint that backend-polls all services
and returns unified status. Admin frontend calls only this one endpoint.

**Rationale:** Avoids the Modal CORS issue (H4 waiver for `requires_proxy_auth`). Backend
can use `httpx` to poll services without browser CORS constraints.

**Consequences:** Internal-write-api needs service URLs as env vars; single point of failure
for health display (acceptable — the aggregator itself is behind the same DO network).

### TP-020: Real-time SQL aggregation for stats

**Decision:** `GET /internal/v1/stats/summary` executes SQL aggregation queries on each
request — no caching or materialized views.

**Rationale:** Pilot scale (<10k documents) makes real-time queries fast enough. Avoids
complexity of cache invalidation or materialized view refresh scheduling.

**Consequences:** If corpus grows significantly, may need caching (future optimization).

### TP-021: React Router v7

**Decision:** Use `react-router` v7 (latest stable) for admin frontend navigation.

**Rationale:** Latest stable version; backward-compatible with v6 patterns; Remix-style data
loading available if needed in future.

**Consequences:** New dependency; existing single-page `App.tsx` refactored to route structure.

### TP-022: Async fire-and-forget serving stats

**Decision:** Chat-rag-backend fires an async `POST /internal/v1/stats/served` via httpx
background task after successful RAG response. Failure does not affect the user's response.

**Rationale:** Zero added latency to the RAG response path. Eventual consistency is
acceptable for analytics counters.

**Consequences:** Possible missed increments on network failure (acceptable for pilot);
no retry mechanism needed in v1.

### TP-023: Explicit audit helper calls

**Decision:** Each write endpoint explicitly calls `emit_audit_event(...)` at the point
of mutation — no magic middleware or DB triggers.

**Rationale:** Most control over what gets logged; readable; testable; clear in code review.
DB triggers are harder to test and version-control.

**Consequences:** Some boilerplate in each write endpoint (acceptable for explicitness).

### TP-024: Best-effort partial success for bulk operations

**Decision:** Bulk operations process each document independently. Report `successes` and
`failures` arrays in the response rather than rolling back everything on one failure.

**Rationale:** More useful for operators — they see which items failed and can retry those
specifically. Atomic all-or-nothing would force operators to retry the entire batch.

**Consequences:** Response schema includes `successes: int` + `failures: [{id, error}]`.
Each successful item emits its own audit event.

### TP-025: Version snapshots on audit events

**Decision:** A new `document_versions` row is created on every audit event that changes
document metadata or tags (tied to the audit emission).

**Rationale:** Automatic; no separate "version creation" code path; version history is a
natural by-product of the audit system.

**Consequences:** Version rows may accumulate — covered by retention policy (TP-027).
Version 1 is created on `document.created` event (initial snapshot).

### TP-026: shadcn/ui via npx init

**Decision:** Use `npx shadcn-ui@latest init` standard installation, generating
`src/components/ui/` directory with copy-pasted component source.

**Rationale:** Standard approach; components are fully owned and customizable; no runtime
dependency on shadcn package.

**Consequences:** Adds ~10 component files to the admin frontend source tree.

### TP-027: Background cleanup job for audit retention

**Decision:** A daily background job deletes audit_log and document_versions entries older
than `VECINITA_AUDIT_RETENTION_DAYS` (default 365).

**Rationale:** Prevents unbounded table growth. Background job is non-blocking.

**Consequences:** Need a cron trigger — can use Modal scheduled function or DO cron job.
Implementation in M30.

### TP-028: Vitest + Testing Library for frontend tests

**Decision:** Frontend component tests use Vitest + `@testing-library/react` — one test
file per new page/component.

**Rationale:** Consistent with existing test setup (JobForm.test.tsx pattern). Fast and
sufficient for component-level validation.

**Consequences:** MSW not used in v1 — API responses mocked via `vi.mock()` or prop injection.

### TP-029: Sequential deploy order

**Decision:** Deploy EV-002 in strict order:
1. Alembic migration (create new tables)
2. Redeploy internal-write-api (new endpoints)
3. Redeploy chat-rag-backend (stats POST integration)
4. Redeploy admin frontend (full UI overhaul)

**Rationale:** Each step depends on the previous: frontend needs endpoints, endpoints need
tables, stats integration needs the stats endpoint to exist.

**Consequences:** Deployment takes 4 steps (~10-15 minutes total); rollback is
per-component in reverse order.

## References

- ADR-016: Audit log no-IP
- ADR-004: Zero personal data
- Feature list: F23–F29
- Spec.md §DO internal write API (EV-002 extensions)
- Context brief §12 (EV-002 resolutions R20–R27)

# EV-012 impact analysis (#116)

## Features

| ID | Change |
|----|--------|
| F32 | Extend: unified Modal list, detail route, status filter, retag `document_id`, SSE, admin CRUD, log links |
| F36 | Extend: eval lifecycle on Modal (`job_type=eval`); metrics stay in DO Postgres; Jobs detail → eval drill-down |

No new Fn (S013-D3).

## Docs to update (delta)

| Doc | Why |
|-----|-----|
| `docs/feature-list.md` | F32/F36 EV-012 deltas |
| `docs/api-contract.md` | `/jobs` fields, events SSE, cancel/retry; eval enqueue note |
| `openapi/data-management.yaml` | Job schema + events (+ cancel) |
| `openapi/internal-write.yaml` | Eval trigger → Modal bridge |
| `docs/user-journeys.md` | UJ-023, UJ-044, UJ-050 |
| `docs/test-plan.md` | TC-146–151 |
| `docs/acceptance-criteria.md` | AC-J1–J10 |
| `docs/adr/ADR-038-*.md` | Modal job lifecycle + DO storage SoT |
| Session execution plan (under S013) | Tasks for 07-build |

## Code / apps

| Area | Touch |
|------|-------|
| `apps/data-management-frontend` | JobsPage Modal list + SSE, `/jobs/:id`, filters, cancel/retry UI |
| `apps/data-management-backend` | `document_id`, `/jobs/events`, cancel/retry, log metadata, `job_type=eval` |
| `apps/internal-write-api` | Trigger eval → enqueue Modal job; keep metrics APIs |
| `tests/e2e/` | UJ-023 / UJ-044 / UJ-050 |
| Vitest + Playwright | Jobs list + detail |

## Connectivity

Admin SPA only. No ChatRAG.

## Risks

- SSE reliability; poll fallback (RD-173).
- Eval enqueue bridge Modal ↔ DO metrics rows.
- Cancel/retry vs eval result row ownership.
- Lean+build skips formal 09/11/12 — rely on 08 + 10 + 13.

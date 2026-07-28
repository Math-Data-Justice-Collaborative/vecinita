# EV-012 impact analysis (#116)

## Features

| ID | Change |
|----|--------|
| F32 | Extend: unified list, detail route, status filter, retag `document_id`, SSE, cancel/retry, logs link, Postgres/SoT |
| F36 | Extend: eval runs visible on Jobs; detail summary + drill-down link; eval SSE |

No new Fn (S013-D3).

## Docs to update (delta)

| Doc | Why |
|-----|-----|
| `docs/feature-list.md` | F32/F36 delta limitations → capabilities |
| `docs/api-contract.md` | `/jobs` fields, events SSE, cancel/retry; eval events |
| `openapi/data-management.yaml` | Job schema + events (+ cancel) |
| `openapi/internal-write.yaml` | Eval list/events; cancel if applicable |
| `docs/user-journeys.md` | Extend UJ-023; detail + eval federation |
| `docs/test-plan.md` | TC for unified list, detail, SSE, cancel |
| `docs/acceptance-criteria.md` | Mirror #116 ACs + SSE |
| `docs/adr/` | Likely new ADR: SSE + SoT (modal.Dict vs Postgres) |
| Session execution plan (under S013) | Tasks for 07-build |

## Code / apps

| Area | Touch |
|------|-------|
| `apps/data-management-frontend` | JobsPage federation, `/jobs/:id`, filters, SSE clients, cancel/retry UI |
| `apps/data-management-backend` | Job payload (`document_id`), `GET /jobs/events`, cancel/retry, log link metadata |
| `apps/internal-write-api` | Eval runs list shape if needed; eval SSE; cancel if eval-owned |
| `tests/e2e/` | Extend UJ-023 / unified jobs |
| Vitest | Jobs list + detail journeys |

## Connectivity

Admin SPA only (gates 01/04 delta, 07, 12–13 / H4–H5 when UI ships). No ChatRAG.

## Risks

- Dual-source SSE + federation complexity; poll fallback needed if SSE drops.
- Postgres SoT vs modal.Dict — product/ADR decision in 04.
- Cancel/retry across Modal vs DO eval — different ownership.
- Lean+build skips formal 09/11/12 — rely on 08 + 10 + 13.

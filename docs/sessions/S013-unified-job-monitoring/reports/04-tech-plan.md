# 04-tech-plan — EV-012 / S013 Unified Admin Jobs

**Date:** 2026-07-28  
**Mode:** delta (Lean+build — 05/06 skipped)  
**Branch:** `evolve/EV-012-unified-job-monitoring`

## Summary

Technical plan for #116: Modal job lifecycle SoT, DO metrics storage, SSE on both Modal jobs and
DO eval progress, admin CRUD, eval enqueue bridge, soft-delete `eval_runs.deleted_at`.

## Locked decisions

| ID | Decision |
|----|----------|
| TP-S013-01 | OpenAPI: `/jobs/events`, cancel/retry/delete, Job extras |
| TP-S013-02 | Keep DictJobStore + modal.Dict |
| TP-S013-03 | DELETE + soft-delete linked eval_runs |
| TP-S013-04 | DO `…/eval/runs/{id}/events` + Modal `/jobs/events` |
| TP-S013-05 | `deleted_at` soft-delete |
| TP-S013-06 | Keep M3 — `enqueue_eval` (ISS-005 resolved) |
| TP-S013-07 | cancelled + best-effort FunctionCall.cancel() |
| TP-S013-08 | Phase 19 / M82–M85 |

## Deliverables

| Artifact | Path |
|----------|------|
| Execution plan Phase 19 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Session roadmap | `docs/sessions/S013-unified-job-monitoring/roadmap.md` |
| OpenAPI DM | `openapi/data-management.yaml` |
| OpenAPI IW | `openapi/internal-write.yaml` |
| API contract | `docs/api-contract.md` §EV-012 |
| ADR-038 | amended §9–12 |
| Decisions | `docs/decisions.md` TP-S013-01–08 |

## Execution plan shape

| Milestone | Focus | Tasks |
|-----------|-------|-------|
| M82 | Modal API + store + OpenAPI | T82.1–T82.6 |
| M83 | Eval enqueue + DO SSE + soft-delete | T83.1–T83.6 |
| M84 | Admin Jobs UI | T84.1–T84.6 |
| M85 | API e2e + Playwright | T85.1–T85.5 |

## Connectivity / UI tests

- No new CORS origins (RD-175)
- Playwright T0-ui: `tests/ui/admin/uj050-job-detail.spec.ts` (+ uj023/uj044)
- CORS H0c for new `/jobs/*` routes (T85.4)
- Existing `make test-ui` / `ui-e2e` CI — no new deps (06 skipped)

## Next

User review of Phase 19 → complete 04 → **07-build** (Lean+build skips 05).

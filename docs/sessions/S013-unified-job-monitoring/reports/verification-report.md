# Verification report — EV-012 M84 (Admin Jobs UI)

**Session:** S013-unified-job-monitoring  
**Branch:** `evolve/EV-012-unified-job-monitoring`  
**Date:** 2026-07-28  
**Milestone:** M84 (T84.1–T84.6)  
**HEAD tip:** `a351a13`

## Result

**PASS** (scoped) — M84 Admin Jobs UI Vitest + jobs/admin client tests green; ruff clean.

## Checks

| Check | Result | Notes |
|-------|--------|-------|
| Ruff (`apps packages tests infra scripts`) | PASS | `make check-fast` ruff portion |
| FE ESLint (changed Jobs/Eval files) | PASS | Pre-existing react-refresh warnings only |
| Vitest M84 suites | PASS | `test_uj023_uj050_jobs_monitoring`, `test_uj050_job_detail_crud`, `test_jobs_page`, `test_job_management_navigation`, `jobs.test`, `admin.test` (subscribeEvalRunEvents) |
| `make check-fast` full | PARTIAL | FE lint aborted: local Node 22 vs required Node ≥24 (`.nvmrc`) — not a code failure |

## Delivered (M84)

- Jobs list: status filter (`?status=`), retag `document_id`, row → `/jobs/:id`
- Fetch-authenticated SSE `/jobs/events` + 4s poll fallback + SSE retry backoff
- `JobDetailPage`: admin cancel/retry/delete; viewer read-only; Modal call id copy + dashboard link
- Evaluation: DO `/eval/runs/{id}/events` preferred over tight poll; metrics via detail GET

## Next

- **T85.1+** — API e2e + Playwright (M85)
- Re-run full `make check-fast` / `make ci-push` under Node 24 before PR updates
- PR #153 remains open (`do_not_merge` until phase ready)

## Connectivity artifacts

| Artifact | Present |
|----------|---------|
| `tests/unit/test_cors_policy.py` | yes (H0c; M85 T85.4 extends if needed) |
| Staging connectivity scripts | unchanged |

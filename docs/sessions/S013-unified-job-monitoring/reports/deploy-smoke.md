# Deploy & Smoke Report — EV-012 Unified Admin Jobs (S013)

> **Date:** 2026-07-29  
> **Session:** S013-unified-job-monitoring  
> **Cycle:** EV-012  
> **Stage:** 13-deploy-smoke  
> **Status:** **deployed** — Path A PASS; #153 merged; DO pins reset to `main`  
> **Branch:** `main` @ `6940770` (Path A smokes were on evolve @ `1135891`)

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| CI (`ci.yml`) | **PASS** | [run 30454245590](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/30454245590) @ `1135891` |
| H0c CORS | **PASS** | `pytest tests/unit/test_cors_policy.py` (local + `verify_connectivity.sh`) |
| Alembic | **PASS** | Staging upgraded `20260707_0008` → `20260728_0009` (EV-012 `eval_runs.deleted_at`) |
| 12-verify-deploy | **waived** | Lean+build S013-D22 |

## Deployment (Path A)

| Step | Action | Result |
|------|--------|--------|
| Modal `vecinita-data-management` | `uv run modal deploy infra/modal/data_management_app.py` | **SUCCESS** — https://vecinita--vecinita-data-management-fastapi-app.modal.run |
| DO `vecinita-internal-write-api` | Pin `github.branch` → evolve branch + force deploy | **ACTIVE** |
| DO `vecinita-admin-frontend` | Pin `github.branch` → evolve branch + force deploy | **ACTIVE** |
| ChatRAG DO apps | Untouched (remain on prior pin/`main`) | n/a |

**Post-merge (2026-07-29):** PR [#153](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/153) merged; DO `github.branch` for write-api + admin FE reset to `main` (both ACTIVE). H0ci PASS on `6940770`.

## Smoke Tests

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG + write `/health`; Modal deps ok |
| H2 DB + Alembic head | **PASS** | `20260728_0009` |
| H3 RAG ask | **PASS** | Answer returned (~55s wall; macOS `date +%s%3N` latency line noisy) |
| H3b Browse | **PASS** | documents + tags |
| T3 EV-002 admin API | **PASS** | `test_staging_ev002_admin.py` live 4/4 |
| H0c + H4/H5 | **PASS** | `verify_connectivity.sh` |
| Jobs list (Modal) | **PASS** | JWT + `X-Vecinita-Proxy-Key`; 25 jobs incl. `eval` + `retag` |
| Jobs detail (retag) | **PASS** | `GET /jobs/{id}` |
| Eval run detail (write) | **PASS** | `GET /internal/v1/eval/runs/{id}` |
| Jobs SSE | **PASS** | `GET /jobs/events` → `event: job` frames |
| Admin FE bundle | **PASS** | `/jobs` + JobDetail strings in built JS |
| Eval SSE OpenAPI | **PASS** | `/internal/v1/eval/runs/{run_id}/events` registered |

## URLs (unchanged hosts)

| Service | URL | Source SHA / branch |
|---------|-----|---------------------|
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run | local deploy @ `1135891` |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app | `main` |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app | `main` |

## Rollback

1. Reset DO `github.branch` to `main` for write-api + admin FE; force redeploy.  
2. `modal deploy` data-management from last known-good `main` SHA.  
3. Optional: Alembic downgrade of `20260728_0009` only if soft-delete column must be removed (prefer leave column).

## Gate / next

- **13-deploy-smoke:** Path A smokes green.  
- **PR #153:** merged; DO pins on `main`; H0ci PASS.  
- **Close:** EV-012 completed (user chose skip optional 15-service-health).

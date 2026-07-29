# Deploy & Smoke Report — EV-013 Admin UI polish (S014)

> **Date:** 2026-07-29  
> **Session:** S014-admin-ui-polish-148  
> **Cycle:** EV-013  
> **Stage:** 13-deploy-smoke  
> **Status:** **deployed** — Path A PASS (FE-only); awaiting merge approval for PR #154  
> **Branch:** `evolve/EV-013-admin-ui-polish-148` @ `f85b6ab` (smokes @ pin `72747f5`+; coverage fix `f85b6ab`)

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| H0c CORS | **PASS** | `pytest tests/unit/test_cors_policy.py` + `verify_connectivity.sh` |
| 10-e2e T0/T0-ui | **PASS** | UJ-051 Vitest + Playwright `uj051` |
| 12-verify-deploy | **waived** | Lean+build (same as S013-D22) |
| CI (`ci.yml`) | **PASS** (after coverage fix) | PR [#154](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/154) — coverage gap in `BoundedTagList` empty path fixed @ `f85b6ab` |

## Deployment (Path A — FE-only)

| Step | Action | Result |
|------|--------|--------|
| Push evolve branch | `git push -u origin HEAD` | **SUCCESS** |
| PR | Open #154 → `main` | **OPEN** |
| DO `vecinita-admin-frontend` | Pin `github.branch` → `evolve/EV-013-admin-ui-polish-148` + force deploy | **ACTIVE** (`d0595145-…`) |
| Modal / write-api / ChatRAG | Untouched (no backend delta) | n/a |

## Smoke Tests

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG + write `/health`; Modal deps ok |
| H2 DB + Alembic head | **PASS** | pool + head match |
| H3 RAG ask | **PASS** | Answer + sources (macOS `date +%s%3N` latency line noisy — same as S013) |
| H3b Browse | **PASS** | documents + tags |
| H0c + H4/H5 | **PASS** | `verify_connectivity.sh` |
| Admin FE bundle | **PASS** | Live JS contains `corpus-table-scroll`, `corpus-tags-more`, `corpus-title-` |

## URLs

| Service | URL | Source |
|---------|-----|--------|
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app | pin evolve/EV-013 |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app | `main` (unchanged) |
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run | unchanged |
| ChatRAG | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app | unchanged |

## Rollback

1. Reset DO `github.branch` to `main` for `vecinita-admin-frontend`; force redeploy.  
2. Close or revert PR #154.

## Gate / next

- **13-deploy-smoke:** Path A smokes green (FE-only pin).  
- **PR #154:** open — **do not merge** without explicit user approval.  
- After merge: reset DO admin FE pin → `main`; watch H0ci on `main`.  
- Optional: 15-service-health / 17-retrospective.

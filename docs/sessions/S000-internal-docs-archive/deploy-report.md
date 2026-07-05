# Deploy Report

> Date: 2026-05-27
> Status: **deployed**
> Version: 0.3.0 (EV-002)
> Commit: `0a2f813` (branch `evolve/EV-002-admin-overhaul`)

## Pre-Deploy

- Checklist: ready (`docs/deploy-checklist.md`, 2026-05-27)
- T0 e2e (not live): PASS
- H0c CORS: PASS (incl. `test_cors_ev002.py` TC-060)
- verify_build: PASS
- Staging DB: `20260526_0003` (head) — migration confirmed

## Deployment (EV-002 — TP-029)

| Step | Command / action | Result |
|------|------------------|--------|
| Database | `alembic upgrade head` → `20260526_0003` | SUCCESS (prior + verified 2026-05-27) |
| internal-write-api | DO deploy @ `0a2f813` (`evolve/EV-002-admin-overhaul`) | SUCCESS — ACTIVE |
| chat-rag-backend | DO deploy @ `0a2f813` | SUCCESS — ACTIVE |
| data-management-frontend | DO deploy @ `0a2f813` | SUCCESS — ACTIVE |
| Modal (3 apps) | Not required for EV-002 | N/A (ADR-017) |

**Note:** DO apps deployed from `evolve/EV-002-admin-overhaul` (not `main`). Local HEAD `98bb7f8` is 2 commits ahead of deployed `0a2f813`; merge to `main` recommended for spec parity (`infra/do/*.yaml` still reference `main`).

## Smoke Tests (2026-05-27 validation)

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG + write `/health` 200 |
| H2 DB + Alembic head | **PASS** | `20260526_0003` |
| H3 RAG ask | **PASS** | ~77s (cold LLM) |
| H3b Browse | **PASS** | documents + tags |
| T3 EV-002 admin API | **PASS** | 4/4 (`test_staging_ev002_admin.py`) |
| H0c CORS (local) | **PASS** | 19 tests |
| H4 CORS (live) | **PASS** | incl. EV-002 bulk/stats/audit preflights |
| H4 Modal data-mgmt | **WAIVER** | `requires_proxy_auth` (EV-001 user-approved) |
| H5 Frontend bundles | **PASS** | chat + admin hosts in JS bundles |

## Health Check

- All 4 DO apps: ACTIVE
- EV-002 routes live: `/internal/v1/stats/summary`, `/health/all`, `/audit`, bulk ops
- Error rate: 0% on smoke paths
- LLM cold-start: elevated H3 latency on first ask after scale-down

## URLs

| Service | URL |
|---------|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| ChatRAG frontend | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |
| Modal embedding | https://vecinita--vecinita-embedding-embedding-api.modal.run |
| Modal LLM | https://vecinita--vecinita-llm-fastapi-app.modal.run |
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run |

## Operator spec files (local only — gitignored)

Export with `doctl apps spec get <app-id> -o yaml > <name>-spec.yaml` for operator reference.
These paths are in `.gitignore` and must **never** be pushed (they contain `EV[...]` DO secrets).

| File | Purpose |
|------|---------|
| `chat-rag-spec.yaml` | ChatRAG DO spec export |
| `internal-write-api-spec.yaml` | Write API DO spec export |
| `admin-fe-spec.yaml` | Admin frontend DO spec export |

For staging smokes, set `VECINITA_STAGING_INTERNAL_API_KEY` in `prod.env` (not committed).

## Rollback

| Field | Value |
|-------|-------|
| Last known good (EV-001) | `4a1598f` |
| EV-002 rollback order | Admin FE → chat-rag → write-api; Option A leave EV-002 tables |
| See | `docs/deploy-checklist.md` §Rollback |

## Previous deploy

EV-001 report (2026-05-25, `4a1598f`): browse/tags/admin chunk editor — see git history `docs/sessions/S000-internal-docs-archive/deploy-report.md` @ `4a1598f`.

## Changelog

See `CHANGELOG.md` — version 0.3.0 (EV-002).

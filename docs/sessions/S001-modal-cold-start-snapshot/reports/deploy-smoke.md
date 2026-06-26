# Deploy & Smoke Report — S001 Modal cold-start / GPU snapshot

> **Date:** 2026-06-26  
> **Session:** S001-modal-cold-start-snapshot  
> **Stage:** 13-deploy-smoke  
> **Status:** **deployed**  
> **Branch:** `feat/S001-modal-cold-start-snapshot` @ `4f3f741`

## Pre-Deploy (Phase 1.5)

| Check | Status | Evidence |
|-------|--------|----------|
| `verify_build.sh` | **PASS** | Modal import smoke OK |
| H0c CORS (`test_cors_policy.py`) | **PASS** | 6 passed, 4 skipped (no local DB) |
| Alembic head | **N/A** | No migration changes in S001 |
| 12-verify-deploy sign-off | **PASS** | User approved 2026-06-25 |

## Deployment (S001 order)

| Step | Command / action | Result |
|------|------------------|--------|
| vecinita-llm | `modal deploy infra/modal/llm_app.py` | **SUCCESS** — GPU snapshot enabled |
| vecinita-embedding | `modal deploy infra/modal/embedding_app.py` | **SUCCESS** — CPU snapshot |
| vecinita-data-management | Skipped | Not required for S001 |
| chat-rag-backend | DO deploy from `feat/S001-modal-cold-start-snapshot` @ `4f3f741` | **SUCCESS** — ACTIVE |
| chat-rag-frontend | DO deploy from `feat/S001-modal-cold-start-snapshot` | **SUCCESS** — ACTIVE |
| internal-write-api | Skipped | Not required for S001 |
| admin-frontend | Skipped | Not required for S001 |

**Note:** DO apps temporarily pinned to `feat/S001-modal-cold-start-snapshot` (was `main`). Merge to `main` and reset branch pins before production cut.

## Smoke Tests

| Test | Status | Notes |
|------|--------|-------|
| H1 API connectivity | **PASS** | ChatRAG + write `/health` 200 |
| H2 DB + Alembic head | **PASS** | Pool OK; head matches |
| H3 RAG ask | **PASS** | ~230s cold (no pre-warm; informative) |
| H3b Browse | **PASS** | documents + tags |
| T3 EV-002 admin API | **PASS** | 4/4 |
| H0c CORS (local) | **PASS** | 20 tests |
| H4 CORS (live) | **PASS** | incl. `/api/v1/warm` preflight |
| H4 Modal data-mgmt | **WAIVER** | `requires_proxy_auth` (EV-001 user-approved) |
| H5 Frontend bundles | **PASS** | chat + admin hosts in JS bundles |
| `POST /api/v1/warm` | **PASS** | `{"status":"warming"}` 200 |

## S001 cold-start validation

| Scenario | Latency | Target | Result |
|----------|---------|--------|--------|
| Warm ask (hot containers) | **7.4s** | — | PASS |
| Cold containers → pre-warm → ask | **14.3s** | < 60s (DO gateway) | **PASS** |
| Cold ask without pre-warm (H3) | **230s** | — | Expected; pre-warm path is the fix |

Pre-warm flow: stop Modal LLM/embed containers → `POST /api/v1/warm` → wait ~50s → `POST /api/v1/ask`.

## Health Check

- All 4 DO apps: ACTIVE
- Modal apps: deployed (llm, embedding, data-mgmt)
- `POST /api/v1/warm` live on staging backend
- No smoke-path errors

## URLs (unchanged)

| Service | URL |
|---------|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| ChatRAG frontend | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |
| Modal LLM | https://vecinita--vecinita-llm-fastapi-app.modal.run |
| Modal embedding | https://vecinita--vecinita-embedding-embedding-api.modal.run |

## Rollback

Per [deploy-checklist.md](deploy-checklist.md) §Rollback:

1. Revert DO branch to `main` and redeploy chat-rag-backend + frontend (optional if warm-only issue)
2. `modal deploy` pre-S001 `llm_app.py` to remove GPU snapshot
3. Emergency: `modal app stop vecinita-llm`

| Field | Value |
|-------|-------|
| Last known good (pre-S001 staging) | `7f38c58` on `main` |
| S001 deployed commit | `4f3f741` |

## Advisories

- **07-build T12** (web-fn hop collapse) still pending — not blocking this deploy.
- **DO branch drift:** staging chat apps on feature branch until merge to `main`.
- **H3 cold without pre-warm** still exceeds 60s — acceptable; browser path uses pre-warm on mount.
- **ADR-022** body still says "Proposed" in places — reconcile on merge.

## Next step

**15-service-health** — record DO-path latency baseline and monitor Modal billing post-snapshot.

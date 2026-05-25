# Deploy Report

> Date: 2026-05-25
> Status: **deployed**
> Version: 0.2.0 (EV-001)
> Commit: `4a1598f`

## Pre-Deploy

- Checklist: all items passed (`docs/deploy-checklist.md`)
- D7 LLM weights: verified (health 200, `/generate` tested)
- T0 e2e: 16/16 passed
- H0c CORS: 9/9 passed (TC-046 browse GET, TC-049 admin PATCH)
- verify_build: PASS (deps, ADR-007, Modal app imports)

## Deployment

| Step | Command | Duration | Result |
|------|---------|----------|--------|
| Database | `alembic upgrade head` (20260519_0001 → 20260524_0002) | 1s | SUCCESS |
| Modal (3 apps) | `bash scripts/deploy/modal.sh` | 11s | SUCCESS |
| DO chat-rag-backend | `do_apps.py deploy` | ~150s | SUCCESS |
| DO internal-write-api | `do_apps.py deploy` | ~150s | SUCCESS |
| DO chat-rag-frontend | `do_apps.py deploy` | ~120s | SUCCESS |
| DO admin-frontend | `do_apps.py deploy` | ~120s | SUCCESS |

**Deploy-time fixes (committed during deploy):**
1. `98cc2ac` — Tag inference chat template + graceful fallback
2. `4a1598f` — Fallback to unfiltered retrieval when tag filter yields empty

Both fixes were pushed to main and chat-rag-backend redeployed before smoke completion.

## Smoke Tests

| Test | Status | Response Time | Notes |
|------|--------|---------------|-------|
| H1 API connectivity (ChatRAG) | **PASS** | <1s | `{"status":"ok","dependencies":{"postgres":"ok","modal_embed":"ok","modal_llm":"ok"}}` |
| H1 API connectivity (Write API) | **PASS** | <1s | `{"status":"ok"}` |
| H2 DB pool + Alembic head | **PASS** | — | Pool connects; revision == head (20260524_0002) |
| H3 RAG ask | **PASS** | 7148ms | Answer returned in `en`; includes tag inference + LLM (cold) |
| H3b Browse documents | **PASS** | <1s | 5 items (total 11); pagination working |
| H3b Browse tags | **PASS** | <1s | 3 tag facets (housing, benefits, legal) |
| H4 ChatRAG CORS | **PASS** | — | OPTIONS preflight from chat frontend origin |
| H4 Write API CORS | **PASS** | — | OPTIONS preflight including PATCH method |
| H4 Modal data-mgmt | **WAIVER** | — | `requires_proxy_auth` blocks OPTIONS (existing user-approved waiver) |
| H5 Chat frontend bundle | **PASS** | — | Bundle contains ChatRAG backend host (browse + ask) |
| H5 Admin frontend bundle | **PASS** | — | Bundle contains write API + Modal hosts |

## Health Check

- Error rate: 0% (all endpoints responding)
- Avg response time: H3 ask 7.1s (cold LLM; warm ~3s), browse <1s
- Container restarts: 0
- All 4 DO apps: ACTIVE
- All 3 Modal apps: deployed (embedding, data-management, llm)

## Monitoring Baseline

- ChatRAG `/health`: postgres ok, modal_embed ok, modal_llm ok
- LLM cold-start: ~5-10s first request after scaledown (300s window)
- Browse latency: <1s (DB query, no external calls)
- Tag inference adds ~3s to ask latency (LLM call for tag extraction)

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

## Rollback

| Field | Value |
|-------|-------|
| Command (DO) | Redeploy previous app spec via dashboard or `do_apps.py` |
| Command (Modal) | `modal app stop vecinita-data-management` |
| DB rollback | Option A: leave tag tables in place (no data loss) |
| Last known good (pre-EV-001) | `c4bc847` |

## Changelog

See `CHANGELOG.md` — version 0.2.0 (EV-001).

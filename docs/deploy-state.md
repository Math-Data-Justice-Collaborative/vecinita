# Deploy State

> Last updated: 2026-05-27
> Status: **deployed** (EV-002)

## Deployment Log

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | T0 e2e (not live) | pass | 2026-05-27 session |
| 2 | H0c CORS | pass | incl. TC-060 EV-002 |
| 3 | DB: alembic head `20260526_0003` | pass | audit_log, document_versions, document_serving_stats |
| 4 | DO internal-write-api | pass | @ `0a2f813` evolve branch |
| 5 | DO chat-rag-backend | pass | stats POST integration |
| 6 | DO admin-frontend | pass | dashboard, health, audit, bulk UI |
| 7 | Modal redeploy | skip | Not required EV-002 |
| 8 | H1/H2/H3/H3b smoke | pass | staging_smoke.sh |
| 9 | T3 EV-002 admin API | pass | 4/4 test_staging_ev002_admin.py |
| 10 | H4/H5 connectivity | pass | verify_connectivity.sh |
| 11 | Deploy report | pass | docs/deploy-report.md |

## Current Deployment

| Field | Value |
|-------|-------|
| App name | vecinita (DO project) |
| Deploy mode | EV-002 delta (hybrid DO + Modal) |
| Commit deployed | `0a2f813` |
| Branch | `evolve/EV-002-admin-overhaul` |
| Local HEAD | `98bb7f8` (2 commits ahead — merge advisory) |
| Alembic head | `20260526_0003` |

## Live URLs

| Service | URL |
|---------|-----|
| ChatRAG backend | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| ChatRAG frontend | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |
| Modal embedding | https://vecinita--vecinita-embedding-embedding-api.modal.run |
| Modal LLM | https://vecinita--vecinita-llm-fastapi-app.modal.run |
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run |

## Staging smoke env

```bash
export VECINITA_STAGING_CHAT_URL=https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app
export VECINITA_STAGING_WRITE_URL=https://vecinita-internal-write-api-icze4.ondigitalocean.app
export VECINITA_STAGING_CHAT_FRONTEND_URL=https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app
export VECINITA_STAGING_ADMIN_FRONTEND_URL=https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
export VECINITA_STAGING_ADMIN_API_URL=https://vecinita--vecinita-data-management-fastapi-app.modal.run
# VECINITA_STAGING_INTERNAL_API_KEY: from chat-rag-spec.yaml (VECINITA_INTERNAL_API_KEY) — do not commit
bash scripts/deploy/staging_smoke.sh
bash scripts/deploy/verify_connectivity.sh
```

## Rollback

See [deploy-checklist.md](deploy-checklist.md) §Rollback — EV-001 LKG `4a1598f`; EV-002 reverse TP-029 order.

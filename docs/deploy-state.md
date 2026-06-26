# Deploy State

> Last updated: 2026-06-26
> Status: **deployed** (S001 + EV-002 staging)

## Deployment Log

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | T0 e2e (not live) | pass | 2026-06-25 session |
| 2 | H0c CORS | pass | incl. TC-060 EV-002 |
| 3 | DB: alembic head `20260526_0003` | pass | audit_log, document_versions, document_serving_stats |
| 4 | DO internal-write-api | pass | EV-002 @ main |
| 5 | DO chat-rag-backend | pass | **S001** @ `4f3f741` feat branch |
| 6 | DO chat-rag-frontend | pass | **S001** @ feat branch (pre-warm) |
| 7 | DO admin-frontend | pass | EV-002 @ main |
| 8 | Modal llm + embedding | pass | **S001** GPU/CPU snapshots 2026-06-26 |
| 9 | H1/H2/H3/H3b smoke | pass | staging_smoke.sh |
| 10 | T3 EV-002 admin API | pass | 4/4 test_staging_ev002_admin.py |
| 11 | H4/H5 connectivity | pass | verify_connectivity.sh |
| 12 | S001 cold+prewarm ask | pass | 14.3s (< 60s target) |
| 13 | Deploy report | pass | docs/sessions/S001-modal-cold-start-snapshot/reports/deploy-smoke.md |

## Current Deployment

| Field | Value |
|-------|-------|
| App name | vecinita (DO project) |
| Deploy mode | S001 delta (Modal snapshot + DO warm path) |
| Commit deployed | `4f3f741` (chat DO apps); Modal from local branch |
| Branch | `feat/S001-modal-cold-start-snapshot` (DO chat apps); write/admin on `main` |
| Alembic head | `20260526_0003` |
| Drift | DO chat apps on feature branch until merge to `main` |

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

See [deploy-checklist.md](deploy-checklist.md) §Rollback — EV-001 LKG `4a1598f`; S001 reverse order in session deploy-checklist.

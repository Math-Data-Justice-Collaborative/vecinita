# Deploy State

> Last updated: 2026-05-25
> Status: **deployed**

## Deployment Log

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | T0 e2e (not live) | pass | 16/16 |
| 2 | verify_build / verify_secrets | pass | ADR-007, Modal imports OK |
| 3 | D7 LLM health | pass | `/health` 200 + `/generate` verified |
| 4 | DB: alembic upgrade head | pass | 20260519_0001 → 20260524_0002 (tag tables) |
| 5 | Modal deploy (3 apps) | pass | embedding, data-management, llm |
| 6 | DO chat-rag-backend | pass | ACTIVE (browse routes + CORS) |
| 7 | DO internal-write-api | pass | ACTIVE (tag PATCH + retag trigger) |
| 8 | DO chat-rag-frontend | pass | ACTIVE (browse UI + tag chips) |
| 9 | DO admin-frontend | pass | ACTIVE (chunk viewer + tag editor) |
| 10 | Deploy-time fix: tag prompt | pass | `98cc2ac` pushed + redeployed |
| 11 | Deploy-time fix: retrieval fallback | pass | `4a1598f` pushed + redeployed |
| 12 | H1/H2/H3/H3b smoke | pass | All tiers green |
| 13 | H4/H5 connectivity | pass (waiver) | Modal H4 waiver (proxy auth); DO H4/H5 pass |
| 14 | Changelog + deploy report | pass | CHANGELOG.md, docs/deploy-report.md |

## DigitalOcean project

All four App Platform apps in project **`vecinita`** (`59561bbc-6383-4b66-8377-187960f14ce2`).

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
# DATABASE_URL from prod.env for H2
uv run pytest tests/smoke -m live -v
```

## Rollback

See [deploy-checklist.md](deploy-checklist.md) §Rollback — last known good code `c4bc847`; Option A approved (leave tag tables).

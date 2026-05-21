# Deploy State

> Last updated: 2026-05-20
> Status: **deployed**

## Deployment Log

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | T0 e2e (not live) | pass | 11/11 |
| 2 | verify_build / verify_secrets | pass | |
| 3 | DO Postgres + Alembic + seed | pass | `vecinita-staging` |
| 4 | DO apps (pydo) + vecinita project | pass | 4 apps |
| 5 | DO internal-write-api | pass | ACTIVE |
| 6 | DO chat-rag-backend | pass | ACTIVE after restore `uv sync --group dev` |
| 7 | DO frontends rebuild | pass | VITE URLs synced |
| 8 | Modal deploy + secrets | pass | |
| 9 | Smoke H1 / H2 / H3 | pass | 2026-05-20 |
| 10 | T3 live pytest (`tests/smoke -m live`) | pass | 11/11; Modal LLM JSON body + D7 staged |
| 11 | Re-validate (13-deploy-smoke) | pass | 2026-05-20: T0 11/11, H1–H3, T3 11/11; commit `c4bc847` |
| 12 | Re-deploy Modal + DO (force_build) | pass | 2026-05-20: `c4bc847`; H3 cold-start 504 until LLM warm (~19s) |
| 13 | H4/H5 connectivity gates | pass (waiver) | 2026-05-21: H4 DO CORS pass; H4 Modal waiver (proxy auth blocks preflight); H5 pass |
| 14 | CORS redeploy (DO backends) | pass | 2026-05-21: `VECINITA_CORS_ORIGINS` pushed via live spec update |

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
# DATABASE_URL from prod.env for H2
uv run pytest tests/smoke -m live -v   # T3 (11 tests)
```

## Rollback

See [deploy-checklist.md](deploy-checklist.md) §Rollback — last known good code `324bb50`; redeploy prior DO deployment via dashboard or `do_apps.py deploy`.

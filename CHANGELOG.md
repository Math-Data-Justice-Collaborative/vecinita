# Changelog

## [0.1.0-staging] — 2026-05-20

### Deploy & infrastructure (13-deploy-smoke)

- **[13]** DigitalOcean App Platform: 4 apps in `vecinita` project (chat-rag-backend, internal-write-api, 2× static frontends)
- **[13]** Managed Postgres `vecinita-staging` + Alembic migrations + seed corpus
- **[13]** Modal: `vecinita-embedding`, `vecinita-llm`, `vecinita-data-management` on `vecinita` workspace
- **[13]** `scripts/deploy/do_apps.py` — pydo helper (`create-all`, `sync-secrets`, `deploy`, `urls`)
- **[13]** `.python-version` (3.11) for DO Python buildpack
- **[13]** DO runtime: `python3 -m uvicorn` (buildpack profile; not bare `uv` in container)

### Fixes during deploy

- `vecinita-admin-frontend` app name shortened for DO 32-char limit
- ChatRAG build requires `uv sync --group dev` for runtime workspace deps

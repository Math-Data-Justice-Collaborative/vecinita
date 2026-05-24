# Staging secrets matrix

> **Project**: Vecinita staging  
> **Source**: `docs/deployment-integration.md` §Secrets, ADR-007, ADR-010  
> **Last updated**: 2026-05-24 (EV-001 T19.1 — browse API shares chat VITE URL)

Store values in **DigitalOcean App Platform** secrets or **Modal** secrets — never commit to git.

## DigitalOcean — ChatRAG Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Managed Postgres connection string (read + pgvector) |
| `VECINITA_MODAL_EMBED_URL` | Yes | Modal `vecinita-embedding` base URL (**`vecinita--`** workspace prefix) |
| `VECINITA_MODAL_LLM_URL` | Yes | Modal `vecinita-llm` base URL |
| `VECINITA_MODAL_TOKEN_ID` | If Modal auth | DO→Modal credential |
| `VECINITA_MODAL_TOKEN_SECRET` | If Modal auth | DO→Modal credential |
| `VECINITA_TOP_K` | No | Default `5` |
| `VECINITA_ENV` | No | Set `staging` |
| `VECINITA_CORS_ORIGINS` | Yes (browser UI) | Comma-separated frontend origins, e.g. `https://vecinita-chat-rag-frontend-….ondigitalocean.app` |

## DigitalOcean — Internal write API

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Same Postgres as ChatRAG (write path) |
| `VECINITA_INTERNAL_API_KEY` | Yes | Bearer token for Modal workers |
| `VECINITA_ENV` | No | `staging` |
| `VECINITA_CORS_ORIGINS` | Yes (browser UI) | Must include admin frontend origin |

## DigitalOcean — Static frontends (build time)

| Variable | App | Description |
|----------|-----|-------------|
| `VITE_VECINITA_CHAT_API_URL` | chat-rag-frontend | Public ChatRAG backend URL (**ask + browse** `/api/v1/documents`, `/tags` — EV-001) |
| `VITE_VECINITA_ADMIN_API_URL` | data-management-frontend | Modal data-mgmt ASGI URL |
| `VITE_VECINITA_MODAL_PROXY_KEY` | data-management-frontend | Edge proxy key for `/jobs` |
| `VITE_VECINITA_CORPUS_API_URL` | data-management-frontend | Internal write API URL |
| `VITE_VECINITA_CORPUS_API_KEY` | data-management-frontend | Same as `VECINITA_INTERNAL_API_KEY` |

## Modal — Data management + workers

| Variable | Required | Description |
|----------|----------|-------------|
| `VECINITA_DO_WRITE_API_URL` | Yes | DO internal write API base URL |
| `VECINITA_INTERNAL_API_KEY` | Yes | Must match DO write API secret |
| `VECINITA_MODAL_PROXY_KEY` | Yes | ASGI `requires_proxy_auth` |
| `VECINITA_CORS_ORIGINS` | Yes (browser UI) | Admin frontend origin; redeploy after change |
| `VECINITA_CHUNK_SIZE_TOKENS` | No | Default `256` |

**Forbidden on Modal:** `DATABASE_URL` (ADR-007).

## Modal — Embedding / LLM

No Vecinita Postgres secrets. HF model cache uses Modal volumes `embedding-models`, `llm-models`.

## Staging smoke env (operator shell)

| Variable | Used by |
|----------|---------|
| `VECINITA_STAGING_CHAT_URL` | H1/H3 — `scripts/deploy/staging_smoke.sh`, `tests/smoke/test_staging_health.py` (skip if unset) |
| `VECINITA_STAGING_WRITE_URL` | Optional H1 check on write API |
| `VECINITA_STAGING_DATABASE_URL` | H2 — staging DB URL; falls back to `DATABASE_URL` |
| `VECINITA_STAGING_CHAT_FRONTEND_URL` | H4–H5 — chat UI origin |
| `VECINITA_STAGING_ADMIN_FRONTEND_URL` | H4–H5 — admin UI origin |
| `VECINITA_STAGING_ADMIN_API_URL` | H4 — Modal data-mgmt base URL |

See [staging-runbook.md](staging-runbook.md) for deploy order and Phase 4 gate checklist.
See [.cursor/skills/connectivity-gates.md](../.cursor/skills/connectivity-gates.md) for full gate matrix.

## Rotation

1. Generate new key in DO dashboard.  
2. Update matching Modal secret.  
3. Redeploy affected apps (`doctl apps create-deployment`, `modal deploy`).  
4. Re-run `bash scripts/deploy/staging_smoke.sh`.

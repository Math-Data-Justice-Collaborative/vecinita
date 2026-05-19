# Staging secrets matrix

> **Project**: Vecinita staging  
> **Source**: `docs/deployment-integration.md` §Secrets, ADR-007, ADR-010  
> **Last updated**: 2026-05-19 (T14.2)

Store values in **DigitalOcean App Platform** secrets or **Modal** secrets — never commit to git.

## DigitalOcean — ChatRAG Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Managed Postgres connection string (read + pgvector) |
| `VECINITA_MODAL_EMBED_URL` | Yes | Modal `vecinita-embedding` base URL |
| `VECINITA_MODAL_LLM_URL` | Yes | Modal `vecinita-llm` base URL |
| `VECINITA_MODAL_TOKEN_ID` | If Modal auth | DO→Modal credential |
| `VECINITA_MODAL_TOKEN_SECRET` | If Modal auth | DO→Modal credential |
| `VECINITA_TOP_K` | No | Default `5` |
| `VECINITA_ENV` | No | Set `staging` |

## DigitalOcean — Internal write API

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Same Postgres as ChatRAG (write path) |
| `VECINITA_INTERNAL_API_KEY` | Yes | Bearer token for Modal workers |
| `VECINITA_ENV` | No | `staging` |

## DigitalOcean — Static frontends (build time)

| Variable | App | Description |
|----------|-----|-------------|
| `VITE_VECINITA_CHAT_API_URL` | chat-rag-frontend | Public ChatRAG backend URL |
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
| `VECINITA_CHUNK_SIZE_TOKENS` | No | Default `256` |

**Forbidden on Modal:** `DATABASE_URL` (ADR-007).

## Modal — Embedding / LLM

No Vecinita Postgres secrets. HF model cache uses Modal volumes `embedding-models`, `llm-models`.

## Staging smoke env (operator shell)

| Variable | Used by |
|----------|---------|
| `VECINITA_STAGING_CHAT_URL` | `scripts/deploy/staging_smoke.sh`, `tests/smoke/test_staging_health.py` |
| `VECINITA_STAGING_WRITE_URL` | Optional H1 check on write API |

## Rotation

1. Generate new key in DO dashboard.  
2. Update matching Modal secret.  
3. Redeploy affected apps (`doctl apps create-deployment`, `modal deploy`).  
4. Re-run `bash scripts/deploy/staging_smoke.sh`.

# Staging secrets matrix

> **Project**: Vecinita staging  
> **Source**: `docs/deployment-integration.md` §Secrets, ADR-007, ADR-010  
> **Last updated**: 2026-05-27 (EV-002 — reconciled health env names with runtime code)

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
| `VECINITA_BROWSE_PAGE_SIZE` | No | Default `20` — EV-001 browse pagination |
| `VECINITA_STATS_ENABLED` | No | Default `true` — EV-002 disable fire-and-forget stats POST (F28) |
| `VECINITA_INTERNAL_WRITE_URL` | Yes (EV-002) | DO internal write API base — stats POST after ask (F28) |
| `VECINITA_INTERNAL_API_KEY` | Yes (EV-002) | Bearer for stats POST; must match write API secret |
| `VECINITA_ENV` | No | Set `staging` |
| `VECINITA_CORS_ORIGINS` | Yes (browser UI) | Comma-separated frontend origins, e.g. `https://vecinita-chat-rag-frontend-….ondigitalocean.app` |

## DigitalOcean — Internal write API

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Same Postgres as ChatRAG (write path) |
| `VECINITA_INTERNAL_API_KEY` | Yes | Bearer token for Modal workers |
| `VECINITA_MODAL_DATA_MGMT_URL` | Yes (EV-001) | Modal data-mgmt base URL — retag job dispatch |
| `VECINITA_MODAL_PROXY_KEY` | Yes (EV-001) | Proxy auth key for Modal data-mgmt `/jobs` retag endpoint |
| `VECINITA_MAX_TAGS_PER_DOCUMENT` | No | Default `10` — EV-001 tag cap enforcement |
| `VECINITA_MAX_TAGS_PER_CHUNK` | No | Default `5` — EV-001 tag cap enforcement |
| `VECINITA_HEALTH_TIMEOUT_MS` | No | Default `5000` — EV-002 health aggregator timeout per service (F26) |
| `VECINITA_AUDIT_RETENTION_DAYS` | No | Default `365` — EV-002 audit retention for `POST /internal/v1/audit/cleanup` (F29); `0` = skip |
| `VECINITA_CHAT_RAG_URL` | Yes (EV-002) | Chat-rag-backend URL for `GET /internal/v1/health/all` polling |
| `VECINITA_MODAL_EMBED_URL` | Yes (EV-002) | Modal embedding URL for health aggregator |
| `VECINITA_MODAL_LLM_URL` | Yes (EV-002) | Modal LLM URL for health aggregator |
| `VECINITA_MODAL_DATA_MGMT_URL` | Yes (EV-001/002) | Modal data-mgmt URL — retag dispatch + health poll |
| `VECINITA_CHAT_FRONTEND_URL` | Yes (EV-002) | Chat static site URL for health aggregator HTTP check |
| `VECINITA_ADMIN_FRONTEND_URL` | Yes (EV-002) | Admin static site URL for health aggregator HTTP check |
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
| `VECINITA_INTERNAL_WRITE_URL` | Yes | DO internal write API base URL (code reads this name, not `VECINITA_DO_WRITE_API_URL`) |
| `VECINITA_INTERNAL_API_KEY` | Yes | Must match DO write API secret |
| `VECINITA_MODAL_PROXY_KEY` | Yes | ASGI `requires_proxy_auth` |
| `VECINITA_MODAL_EMBED_URL` | Yes | Modal `vecinita-embedding` base URL — used by ingest workers |
| `VECINITA_MODAL_LLM_URL` | Yes (EV-001) | Modal `vecinita-llm` base URL — LLM tagging at ingest |
| `VECINITA_CORS_ORIGINS` | Yes (browser UI) | Admin frontend origin; redeploy after change |
| `VECINITA_LLM_TAG_MAX_TOKENS` | No | Default `128` — EV-001 LLM tag generation token limit |
| `VECINITA_TAG_SEED_PATH` | No | Default `data/fixtures/tags/seed_tags.json` — EV-001 tag vocabulary path |

**Forbidden on Modal:** `DATABASE_URL` (ADR-007).

**Name correction (12-verify-deploy):** Code reads `VECINITA_INTERNAL_WRITE_URL`, not the previously documented `VECINITA_DO_WRITE_API_URL`. The Modal secret `vecinita-data-management` was already created with the correct name during 13-deploy-smoke. The `config-spec.md` reference to `VECINITA_DO_WRITE_API_URL` is stale — the code and deploy scripts use `VECINITA_INTERNAL_WRITE_URL`.

## Modal — Embedding / LLM

No Vecinita Postgres secrets. HF model cache uses Modal volumes `embedding-models`, `llm-models`.

## Staging smoke env (operator shell)

| Variable | Used by |
|----------|---------|
| `VECINITA_STAGING_CHAT_URL` | H1/H3 — `scripts/deploy/staging_smoke.sh`, `tests/smoke/test_staging_health.py` (skip if unset) |
| `VECINITA_STAGING_WRITE_URL` | Optional H1 check on write API; EV-002 bulk/stats/audit endpoints |
| `VECINITA_STAGING_DATABASE_URL` | H2 — staging DB URL; falls back to `DATABASE_URL` |
| `VECINITA_STAGING_CHAT_FRONTEND_URL` | H4–H5 — chat UI origin |
| `VECINITA_STAGING_ADMIN_FRONTEND_URL` | H4–H5 — admin UI origin |
| `VECINITA_STAGING_ADMIN_API_URL` | H4 — Modal data-mgmt base URL |
| `VECINITA_STAGING_INTERNAL_API_KEY` | T3 / H3c — Bearer for write API admin smokes (EV-002) |

See [staging-runbook.md](staging-runbook.md) for deploy order and Phase 4 gate checklist.
See [.cursor/skills/connectivity-gates.md](../.cursor/skills/connectivity-gates.md) for full gate matrix.

## Rotation

1. Generate new key in DO dashboard.  
2. Update matching Modal secret.  
3. Redeploy affected apps (`doctl apps create-deployment`, `modal deploy`).  
4. Re-run `bash scripts/deploy/staging_smoke.sh`.

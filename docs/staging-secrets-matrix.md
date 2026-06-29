# Staging secrets matrix

> **Project**: Vecinita staging  
> **Source**: `docs/deployment-integration.md` §Secrets, ADR-007, ADR-010  
> **Last updated**: 2026-06-13 (EV-004 — no new secrets; existing VITE/CORS rows sufficient per AC-F6)

Store values in **DigitalOcean App Platform** secrets or **Modal** secrets — never commit to git.

## DigitalOcean — ChatRAG Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Managed Postgres connection string (read + pgvector) |
| `VECINITA_MODAL_EMBED_URL` | Yes | Modal `vecinita-embedding` **base** URL (**`vecinita--`** prefix; no `/health` suffix) |
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
| `VECINITA_MODAL_EMBED_URL` | Yes (EV-002) | Modal embedding **base** URL (no `/health` suffix); health poll appends `/health` |
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

## EV-005 (F34) — Supabase admin auth (#75)

Identity for **admin surfaces only** (DM UI, DM Modal API, internal-write API). ChatRAG stays anonymous.

### Supabase project (`cfuvghdsuwactfeamtym`)

| Variable | Where | Required | Description |
|----------|-------|----------|-------------|
| `SUPABASE_URL` | DO write API, Modal DM ASGI, operator shell | Yes | `https://cfuvghdsuwactfeamtym.supabase.co` — JWKS at `/auth/v1/.well-known/jwks.json` (ES256, ADR-028) |
| `SUPABASE_SECRET_KEY` | Operator shell / seed script only | Yes | Admin API (`inviteUserByEmail`, `seed_first_admin.py`) — **never** in browser builds |
| `SUPABASE_PUBLISHABLE_KEY` | DM frontend build (`VITE_*`) | Yes | Browser-safe publishable key |
| `SUPABASE_ADMIN_EMAIL` | `prod.env` / seed script | Bootstrap | First admin email (`admin@vecinita.admin`) |
| `SUPABASE_ADMIN_PASSWORD` | `prod.env` / seed script | Bootstrap | First admin password — set before `scripts/seed_first_admin.py` |
| `VECINITA_AUTH_REQUIRED` | Admin backends | No | Default `true`; `false` only for local dev without Supabase |
| `SUPABASE_JWT_AUD` | Admin backends | No | Default `authenticated` |

### DigitalOcean — Internal write API (add)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes (F34) | JWKS verification for operator JWTs |

### DigitalOcean — Static admin frontend (add build-time)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_SUPABASE_URL` | Yes (F34) | Same as `SUPABASE_URL` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Yes (F34) | Same as `SUPABASE_PUBLISHABLE_KEY` |

### Modal — Data management ASGI (add)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes (F34) | JWT verification (with existing `X-Vecinita-Proxy-Key`) |

### Operator runbook (AC-A10)

- **Invite operator:** Supabase Dashboard → Authentication → Users → Invite (or `inviteUserByEmail` with custom SMTP).
- **Disable operator:** Dashboard → delete/ban user.
- **Role change:** set `app_metadata.role` to `admin` or `viewer` (never `user_metadata`).
- **First admin:** `uv run python scripts/seed_first_admin.py` (idempotent).
- **Env sync:** `supabase/README.md` — ephemeral preview branches; tear down after PR merge.
- **JWT key rotation:** automatic via JWKS refresh (no `SUPABASE_JWT_SECRET` with ES256).

### GitHub Actions (Supabase CI workflow)

| Secret | Required | Description |
|--------|----------|-------------|
| `SUPABASE_ACCESS_TOKEN` | For cloud sync jobs | Personal access token from [Supabase dashboard account tokens](https://supabase.com/dashboard/account/tokens); enables `preview-branch` + `sync-production` in `.github/workflows/supabase.yml` |
| `SUPABASE_DB_PASSWORD` | Optional | Database password for `supabase link` when applying SQL migrations via `db push` |

Offline **validate** job runs without these secrets. Cloud jobs skip when the token is absent.

**Example env files (placeholders):** `infra/do/.env.example`, `infra/modal/.env.example`  
**Push to DO:** `scripts/deploy/do_apps.py sync-secrets` or `sync-all-secrets` (see `infra/do/README.md`).  
**Push everywhere (Supabase check + Modal + DO):** `bash scripts/deploy/sync_env.sh --apply`  
**Push to Modal only:** `bash scripts/deploy/sync_modal_secret.sh --apply`

## EV-004 (F31) — no new secrets

EV-004 is client-only i18n/UI. **No new environment variables** or CORS policy changes (AC-F6). Existing `VITE_*` rows for both DO static frontends and `VECINITA_CORS_ORIGINS` on backends remain sufficient. Re-run H4/H5 after redeploying both frontends (AC-F7).

# Staging secrets matrix

> **Project**: Vecinita staging  
> **Source**: `docs/deployment-integration.md` §Secrets, ADR-007, ADR-010  
> **Last updated**: 2026-07-01 (S007/EV-008 F36 — VECINITA_EVAL_* on internal-write-api)

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
| `VECINITA_EVAL_FIXTURE_PATH` | No | Default `data/fixtures/eval/qa_pairs.json` — golden set (EV-008 F36) |
| `VECINITA_EVAL_RETRIEVAL_THRESHOLD` | No | Default `0.80` — aggregate retrieval gate |
| `VECINITA_EVAL_FAITHFULNESS_CI_MIN` | No | Default `0.60` |
| `VECINITA_EVAL_FAITHFULNESS_DISPLAY_MIN` | No | Default `0.70` — admin UI highlight |
| `VECINITA_EVAL_ANSWER_RELEVANCY_CI_MIN` | No | Default `0.60` |
| `VECINITA_EVAL_ANSWER_RELEVANCY_DISPLAY_MIN` | No | Default `0.70` |
| `VECINITA_EVAL_LATENCY_P95_DISPLAY_MS` | No | Default `30000` — informational only |
| `VECINITA_EVAL_JUDGE_QUERY_LANGUAGE` | No | Default `true` — judge rubric follows question locale |
| `VECINITA_EVAL_CORPUS_PROFILE` | No | Default `fixture`; set `staging` for live-corpus eval runs |
| `VECINITA_SUPER_ADMIN_EMAIL` | Yes (EV-009) | Canonical operator email with `role=super-admin` for promote (internal-write-api + auth seed) |
| `VECINITA_RAG_CONFIG_FALLBACK_*` | No | ChatRAG bootstrap when no `rag_production_config` row (see config-spec §Eval playground) |

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

| Secret | Required keys | Used by |
|--------|---------------|---------|
| **`vecinita-llm`** | `VECINITA_MODAL_PROXY_KEY` | `llm_app.py` ASGI — `/models/ollama*` proxy auth (ADR-037) |

Sync: `bash scripts/deploy/sync_llm_secret.sh --apply` (source `prod.env` first).
Proxy key must match DO internal-write-api `VECINITA_MODAL_PROXY_KEY`.

No Vecinita Postgres secrets on embed/LLM apps. HF model cache uses Modal volumes
`embedding-models`, `llm-models`. Playground staging: `modal run infra/modal/llm_app.py::stage_default_model`.

**Deprecated:** Modal secret `vecinita-ollama`, app `vecinita-ollama`, env `VECINITA_MODAL_OLLAMA_URL`.

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
| `SUPABASE_SECRET_KEY` | Yes (F35) | Admin API for `/admin/users*` (TP-S005-01) |

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
| `SUPABASE_PROJECT_ID` | Yes (cloud sync) | Canonical project ref (`cfuvghdsuwactfeamtym`) |
| `SUPABASE_PUBLISHABLE_KEY` | Deploy / future CI | New `sb_publishable_*` key (browser-safe; maps to `VITE_SUPABASE_PUBLISHABLE_KEY`) |
| `SUPABASE_SECRET_KEY` | Deploy / seed CI | New `sb_secret_*` key (admin API; replaces legacy `service_role`) |
| `SUPABASE_URL` | Deploy / CI | `https://cfuvghdsuwactfeamtym.supabase.co` |
| `SUPABASE_SMTP_PASS` | **EV-006 sync-production** | Resend API key (`re_...`); resolves `[auth.email.smtp] pass = env(SUPABASE_SMTP_PASS)` at `config push`. **Operator prerequisite: verified Resend domain** before setting. |

Offline **validate** job runs without these secrets. Cloud jobs skip when the token is absent.

**Push from `prod.env`:** `bash scripts/deploy/sync_github_secrets.sh --apply`
(dry run without `--apply`). Template: `infra/github/.env.example`. Supabase-CLI env
template: `supabase/.env.example`. Note: `prod.env` stores the DB password as
`SUPABASE_DATABASE_PASSWORD`; the sync script and CLI map it to `SUPABASE_DB_PASSWORD`.

**Example env files (placeholders):** `prod.env.example`, `infra/github/.env.example`, `infra/do/.env.example`, `infra/modal/.env.example`, `infra/resend/.env.example`, `supabase/.env.example`  
**Push to DO:** `scripts/deploy/do_apps.py sync-secrets` or `sync-all-secrets` (see `infra/do/README.md`).  
**Push everywhere (Supabase check + Modal + DO):** `bash scripts/deploy/sync_env.sh --apply`  
**Push to Modal only:** `bash scripts/deploy/sync_modal_secret.sh --apply`

## EV-006 (F35) — Admin user management + Resend SMTP (#75)

Builds on EV-005. Adds the live admin user-management surface and production email delivery.

### Backend hosting `/admin/users*` (ADR-030 / TP-S005-01)

| Variable | Where | Required | Description |
|----------|-------|----------|-------------|
| `SUPABASE_SECRET_KEY` | **Modal data-management ASGI only** | Yes (F35) | Supabase Admin API key for `/admin/users*`. **Server-side only** — never in internal-write-api or any `VITE_*` build. |
| `VECINITA_INTERNAL_WRITE_URL` | Modal data-management ASGI | Yes (F35) | Base URL for audit ingest (`POST /internal/v1/audit/event`) |
| `VECINITA_INTERNAL_API_KEY` | Modal data-management ASGI | Yes (F35) | Service key for audit ingest calls |
| `RESEND_API_KEY` | **Modal data-management ASGI only** | Yes (F35 test-send) | Resend API key (same value as `SUPABASE_SMTP_PASS`) for `POST /admin/email/test` (Resend REST). Server-side only. (TP-S005-22) |
| `RESEND_SENDER_EMAIL` | Modal data-management ASGI | Yes (F35 test-send) | Verified Resend sender (= `[auth.email.smtp] admin_email`) used as test-send `from`. (TP-S005-22) |
| `VITE_VECINITA_IDLE_TIMEOUT_MIN` | DM frontend build (`VITE_*`) | No (default 30) | Idle auto-logout minutes (TP-S005-17) |
| `VITE_VECINITA_IDLE_WARNING_SEC` | DM frontend build (`VITE_*`) | No (default 60) | Idle warning countdown seconds (TP-S005-17) |

### Supabase project — email delivery (used by Supabase/CLI, not Vecinita backends)

| Variable / item | Where | Required | Description |
|-----------------|-------|----------|-------------|
| `SUPABASE_SMTP_PASS` | GitHub Actions secret + Supabase project env | Yes (prod) | Resend API key; referenced by `[auth.email.smtp] pass = env(SUPABASE_SMTP_PASS)` |
| Verified Resend sending domain | Resend dashboard (operator) | Yes (prod) | SPF/DKIM-verified domain for `admin_email`/sender (RD-090) |
| Sender address + name | `config.toml` `[auth.email.smtp]` | Yes (prod) | e.g. `noreply@josephcmcg.com` (verified Resend domain), "Vecinita Admin" |

### Per-environment .env files (master = repo-root `prod.env`, gitignored)

| Environment | Template | Push command |
|-------------|----------|--------------|
| **GitHub Actions** | `infra/github/.env.example` | `bash scripts/deploy/sync_github_secrets.sh --apply` |
| **Supabase** (CLI / config push) | `supabase/.env.example` | `bash scripts/supabase/ci_sync.sh sync-production` (CI) |
| **Modal** (`vecinita-data-management`) | `infra/modal/.env.example` | `bash scripts/deploy/sync_modal_secret.sh --merge --apply` |
| **DigitalOcean** (4 apps) | `infra/do/.env.example` | `uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets` |
| **Resend** (SMTP + REST) | `infra/resend/.env.example` | `sync_github_secrets.sh` + `ci_sync.sh` + `sync_modal_secret.sh` |
| **Operator master** | `prod.env.example` → `prod.env` | `bash scripts/deploy/sync_env.sh --apply` |
| **Staging smokes** | `infra/staging/.env.example` | `bash scripts/deploy/verify_connectivity.sh` |

One-shot across every environment (dry run without `--apply`):

```bash
set -a && source prod.env && set +a
bash scripts/deploy/sync_env.sh --apply          # github + supabase + modal + do
bash scripts/deploy/sync_env.sh --github --apply # single environment
```

> **`--merge` for Modal:** `modal secret create --force` *replaces* the whole secret. The
> `--merge` flag exports the live secret first (via `scripts/deploy/export_modal_secret.py`),
> layers `prod.env` on top, then re-pushes the union — so adding `SUPABASE_SECRET_KEY` (F35)
> does not drop the existing keys.

### Operator prerequisites (F35)

1. Connect **Resend** (provision API key) and **verify the sending domain** (SPF/DKIM).
2. Set the Resend API key — in `prod.env` as `RESEND_API_KEY` (or `SUPABASE_SMTP_PASS`), then
   `bash scripts/deploy/sync_github_secrets.sh --apply` (maps `RESEND_API_KEY` → `SUPABASE_SMTP_PASS` on GitHub).
3. Set `SUPABASE_SECRET_KEY` on the **Modal data-management** backend
   (`bash scripts/deploy/sync_modal_secret.sh --merge --apply`) — host of `/admin/users*` (ADR-030).
4. Update `[auth.email.smtp] admin_email`/`sender_name` in `config.toml` to the verified sender.
5. `supabase config push` (via `supabase.yml` on merge to `main`) syncs SMTP + templates.
6. Set `RESEND_API_KEY` (same Resend key) + `RESEND_SENDER_EMAIL` on the Modal DM secret for the
   in-app **test-send** button (TP-S005-22).
7. **One-time:** apply the `admin_delete_user_sessions` RPC to the Supabase project (committed under
   `supabase/migrations/`) to enable admin **force sign-out** (TP-S005-19); until applied,
   `POST /admin/users/{id}/signout` returns `503` and **Disable** is the lockout fallback.

#### Deliverability DNS checklist (Resend domain — operator, TP-S005-23)

Add at the DNS provider for the verified sending domain (values from the Resend dashboard):

| Record | Type | Purpose |
|--------|------|---------|
| SPF | `TXT` | Authorize Resend to send for the domain (`v=spf1 include:...`) |
| DKIM | `CNAME`/`TXT` | Resend-provided signing keys |
| DMARC | `TXT` | `_dmarc` policy (start `p=none`, tighten to `quarantine`/`reject`) |

Verify end-to-end with the in-app **Send test email** (`POST /admin/email/test`).

### Operator runbook delta (supersedes parts of AC-A10)

- **Invite / disable / role change / revoke / reset:** now done in-app on the **`/users`** page
  (admin-only) — Supabase Dashboard no longer required for routine user management.
- **Emails:** delivered via **Resend**; templates are versioned in `supabase/templates/` and synced
  by `supabase config push` (never hand-edited in the Dashboard, which `config push` would overwrite).

## EV-007 (F35 ext) — Invite acceptance redirect chain (#109)

Builds on EV-006. Closes the production onboarding gap: email links must land on the deployed
admin frontend `/accept-invite`, not `localhost:3000`.

### Modal — Data management ASGI (add)

| Variable | Required | Description |
|----------|----------|-------------|
| `VECINITA_ADMIN_FRONTEND_URL` | Yes (F35 EV-007) | Deployed admin SPA origin **without trailing slash** — builds GoTrue `redirect_to` for invite/resend (`…/accept-invite`) and admin recovery (`…/reset-password`). **Server-side only** — not a `VITE_*` build var. Returns `503` on invite/resend/recovery routes when unset. (TP-S006-02, ADR-032 §2) |

Also used by internal-write-api health aggregator (EV-002) — same staging URL value.

### Supabase project — redirect configuration (not env vars on Vecinita backends)

| Setting | Where | Required | Description |
|---------|-------|----------|-------------|
| `[auth] site_url` | `supabase/config.toml` → `config push` | Yes (EV-007) | **Staging-first:** staging admin frontend URL (not `localhost:3000`) |
| `[auth] additional_redirect_urls` | `supabase/config.toml` → `config push` | Yes (EV-007) | Full paths: `{staging}/accept-invite`, `{staging}/reset-password`, prod admin URLs, local dev (`127.0.0.1:5173`) |

Verify Dashboard → Authentication → URL Configuration after every `config push` (TC-109).

### Operator prerequisites (EV-007)

1. Complete EV-006 prerequisites (Resend domain, `SUPABASE_SECRET_KEY` on Modal DM, SMTP sync).
2. Set `VECINITA_ADMIN_FRONTEND_URL` on Modal DM secret
   (`bash scripts/deploy/sync_modal_secret.sh --merge --apply`).
3. Merge to `main` triggers `supabase config push` (or run manually with `SUPABASE_ACCESS_TOKEN`).
4. **Redeploy order:** config push → Modal secret → `modal deploy` DM ASGI → redeploy admin FE → live invite smoke (13-deploy-smoke T3).

## EV-004 (F31) — no new secrets

EV-004 is client-only i18n/UI. **No new environment variables** or CORS policy changes (AC-F6). Existing `VITE_*` rows for both DO static frontends and `VECINITA_CORS_ORIGINS` on backends remain sufficient. Re-run H4/H5 after redeploying both frontends (AC-F7).

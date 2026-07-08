# Configuration Specification

> **Project**: Vecinita  
> **Last updated**: 2026-06-29 (S005/EV-006 F35 — admin user management + Resend SMTP/templates + remember-me)

## Precedence

CLI flags (where present) > Environment variables > Config file > Defaults

## Environment Variables

### Shared

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DATABASE_URL` | string | — | Yes (DO backends only) | Postgres connection; **not** on Modal workers |
| `VECINITA_ENV` | string | `development` | No | `development` \| `staging` \| `production` |
| `VECINITA_LOG_LEVEL` | string | `INFO` | No | Logging level |
| `VECINITA_LOG_RETENTION_DAYS` | int | `7` | No | Max retention; no raw prompts in persistent logs |

### ChatRAG Backend (DO)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_TOP_K` | int | `5` | No | Retrieval chunk count |
| `VECINITA_MIN_RETRIEVAL_SCORE` | float | `0.2` | No | Minimum pgvector similarity (`1 - distance`); chunks below are dropped |
| `VECINITA_CHAT_MAX_TOKENS` | int | `256` | No | Max tokens sent to Modal LLM per chat answer |
| `VECINITA_MODAL_EMBED_URL` | string | — | Yes (prod) | Modal FastEmbed base URL |
| `VECINITA_MODAL_LLM_URL` | string | — | Yes (prod) | Modal LLM base URL |
| `VECINITA_MODAL_TOKEN_ID` | string | — | Yes (DO→Modal) | Modal credential (DO secret) |
| `VECINITA_MODAL_TOKEN_SECRET` | string | — | Yes | Modal credential |
| `VECINITA_LLM_BACKEND` | string | `vllm` | No | `vllm` primary; `ollama` fallback only per ADR-009 |
| `VECINITA_REQUEST_TIMEOUT_S` | int | `120` | No | Upstream Modal timeout (cold-start margin; see R5) |
| `VECINITA_BROWSE_PAGE_SIZE` | int | `20` | No | Default page size for `GET /api/v1/documents` |
| `VECINITA_STATS_ENABLED` | string | `true` | No | Fire-and-forget stats POST after ask (F28); `false` disables |
| `VECINITA_INTERNAL_WRITE_URL` | string | — | Yes (EV-002) | Internal write API base for stats POST |
| `VECINITA_INTERNAL_API_KEY` | string | — | Yes (EV-002) | Bearer for stats POST; must match write API |
| `VECINITA_MAX_TAGS_PER_DOCUMENT` | int | `10` | No | Hard cap on document tags |
| `VECINITA_MAX_TAGS_PER_CHUNK` | int | `5` | No | Hard cap on chunk tags |
| `VECINITA_TAG_SEED_PATH` | string | `data/fixtures/tags/seed_tags.json` | No | Starter tag vocabulary for LLM + browse facets |

### DO internal write API

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_INTERNAL_API_KEY` | string | — | Yes | Shared secret Modal workers use |
| `DATABASE_URL` | string | — | Yes | Postgres |
| `VECINITA_AUDIT_RETENTION_DAYS` | int | `365` | No | Days for `POST /internal/v1/audit/cleanup` (F29); `0` skips delete |
| `VECINITA_HEALTH_TIMEOUT_MS` | int | `5000` | No | Timeout per service health poll in aggregator (F26); TP-019 |
| `VECINITA_CHAT_RAG_URL` | string | — | Yes (EV-002) | Chat-rag-backend URL for health aggregator |
| `VECINITA_MODAL_EMBED_URL` | string | — | Yes (EV-002) | Modal embedding **base** URL for health aggregator (no `/health` suffix) |
| `VECINITA_MODAL_LLM_URL` | string | — | Yes (EV-002) | Modal LLM URL for health aggregator |
| `VECINITA_MODAL_DATA_MGMT_URL` | string | — | Yes (EV-001/002) | Modal data-mgmt URL for health aggregator |
| `VECINITA_CHAT_FRONTEND_URL` | string | — | Yes (EV-002) | Chat static site URL for health aggregator |
| `VECINITA_ADMIN_FRONTEND_URL` | string | — | Yes (EV-002) | Admin static site URL for health aggregator |

### RAG evaluation (EV-008 F36)

Eval runner and thresholds for golden-set harness + admin tab. Judge LLM reuses Modal LLM URL
(same as ChatRAG). Fixture path is repo-relative in CI; staging runs use seeded corpus.

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_EVAL_FIXTURE_PATH` | string | `data/fixtures/eval/qa_pairs.json` | No | Golden set JSON path |
| `VECINITA_EVAL_RETRIEVAL_THRESHOLD` | float | `0.80` | No | Minimum aggregate retrieval relevance (`hit` + `any_of` rows) |
| `VECINITA_EVAL_FAITHFULNESS_CI_MIN` | float | `0.60` | No | CI gate — minimum aggregate faithfulness |
| `VECINITA_EVAL_FAITHFULNESS_DISPLAY_MIN` | float | `0.70` | No | Admin UI highlight threshold |
| `VECINITA_EVAL_ANSWER_RELEVANCY_CI_MIN` | float | `0.60` | No | CI gate — minimum aggregate answer relevancy |
| `VECINITA_EVAL_ANSWER_RELEVANCY_DISPLAY_MIN` | float | `0.70` | No | Admin UI highlight threshold |
| `VECINITA_EVAL_LATENCY_P95_DISPLAY_MS` | int | `30000` | No | Informational p95 reference (not a CI gate) |
| `VECINITA_EVAL_JUDGE_QUERY_LANGUAGE` | string | `true` | No | When `true`, LlamaIndex judge rubric follows question locale (RD-109) |
| `VECINITA_EVAL_CORPUS_PROFILE` | string | `fixture` | No | `fixture` \| `staging` — which corpus to run against (04-tech-plan) |

### Eval playground + production config (EV-009 F37)

Sandbox eval overrides are per-run / per-preset (API body), not env vars. Production values
after promote are stored in `rag_production_config` (DB); env vars below are bootstrap/fallback only.

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_SUPER_ADMIN_EMAIL` | string | — | Yes (staging/prod) | Canonical operator email seeded with `role=super-admin` for promote |
| `VECINITA_RAG_CONFIG_FALLBACK_TOP_K` | int | `5` | No | ChatRAG fallback when no active DB config |
| `VECINITA_RAG_CONFIG_FALLBACK_MIN_RETRIEVAL_SCORE` | float | `0.2` | No | Fallback min similarity |
| `VECINITA_RAG_CONFIG_FALLBACK_SYSTEM_PROMPT` | string | (built-in) | No | Fallback system rules text |
| `VECINITA_RAG_CONFIG_FALLBACK_MAX_TOKENS` | int | `256` | No | Fallback LLM max tokens |
| `VECINITA_RAG_CONFIG_FALLBACK_TEMPERATURE` | float | `0.2` | No | Fallback LLM temperature |
| `VECINITA_EVAL_JUDGE_TEMPERATURE_DEFAULT` | float | `0.2` | No | Default judge temperature in playground |

#### `EvalConfig` validation bounds (API body / preset / promote)

Validated in `vecinita_shared_schemas` per ADR-035 §5. Playground form defaults match ChatRAG env
defaults (RD-137), not live production DB config until user loads a preset.

| Field | Type | Bounds | Default |
|-------|------|--------|---------|
| `top_k` | int | 1–50 | 5 |
| `min_retrieval_score` | float | 0.0–1.0 | 0.2 |
| `system_prompt` | string | 1–8000 chars | built-in ChatRAG default |
| `max_tokens` | int | 1–1024 | 256 |
| `temperature` | float | 0.0–2.0 | 0.2 |
| `corpus_profile` | enum | `fixture` \| `staging` | `fixture` |
| `criteria_ids` | uuid[] | must reference enabled `eval_criteria` rows | all active |
| `judge_temperature` | float | 0.0–2.0 | 0.2 |
| `model_id` | string | valid Ollama tag on Modal `vecinita-models` volume | `qwen2.5:1.5b-instruct` |

Model selection: **Ollama model picker** on Modal (RD-139–RD-141). Playground lists models via
Ollama API; missing models trigger a Modal background pull job into `vecinita-models`. Promote
includes `model_id` so production ChatRAG switches LLM at runtime.

**Eval LLM read timeout (BUG-2026-07-08):** eval batches build their `LlmClient` with a
**900s** read timeout (`vecinita_eval.modal_llm._EVAL_LLM_TIMEOUT_S`), well above the 120s
`LlmClient` default. This is **scoped to eval only** — interactive chat keeps the 120s default.
Golden/ad-hoc first-token latency on a freshly-loaded model otherwise surfaced as
`"The read operation timed out"`.

### Admin auth — Supabase (EV-005 F34)

Used by the **Data Management API** and the **Internal Write API** to verify operator Supabase
JWTs (`Authorization: Bearer`), and by the **DM frontend** for the SPA session. Operator identity
lives in Supabase only; the corpus DB stays PII-free (ADR-026). All values are **secrets** —
delivered via Modal secrets / DO env, **never** committed (no-operator-spec-commits). Resolved in
04-tech-plan (ADR-027) + 07-build (ADR-028): verification = **ES256/JWKS** from
`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`; role source = **`app_metadata.role`** read directly
from the verified JWT (no `user_roles` table).

**Backends (DM API + internal-write API):**

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `SUPABASE_URL` | string | — | Yes (admin) | Supabase project URL (canonical `https://cfuvghdsuwactfeamtym.supabase.co`); base for auth / admin API |
| `SUPABASE_SECRET_KEY` | string (secret) | — | Yes (admin) | Server-side Supabase key for admin/auth operations (invite, first-admin seed; new key scheme, formerly service_role) |
| `SUPABASE_JWT_AUD` | string | `authenticated` | No | Expected JWT `aud` claim for verification |
| `VECINITA_AUTH_REQUIRED` | string | `true` | No | `true` enforces JWT on admin routes; `false` only for local dev without Supabase |

> `SUPABASE_DATABASE_PASSWORD` / `SUPABASE_URI` are Supabase's own Postgres credentials (for
> branching/migrations on the Supabase project via the Supabase CLI) — **not** the Vecinita corpus
> `DATABASE_URL` (which stays DO-only, H8). First-admin bootstrap uses `SUPABASE_ADMIN_EMAIL` /
> `SUPABASE_ADMIN_PASSWORD` (operator-only, in `prod.env`; never tracked). Invitation email delivery
> requires a **custom SMTP** provider configured on the Supabase project (TP-S004-08).

**DM frontend (build-time):**

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VITE_SUPABASE_URL` | string | — | Yes (admin build) | Supabase project URL for `@supabase/supabase-js` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | string | — | Yes (admin build) | Supabase **publishable** key (browser-safe; new key scheme, formerly anon) |

### Admin user management + email (EV-006 F35)

User-management endpoints (`/admin/users*`) wrap the Supabase **Admin API**; the secret key is used
**server-side only**. Email delivery uses **Resend** SMTP, encoded in `supabase/config.toml` so
`supabase config push` is the single source of truth (ADR-029). Identity stays in Supabase; the
corpus DB stays PII-free.

**Backend hosting `/admin/users*` (host resolved in 04-tech-plan):**

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `SUPABASE_SECRET_KEY` | string (secret) | — | Yes (F35) | Supabase Admin API key for `/admin/users*` (invite/list/role/disable/delete/reset/revoke-invite). **Server-side only**; never in browser builds. Previously seed/operator-shell only (F34). |
| `VECINITA_ADMIN_FRONTEND_URL` | string (URL) | — | Yes (F35 EV-007) | Deployed admin SPA origin **without trailing slash** — used to build `redirect_to` for GoTrue invite/resend/recovery (`{url}/accept-invite`, `{url}/reset-password`). Modal DM backend secret (also used by internal-write-api health aggregator). |
| `SUPABASE_SMTP_PASS` | string (secret) | — | Yes (F35 prod) | Resend API key; referenced by `[auth.email.smtp] pass = "env(SUPABASE_SMTP_PASS)"` in `config.toml`. Read by Supabase/CLI, **not** by Vecinita backends. |
| `RESEND_API_KEY` | string (secret) | — | Yes (F35 test-send) | Resend API key (same value as `SUPABASE_SMTP_PASS`) read by the **DM backend** for `POST /admin/email/test` (Resend REST). Modal DM secret only. (ADR-031 TP-S005-22) |
| `RESEND_SENDER_EMAIL` | string | — | Yes (F35 test-send) | Verified Resend sender address (= `[auth.email.smtp] admin_email`) used as the `from` for test sends. Modal DM secret. (ADR-031 TP-S005-22) |

**Supabase `config.toml` (versioned; synced via `config push`):**

| Block / key | Value | Notes |
|-------------|-------|-------|
| `[auth] enable_signup` | `false` | Blocks public self-registration (invite-only) |
| `[auth.email] enable_signup` | `true` | Keeps the email **provider** enabled for operator login; must not be `false` or GoTrue returns `email_provider_disabled` even for invited users |
| `[auth] additional_redirect_urls` | Staging + prod admin origins with `/accept-invite`, `/reset-password`; local dev origins | Full path URLs required; verify Dashboard after `config push` |
| `[auth.email.smtp] enabled` | `true` (prod) | Custom SMTP via Resend |
| `[auth.email.smtp] host` | `smtp.resend.com` | Resend SMTP host |
| `[auth.email.smtp] port` | `465` | Resend SMTP port |
| `[auth.email.smtp] user` | `resend` | Resend SMTP username |
| `[auth.email.smtp] pass` | `env(SUPABASE_SMTP_PASS)` | Resend API key (secret) |
| `[auth.email.smtp] admin_email` / `sender_name` | operator-supplied verified sender (RD-090) | Verified Resend domain |
| `[auth.email.template.{invite,recovery,confirmation,magic_link,email_change}]` | `content_path` → `supabase/templates/*.html` | Path resolves from **project root** (#5124); stacked-bilingual HTML |
| `[auth.email.notification.{password_changed,email_changed,mfa_*}]` | `content_path` → `templates/*.html` | Path resolves from **`supabase/`** (#5124) |
| `[auth.rate_limit] email_sent` | `30` | Max auth emails/hour (custom SMTP required); TP-S005-07 |
| `[auth.email] otp_expiry` | `3600` | OTP/recovery/invite acceptance token expiry (seconds); TP-S005-07 |
| `[auth.email] max_frequency` | `60s` | Per-user resend cooldown between auth emails |
| `[auth] minimum_password_length` | `8` | Minimum operator password length; TP-S005-11 |
| App invite rate limit | `10/hour/admin JWT` | DM backend sliding window on `POST /admin/users/invite`; TP-S005-07 |
| App test-send rate limit | `5/hour/admin JWT` | DM backend sliding window on `POST /admin/email/test`; TP-S005-22 |
| User search `q` | `≥ 3 chars` → GoTrue `filter` | `GET /admin/users`; `< 3` non-empty → `400 invalid_search`; TP-S005-20 |

**DM frontend — auth UX browser config (build-time, not server secrets):**

| Key | Source | Default | Valid | Description |
|-----|--------|---------|-------|-------------|
| `VITE_VECINITA_IDLE_TIMEOUT_MIN` | build env | `30` | int ≥ 1 | Minutes of inactivity before auto sign-out of the current device (UJ-034). TP-S005-17 |
| `VITE_VECINITA_IDLE_WARNING_SEC` | build env | `60` | int ≥ 5 | Seconds the "Stay signed in?" warning shows before timeout. TP-S005-17 |

**DM frontend — remember-me (browser state, not server env):**

| Key | Storage | Default | Values | Description |
|-----|---------|---------|--------|-------------|
| `vecinita.auth.remember` | `localStorage` | `true` (checked) | `true` \| `false` | Remember-me preference (UJ-032). `true` → Supabase session in `localStorage`; `false` → `sessionStorage`. Read **before** `createClient` to select the `storage` adapter. |

### Data Management (Modal)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VECINITA_INTERNAL_WRITE_URL` | string | — | Yes | DO internal write API base URL <!-- 12-verify-deploy: code uses this name, not VECINITA_DO_WRITE_API_URL --> |
| `VECINITA_INTERNAL_API_KEY` | string | — | Yes | Matches DO secret |
| `VECINITA_CHUNK_SIZE_TOKENS` | int | `256` | No | Ingest chunk target (tokenizer-based) |
| `VECINITA_SCRAPE_TIMEOUT_S` | int | `30` | No | Per-URL fetch timeout |
| `VECINITA_LLM_TAG_MAX_TOKENS` | int | `128` | No | Max tokens for LLM tagging completion per document |

### Frontends

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `VITE_VECINITA_CHAT_API_URL` | string | `http://localhost:8000` | Yes (build) | ChatRAG Backend base |
| `VITE_VECINITA_ADMIN_API_URL` | string | — | Yes | Modal ASGI or gateway URL for jobs |
| `VITE_VECINITA_CORPUS_API_URL` | string | — | Yes (admin) | Internal write API base for corpus/tag admin |
| `VITE_VECINITA_CORPUS_API_KEY` | string | — | Yes (admin build) | Bearer token for tag/chunk admin routes |

### Browser locale (EV-004 F31 — not server env)

| Key | Storage | Default | Values | Description |
|-----|---------|---------|--------|-------------|
| `vecinita.locale` | `localStorage` | Browser-detected | `en` \| `es` | Shared UI locale for ChatRAG + admin; `detectBrowserLocale()` when unset |

**Detection rules:** `navigator.language` starting with `en` → `en`; starting with `es` → `es`; otherwise **ES** (matches ChatRAG).

**HTML:** `LocaleProvider` sets `document.documentElement.lang` to active locale.

**Date/time:** Admin audit timestamps and dashboard dates use UI locale in `Intl.DateTimeFormat` / `toLocaleString()` (F31).

<!-- No VITE_* locale vars — i18n is client-only; no CORS impact -->

### CORS (EV-005 F34)

`VECINITA_CORS_ORIGINS` (existing, per service) controls allowed browser origins.

- **ChatRAG API** (`apps/chat-rag-backend`): set `VECINITA_CORS_ORIGINS` to the **ChatRAG frontend origin only** (strict — RD-079). No wildcard.
- **Admin APIs** (DM API + internal-write API): allow the **admin frontend origin** and add `Authorization` to allowed request headers (so the bearer JWT preflight passes — H4).

<!-- TP-019 / TS-EV002-C01: Health dashboard uses backend aggregator at GET /internal/v1/health/all
     (via VITE_VECINITA_CORPUS_API_URL). Frontend does NOT poll services directly. -->

## Recommended defaults (spec)

| Parameter | Value | Reference |
|-----------|-------|-----------|
| `VECINITA_TOP_K` | 5 | RD interview |
| `VECINITA_CHUNK_SIZE_TOKENS` | 256 | RD interview |
| Embedding dimension | 384 | FastEmbed / pgvector |
| `VECINITA_LLM_BACKEND` | `vllm` | ADR-009, RD-021 |

## Validation rules

| Rule | Enforcement |
|------|-------------|
| `VECINITA_TOP_K` ≥ 1 and ≤ 50 | Config module at startup |
| `VECINITA_MIN_RETRIEVAL_SCORE` ≥ 0 and < 1 | Config module at startup |
| `VECINITA_CHAT_MAX_TOKENS` ≥ 32 and ≤ 2048 | Config module at startup |
| `VECINITA_CHUNK_SIZE_TOKENS` ≥ 64 | Ingest validation |
| `VECINITA_MAX_TAGS_PER_DOCUMENT` ≥ 1 and ≤ 20 | Config module |
| `VECINITA_MAX_TAGS_PER_CHUNK` ≥ 1 and ≤ 10 | Config module |
| `VECINITA_BROWSE_PAGE_SIZE` ≥ 1 and ≤ 100 | Config module |
| `VECINITA_AUDIT_RETENTION_DAYS` ≥ 0 (0 = forever) | Config module |
| `VECINITA_STATS_ENABLED` in `true`, `false` | Config module |
| `VECINITA_HEALTH_TIMEOUT_MS` ≥ 1000 and ≤ 30000 | Config module (internal-write-api) |
| Reject unknown `VECINITA_*` in strict mode | Optional dev strictness |
| No identity fields in public API bodies | OpenAPI + Pydantic models |
| `VECINITA_AUTH_REQUIRED` in `true`, `false` | Config module (admin backends, F34) |
| `SUPABASE_URL` set when `VECINITA_AUTH_REQUIRED=true` | Admin backend startup (F34; JWKS from URL) |
| ChatRAG `VECINITA_CORS_ORIGINS` is non-wildcard, frontend origin only | Config / deploy review (F34, RD-079) |
| `SUPABASE_SECRET_KEY` set on the backend hosting `/admin/users*` | Admin user-mgmt startup (F35); server-side only |
| `[auth.email.template.*]` `content_path` resolves from project root; `[auth.email.notification.*]` from `supabase/` | `scripts/check_supabase_config.sh` / TC-095 (#5124) |
| `[auth.email.smtp] pass` references `env(SUPABASE_SMTP_PASS)` (no literal secret) | Supabase config contract (F35, TC-094) |
| `vecinita.auth.remember` in `true`, `false` | DM frontend (F35; default `true`) |
| `RESEND_API_KEY` + `RESEND_SENDER_EMAIL` set on DM backend hosting `/admin/email/test` | Test-send startup (F35); `503 email_unconfigured` if unset (TP-S005-22) |
| `q` on `GET /admin/users` is empty or ≥ 3 chars | DM backend (F35; `400 invalid_search` otherwise, TP-S005-20) |

## Configuration files

**`vecinita.yaml`** (v1, audited S5.5): Optional repo-root or `infra/vecinita.yaml` for local/staging defaults. Production on DO/Modal still uses platform secrets for sensitive values; YAML holds non-secret defaults (e.g. `top_k`, `chunk_size_tokens`, service URLs for local compose).

```yaml
# Example (non-secret defaults only)
env: development
chat_rag:
  top_k: 5
  request_timeout_s: 60
ingest:
  chunk_size_tokens: 256
  scrape_timeout_s: 30
```

Precedence: CLI flags > environment variables > `vecinita.yaml` > table defaults above.

## CLI flags

⚠️ **Not discussed:** No user-facing CLI in v1 beyond developer scripts (`alembic`, `modal`, `docker-compose`).

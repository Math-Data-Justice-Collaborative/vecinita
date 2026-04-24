# Render Shared Environment Variable Contract

This document is the single source of truth for environment variables required by each
Render-deployed service. Set these in the Render dashboard before triggering the first
deploy. Variables marked **Required** will cause startup failures if missing.

Shared contract templates:

- `.env.prod.render.example`
- `.env.staging.render.example`

Use these template files as the authoritative key sets for CI contract/parity checks.

## Credentials parity with local `.env`

Values you keep in gitignored **`.env`**, **`.env.local`**, **`.env.prod.render`**, or **`.env.staging.render`** (copied from the examples below) must appear on **Render** under the **same variable names** the services read at runtime. Render does not rename keys for you.

| Where you work | Template to copy keys from |
|----------------|----------------------------|
| Production Render Environment Group / per-service env | [`.env.prod.render.example`](../../.env.prod.render.example) |
| Staging Render Environment Group / per-service env | [`.env.staging.render.example`](../../.env.staging.render.example) |
| Local full-stack development | [`.env.local.example`](../../.env.local.example) |

**Modal:** On Render, set **`MODAL_TOKEN_ID`** and **`MODAL_TOKEN_SECRET`**. When **`OLLAMA_BASE_URL`**, **`EMBEDDING_SERVICE_URL`**, or other resolved URLs point at **`*.modal.run`**, also set **`MODAL_FUNCTION_INVOCATION=auto`** (or **`1`**) so the agent and gateway use Modal **`Function.from_name`** instead of raw HTTP to deprecated ASGI endpoints (see `backend/src/services/modal/invoker.py`). With **`auto`**, invocation turns on only when both **`MODAL_TOKEN_*`** values are set. If your local `.env` only has **`MODAL_TOKEN_ID`** / **`MODAL_TOKEN_SECRET`** (see `.env.local.example`), paste the same token values into Render using the **`MODAL_TOKEN_*`** names — production/staging services do not read `MODAL_API_TOKEN_*`.

**Postgres:** Prefer **`DATABASE_URL`** (Render blueprints can inject it with `fromDatabase`). Some components also accept **`DB_URL`** as an optional alias if an existing secret uses that name.

**Modal scraper Postgres:** Scraper Modal functions (`modal_scrape_job_submit`, list/cancel, etc.) run **outside** Render’s [private network](https://render.com/docs/postgresql-creating-connecting#internal-connections). They **cannot** use the internal hostname (`dpg-…-a`) from the Render web service’s `DATABASE_URL` — DNS fails with `could not translate host name … to address`. In Modal secret group **`vecinita-scraper-env`**, set **`MODAL_DATABASE_URL`** to the same database using Render’s [**external** database URL](https://render.com/docs/postgresql-creating-connecting#external-connections) from the database *Connect* / *Info* page (include `?sslmode=require` as for other clients). **`DATABASE_URL`** in that Modal secret may still be set for compatibility, but when **`MODAL_DATABASE_URL`** is non-empty the scraper code **prefers it**. On Render-hosted services only, keep using the internal URL from `fromDatabase` for lower latency. For [backups / recovery](https://render.com/docs/postgresql-backups), [credentials](https://render.com/docs/postgresql-credentials), [HA](https://render.com/docs/postgresql-high-availability), [PgBouncer](https://render.com/docs/postgresql-connection-pooling), and [upgrades](https://render.com/docs/postgresql-upgrading), follow Render’s Postgres docs; Modal only needs a **publicly resolvable** host for the DSN you put in `MODAL_DATABASE_URL`. If the DSN points at a **suspended** instance, you may instead see `SSL connection has been closed unexpectedly` — update the secret and redeploy the Modal app.

**Gateway-owned Modal scraper control plane (`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`):** When set to **`1`** / **`true`** on the **Render gateway** (`vecinita-gateway`), the gateway inserts the `scraping_jobs` row using the service’s normal **`DATABASE_URL`** (internal hostname is fine). It then calls Modal `modal_scrape_job_submit` with a **`job_id`** in the payload so Modal **only enqueues** scrape work and does **not** open Postgres for that RPC. A non-empty **`job_id`** on the request alone implies enqueue-only (no Modal env flag sync required). For **get / list / cancel** on `/api/v1/modal-jobs/scraper`, the gateway reads and updates Postgres directly and **does not** call the corresponding Modal RPCs while the flag is enabled.

**Gateway HTTP pipeline ingest (Modal workers without Postgres):** When Modal scraper workers must not hold any DSN, set on the **gateway** the same comma-separated **`SCRAPER_API_KEYS`** used for other scraper Bearer auth. Internal routes under **`/api/v1/internal/scraper-pipeline/*`** (see `backend/src/api/router_scraper_pipeline_ingest.py`) accept the header **`X-Scraper-Pipeline-Ingest-Token`** when its value matches **any** key segment in **`SCRAPER_API_KEYS`**. On Modal secret **`vecinita-scraper-env`**, set **`SCRAPER_GATEWAY_BASE_URL`** to the gateway’s public base URL (e.g. `https://your-gateway.onrender.com`) and the **same** **`SCRAPER_API_KEYS`** string as on the gateway. Modal workers send the **first** non-empty segment in that header (leading commas are skipped). The scraper’s `get_db()` then uses HTTP to persist crawl/process/chunk/embed state on Render Postgres. You can omit **`MODAL_DATABASE_URL`** / **`DATABASE_URL`** on Modal for pipeline workers when this pair is set. Modal RPCs **`modal_scrape_job_get` / list / cancel** still require Postgres unless the gateway serves those routes with **`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`** (recommended).

**See also (feature 012 — gateway HTTP contract for operators):** [`specs/012-queued-page-ingestion-pipeline/contracts/gateway-ingestion-http-surface.md`](../../specs/012-queued-page-ingestion-pipeline/contracts/gateway-ingestion-http-surface.md) — correlation IDs, stable error JSON for browser-visible routes, and OpenAPI/Pact expectations (**FR-011–FR-015**).

**Partial HTTP pair on Modal:** If **`SCRAPER_GATEWAY_BASE_URL`** is set but **`SCRAPER_API_KEYS`** has no usable first segment (empty, or only whitespace between commas), or the URL is missing while keys are set, workers fail fast with **`ConfigError: … Render gateway …`** pointing at this document—**not** a generic Postgres connection error. Fix by setting **both** the public gateway origin and a matching key list (same string as on the gateway).

**Worker failure visibility:** Scrape/processor/chunker Modal entrypoints previously called `get_db()` again inside a generic `except` when marking a job `FAILED`, which could surface the **same** `ConfigError` twice in Modal logs (“During handling of the above exception…”). The worker path now skips that second `get_db()` for `ConfigError` so operators see a **single** configuration failure.

**Exceptional debugging only (`SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL`):** The scraper may honor **`SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL=1`** (or `true`/`yes`/`on`) on Modal **only** for short, approved debugging sessions. It allows direct Postgres from Modal cloud despite the default gateway-first policy. **Do not** leave this enabled in production steady state; treat changes like any other secret rotation (time-bounded, audited, reverted after triage). Production pipeline workers should use **`SCRAPER_GATEWAY_BASE_URL` + `SCRAPER_API_KEYS`** instead.

**Regression coverage (CI):** Gateway-owned submit with **`job_id`** injection (**FR-004** style behavior) is covered by **`backend/tests/test_api/test_router_modal_jobs.py`** (e.g. `test_modal_scraper_submit_gateway_persist_injects_job_id`). Multi-segment pipeline ingest auth (**FR-005** gateway side) is covered by **`backend/tests/test_api/test_router_scraper_pipeline_ingest.py`** (e.g. `test_pipeline_ingest_accepts_any_listed_api_key`). Modal worker persistence matrix and failure helper are covered by **`services/scraper/tests/unit/test_get_db_modal_gateway.py`** and **`services/scraper/tests/unit/test_worker_failure_paths.py`** in the scraper package tests.

After adding a new key to the app, update the matching example file and your Render env group so names stay aligned.

### Go / no-go checklist (Modal scraper + Postgres DNS class failures)

Use this before calling live contract tests or declaring the gateway “healthy” for hosted scraper
jobs (`specs/003-consolidate-scraper-dm`):

| # | Check | Pass criteria |
|---|--------|----------------|
| 1 | **Gateway** `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` | Matches intended mode (`1`/`true` when gateway owns `scraping_jobs` inserts + Modal submit is enqueue-only). |
| 2 | **Gateway** `DATABASE_URL` (or `DB_URL`) | Non-empty when gateway-owned persistence is enabled; uses **internal** Render hostname for the gateway process only. |
| 3 | **Modal** pipeline persistence | Either **`MODAL_DATABASE_URL`** (external DSN, not internal `dpg-*-a`) for legacy direct Postgres **or** **`SCRAPER_GATEWAY_BASE_URL` + `SCRAPER_API_KEYS`** matching the gateway (HTTP ingest; no Modal DSN for workers). |
| 4 | **Modal** `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` | Optional on Modal when submit payloads always include **`job_id`** from the gateway; still recommended for explicit split. |
| 5 | **Gateway** `SCRAPER_API_KEYS` | Set when Modal uses HTTP pipeline ingest; must match Modal’s key list (any segment may be sent in `X-Scraper-Pipeline-Ingest-Token`). |
| 6 | Symptom spot-check | `GET /api/v1/modal-jobs/scraper` returns **not** `500` with `could not translate host name "dpg-…"` when dependencies above are satisfied. |

---

## vecinita-data-management-frontend-v1 (Render Web Service)

This frontend image writes runtime config to `dist/env.js` at container startup,
so `VITE_*` values can be provided as runtime environment variables without
rebuilding the image.

| Variable | Required | Description |
|---|---|---|
| `VITE_DM_API_BASE_URL` | **Required** (preferred) | Same value as the historical `VITE_VECINITA_SCRAPER_API_URL`: public origin of **`vecinita-data-management-api-v1`** (no `*.modal.run`). |
| `VITE_VECINITA_SCRAPER_API_URL` | Legacy alias | Still accepted if `VITE_DM_API_BASE_URL` is unset. |
| `VITE_DEFAULT_SCRAPER_USER_ID` | Optional | Default user ID submitted with scraping jobs. Defaults to `frontend-user` if absent. |

> **Naming note:** `VITE_VECINITA_SCRAPER_API_URL` is the historical name for the
> data-management API base URL. Despite the `SCRAPER` in the name, it points at the
> data-management API web service, not directly at the Modal scraper endpoint.

**Partial rollout (007):** When the scraper’s legacy `*.modal.run` ASGI remains deployed for
non-operator clients, treat the **Render `vecinita-data-management-api` URL** (and matching
`VITE_DM_API_BASE_URL`) as **authoritative** for operator scraping in the DM SPA. Do not point
the DM frontend at the gateway **`/api/v1/modal-jobs/scraper`** path for supported workflows.

---

## vecinita-data-management-api-v1 (Render Web Service — Scraper FastAPI image)

Blueprint builds [`services/scraper`](../../services/scraper) (`vecinita_scraper`). At startup the process validates config and **fails immediately** if production auth is incomplete (`ConfigError: Missing required auth configuration…`).

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | **Required** | Postgres DSN (root blueprint injects via `fromDatabase` on `vecinita-postgres`). |
| `SCRAPER_API_KEYS` | **Required** | Comma-separated Bearer token values accepted on protected routes (`Authorization: Bearer …`). Set on the **Render** env group linked to this service. Without this, Uvicorn exits during import. |
| `VECINITA_EMBEDDING_API_URL` | **Required** | Public URL of the embedding service (typically Modal). |
| `CORS_ORIGINS` | **Required** | Comma-separated allowed browser origins. **Must not be `*` in production** when cookies or credentials matter. |
| `ENVIRONMENT` | **Required for strict checks** | Use `production` on Render (see `render.yaml`). Enables Modal token validation. |
| `MODAL_TOKEN_ID` | **Required** when `ENVIRONMENT=production` | Modal workspace token ID for server-side Modal usage. |
| `MODAL_TOKEN_SECRET` | **Required** when `ENVIRONMENT=production` | Modal workspace token secret. |
| `MODAL_FUNCTION_INVOCATION` | Recommended | Use `auto` or `1` when upstream embedding/model/scraper calls use Modal **functions** from this service (align with gateway semantics; see `packages/service-clients/service_clients/modal_invoker.py`). |
| `MODAL_WORKSPACE` | Recommended | Modal workspace slug (e.g. `vecinita`). |
| `VECINITA_MODEL_API_URL` | Recommended | Model API base URL when model-assisted features run. |
| `SCRAPER_DEBUG_BYPASS_AUTH` | Must be `false` | Only `true` in local/dev/test; production must keep `false`. |
| `DEV_ADMIN_BEARER_TOKEN` | Optional | Legacy compatibility: if set, also treated as an accepted Bearer secret. |
| `LOG_LEVEL` | Optional | Defaults to `INFO`. |
| `UPSTREAM_TIMEOUT_SECONDS` | Optional | Upstream HTTP timeout (seconds). |

**Modal (`vecinita-scraper-env`):** If you also deploy the same FastAPI behind Modal (`vecinita_scraper.api.app`), put the **same** `SCRAPER_API_KEYS` (and DB / upstream URLs) in the Modal secret group `vecinita-scraper-env`. GitHub Actions does not push those values to Render or Modal; operators define secrets in each platform.

**Shared contract / CI:** The monorepo validates `.env.prod.render` / `.env.staging.render` against [`backend/src/utils/render_env_contract.py`](../../backend/src/utils/render_env_contract.py). `SCRAPER_API_KEYS` must not remain the old template literal `replace-with-comma-separated-api-keys`.

> **Region and CORS setup order (critical):**
> 1. Deploy `vecinita-data-management-api-v1` (and staging equivalent) with `SCRAPER_API_KEYS`, `DATABASE_URL`, and upstream URLs set.
> 2. Deploy `vecinita-data-management-frontend-v1` and set `VITE_VECINITA_SCRAPER_API_URL` to this API’s public URL.
> 3. Set `CORS_ORIGINS` on the API to that frontend origin.

---

## vecinita-agent (Render Web Service — Chat Agent)

Root-repo owned. All env vars are controlled by the shared env group `.env.prod.render` in the
Render dashboard. See `render.yaml` for the full list.

| Variable | Required | Description |
|---|---|---|
| `MODAL_FUNCTION_INVOCATION` | **Required** when model/embedding URLs use `*.modal.run` | Use `auto` (recommended) or `1`. Without it, startup fails fast in `enforce_modal_function_policy_for_urls` even if `MODAL_TOKEN_*` are set. |
| `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | **Required** with Modal function invocation | Workspace token pair for `modal.Function.from_name` calls to embedding and chat functions. |

---

## vecinita-gateway (Render Web Service — Chat Gateway)

Root-repo owned. All env vars are controlled by the shared env group `.env.prod.render` in the
Render dashboard. Key vars:

| Variable | Required | Description |
|---|---|---|
| `MODAL_FUNCTION_INVOCATION` | **Required** when upstream embedding/model hosts are `*.modal.run` | Same semantics as on the agent (`auto` recommended). Gateway embed routes and Modal job APIs depend on this when URLs target Modal. |
| `ALLOWED_ORIGINS` | **Required** | Comma-separated chat frontend origins for CORS. |
| `VECINITA_EMBEDDING_API_URL` | **Required** for embed routes | HTTPS base URL of the Modal (or other) embedding service — no trailing path. Must serve `POST /embed` and batch routes used by [`backend/src/api/router_embed.py`](../../backend/src/api/router_embed.py). Canonical Modal `web_app` deploy uses a `*-embedding-web-app.modal.run` host (see `.env.prod.render.example`). Legacy `*-embedding-embeddingservicecontainer-api.modal.run` values are rewritten at runtime to that host (and a mistaken `*-embedding-embedding-web-app*` segment is normalized). |
| `EMBEDDING_SERVICE_AUTH_TOKEN` | Recommended | Sent to the embedding service as `x-embedding-service-token` / `Authorization` from the gateway when set. |
| `REINDEX_SERVICE_URL` | **Required** for `POST /api/v1/scrape/reindex` | Absolute `https://…` URL of the scraper jobs API base, ending in `/jobs` (same shape as [`backend/src/api/router_scrape.py`](../../backend/src/api/router_scrape.py) default). The hostname must resolve from the gateway (typically a public `*.modal.run` host). A typo, internal-only name, or Docker-only hostname causes DNS failures (`Name or service not known`) at runtime — verify with `curl` from the gateway service shell if live API tests fail. |
| `REINDEX_TRIGGER_TOKEN` | Optional | When set, the gateway forwards it as `x-reindex-token` to the reindex endpoint. |
| `AGENT_SERVICE_URL` | **Injected by blueprint** | `render.yaml` sets this via `fromService` (`property: hostport`), which is `host:port` without a scheme. The gateway normalizes it to `http://…` for httpx. Do **not** duplicate in the env group unless you intentionally override the binding. |
| `DEV_ADMIN_BEARER_TOKEN` | Optional | Developer admin bearer token for the chat UI admin panel. |

### OpenAPI / Schemathesis

Contract tests and live Schemathesis runs use [`backend/schemathesis.toml`](../../backend/schemathesis.toml) and [`backend/tests/schemathesis_hooks.py`](../../backend/tests/schemathesis_hooks.py). If Schemathesis reports **schema validation mismatch** on scrape/embed/ask routes, tighten Pydantic constraints and add **`Field(examples=…)`** / **`openapi_examples`** on gateway routers so generated examples stay valid.

**Offline pytest** (`make test-schemathesis`, gateway + agent) uses mocked upstreams in CI. The **scraper / data-management** HTTP API also has offline Schemathesis in [`services/scraper/tests/integration/test_openapi_schemathesis.py`](../../services/scraper/tests/integration/test_openapi_schemathesis.py) (mocked job control; runs in the scraper package test suite).

**Live CLI** ([`backend/scripts/run_schemathesis_live.sh`](../../backend/scripts/run_schemathesis_live.sh), `make test-schemathesis-cli`) targets **gateway** and **data-management** OpenAPI URLs (`GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`). Set optional **`AGENT_SCHEMA_URL`** (e.g. `https://vecinita-agent-lx27.onrender.com/openapi.json`) for a third CLI pass, or run **`make test-schemathesis-cli-agent`** for live pytest Schemathesis on the agent. Gateway runs include `GET /api/v1/ask/stream` by default unless `SCHEMATHESIS_EXCLUDE_ASK_STREAM=1`.

For **agent** in-process Schemathesis, `POST /model-selection` can return **403** when `LOCK_MODEL_SELECTION` is enabled (policy, not missing credentials); related pytest/live-agent tuning may use `SCHEMATHESIS_EXCLUDE_IGNORED_AUTH` / `SCHEMATHESIS_EXCLUDE_AGENT_MODEL_SELECTION` (see script and `TESTING_DOCUMENTATION.md`).

---

## Deploy Hook Secrets (GitHub Actions)

Each service repo that uses a Render deploy hook (`curl POST $RENDER_DEPLOY_HOOK_URL`) must have
`RENDER_DEPLOY_HOOK_URL` set in its GitHub Actions secrets.

| GitHub Repository | Where to set | Connects to |
|---|---|---|
| `Math-Data-Justice-Collaborative/vecinita-data-management` | Repo Settings → Secrets → Actions | `vecinita-data-management-api-v1` deploy hook |
| `Math-Data-Justice-Collaborative/vecinita-data-management-frontend` | Repo Settings → Secrets → Actions | `vecinita-data-management-frontend-v1` deploy hook |
| `joseph-c-mcguire/Vecinitafrontend` | Repo Settings → Secrets → Actions | `vecinita-frontend` deploy hook |

> The `vecinita-data-management` repo's `deploy.yml` should trigger the data-management API
> Render deploy hook. Wire the API hook URL into
> `vecinita-data-management`'s `RENDER_DEPLOY_HOOK_URL` secret so the orchestrator's
> `deploy_data_management_api` input deploys the API service as intended.

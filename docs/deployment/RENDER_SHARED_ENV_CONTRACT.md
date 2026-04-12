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

**Modal:** On Render, set **`MODAL_TOKEN_ID`** and **`MODAL_TOKEN_SECRET`**. If your local `.env` only has **`MODAL_API_TOKEN_ID`** / **`MODAL_API_TOKEN_SECRET`** (see `.env.local.example`), paste the same token values into Render using the **`MODAL_TOKEN_*`** names — production/staging services do not read `MODAL_API_TOKEN_*`.

**Postgres:** Prefer **`DATABASE_URL`** (Render blueprints can inject it with `fromDatabase`). Some components also accept **`DB_URL`** as an optional alias if an existing secret uses that name.

After adding a new key to the app, update the matching example file and your Render env group so names stay aligned.

---

## vecinita-data-management-frontend-v1 (Render Web Service)

This frontend image writes runtime config to `dist/env.js` at container startup,
so `VITE_*` values can be provided as runtime environment variables without
rebuilding the image.

| Variable | Required | Description |
|---|---|---|
| `VITE_VECINITA_SCRAPER_API_URL` | **Required** | Public URL of the `vecinita-data-management-api-v1` Render web service (or staging equivalent). No production fallback — if unset, the "Scraper API not configured" banner will appear for all users. |
| `VITE_DEFAULT_SCRAPER_USER_ID` | Optional | Default user ID submitted with scraping jobs. Defaults to `frontend-user` if absent. |

> **Naming note:** `VITE_VECINITA_SCRAPER_API_URL` is the historical name for the
> data-management API base URL. Despite the `SCRAPER` in the name, it points at the
> data-management API web service, not directly at the Modal scraper endpoint.

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

---

## vecinita-gateway (Render Web Service — Chat Gateway)

Root-repo owned. All env vars are controlled by the shared env group `.env.prod.render` in the
Render dashboard. Key vars:

| Variable | Required | Description |
|---|---|---|
| `ALLOWED_ORIGINS` | **Required** | Comma-separated chat frontend origins for CORS. |
| `VECINITA_EMBEDDING_API_URL` | **Required** for embed routes | HTTPS base URL of the Modal (or other) embedding service — no trailing path. Must serve `POST /embed` and batch routes used by [`backend/src/api/router_embed.py`](../../backend/src/api/router_embed.py). Canonical Modal `web_app` deploy uses a `*-embedding-web-app.modal.run` host (see `.env.prod.render.example`). |
| `EMBEDDING_SERVICE_AUTH_TOKEN` | Recommended | Sent to the embedding service as `x-embedding-service-token` / `Authorization` from the gateway when set. |
| `REINDEX_SERVICE_URL` | **Required** for `POST /api/v1/scrape/reindex` | Absolute `https://…` URL of the scraper jobs API base, ending in `/jobs` (same shape as [`backend/src/api/router_scrape.py`](../../backend/src/api/router_scrape.py) default). A typo or Docker-only hostname causes DNS failures (`Name or service not known`) at runtime. |
| `REINDEX_TRIGGER_TOKEN` | Optional | When set, the gateway forwards it as `x-reindex-token` to the reindex endpoint. |
| `AGENT_SERVICE_URL` | **Injected by blueprint** | `render.yaml` sets this via `fromService` (`property: hostport`), which is `host:port` without a scheme. The gateway normalizes it to `http://…` for httpx. Do **not** duplicate in the env group unless you intentionally override the binding. |
| `DEV_ADMIN_BEARER_TOKEN` | Optional | Developer admin bearer token for the chat UI admin panel. |

### OpenAPI / Schemathesis

Contract tests and live Schemathesis runs use [`backend/schemathesis.toml`](../../backend/schemathesis.toml) and [`backend/tests/schemathesis_hooks.py`](../../backend/tests/schemathesis_hooks.py). If Schemathesis reports **schema validation mismatch** on scrape/embed/ask routes, tighten Pydantic constraints and add **`Field(examples=…)`** / **`openapi_examples`** on gateway routers so generated examples stay valid. Live CLI: [`backend/scripts/run_schemathesis_live.sh`](../../backend/scripts/run_schemathesis_live.sh) — agent runs skip the `ignored_auth` check by default (`SCHEMATHESIS_EXCLUDE_IGNORED_AUTH=1`) because `POST /model-selection` returns **403** when model selection is locked (policy), not missing credentials.

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

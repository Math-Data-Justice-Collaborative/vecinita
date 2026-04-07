# Render Shared Environment Variable Contract

This document is the single source of truth for environment variables required by each
Render-deployed service. Set these in the Render dashboard before triggering the first
deploy. Variables marked **Required** will cause startup failures if missing.

---

## vecinita-data-management-frontend (Render Static Site)

VITE_* variables are baked into the JavaScript bundle at **build time** by Vite. Changing
them requires a new deploy; they cannot be injected at runtime.

| Variable | Required | Description |
|---|---|---|
| `VITE_VECINITA_SCRAPER_API_URL` | **Required** | Public URL of the `vecinita-modal-proxy` Render web service (e.g. `https://vecinita-modal-proxy.onrender.com`). No production fallback — if unset, the "Scraper API not configured" banner will appear for all users. |
| `VITE_DEFAULT_SCRAPER_USER_ID` | Optional | Default user ID submitted with scraping jobs. Defaults to `frontend-user` if absent. |

> **Naming note:** `VITE_VECINITA_SCRAPER_API_URL` is the historical name for the
> data-management API base URL. Despite the `SCRAPER` in the name, it points at the
> proxy service, not directly at the Modal scraper endpoint.

---

## vecinita-modal-proxy (Render Web Service — the Data Management API)

The proxy is a FastAPI service that authenticates requests and routes them to Modal-deployed
backends. All variables below are runtime environment variables.

| Variable | Required | Description |
|---|---|---|
| `MODAL_TOKEN_ID` | **Required** | Modal workspace token ID. Used to authenticate proxy-to-Modal calls. |
| `MODAL_TOKEN_SECRET` | **Required** | Modal workspace token secret. |
| `VECINITA_SCRAPER_API_URL` | **Required** | Public URL of the vecinita-scraper Modal endpoint. |
| `CORS_ORIGINS` | **Required** | Comma-separated list of allowed frontend origins. **Must not be `*` in production.** Set to the data-management frontend's Render URL (e.g. `https://vecinita-data-management-frontend.onrender.com`). |
| `VECINITA_MODEL_API_URL` | Recommended | Public URL of the vecinita-model Modal endpoint. Required if model routes are used. |
| `VECINITA_EMBEDDING_API_URL` | Recommended | Public URL of the vecinita-embedding Modal endpoint. Required if embedding routes are used. |
| `PROXY_AUTH_TOKEN` | Optional | Shared secret for `X-Proxy-Token` header authentication. If set, callers must include this header. |
| `ENVIRONMENT` | Optional | Runtime environment label. Defaults to `production`. |
| `LOG_LEVEL` | Optional | Logging verbosity. Defaults to `INFO`. |
| `UPSTREAM_TIMEOUT_SECONDS` | Optional | Timeout for upstream Modal calls in seconds. Defaults to `55`. |
| `RATE_LIMIT_DEFAULT` | Optional | Global rate limit per client IP. Defaults to `60/minute`. |
| `BACKEND_ROUTE_RULES_JSON` | Optional | JSON array of custom route rules overriding defaults. |

> **Region and CORS setup order (critical):**
> 1. Create the `vecinita-modal-proxy` web service first — you need its public URL before configuring the frontend.
> 2. Create the `vecinita-data-management-frontend` static site and set `VITE_VECINITA_SCRAPER_API_URL` to the proxy URL from step 1.
> 3. Return to `vecinita-modal-proxy` and set `CORS_ORIGINS` to the frontend URL from step 2.

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
| `DEV_ADMIN_BEARER_TOKEN` | Optional | Developer admin bearer token for the chat UI admin panel. |

---

## Deploy Hook Secrets (GitHub Actions)

Each service repo that uses a Render deploy hook (`curl POST $RENDER_DEPLOY_HOOK_URL`) must have
`RENDER_DEPLOY_HOOK_URL` set in its GitHub Actions secrets.

| GitHub Repository | Where to set | Connects to |
|---|---|---|
| `Math-Data-Justice-Collaborative/vecinita-data-management` | Repo Settings → Secrets → Actions | `vecinita-modal-proxy` deploy hook |
| `Math-Data-Justice-Collaborative/vecinita-data-management-frontend` | Repo Settings → Secrets → Actions | `vecinita-data-management-frontend` deploy hook |
| `joseph-c-mcguire/Vecinitafrontend` | Repo Settings → Secrets → Actions | `vecinita-frontend` deploy hook |

> The `vecinita-data-management` repo's `deploy.yml` triggers the proxy's Render deploy hook
> (not a deploy of the monorepo itself, which has no Render service). Wire the proxy hook URL
> into `vecinita-data-management`'s `RENDER_DEPLOY_HOOK_URL` secret so the orchestrator's
> `deploy_data_management_api` input deploys the proxy as intended.

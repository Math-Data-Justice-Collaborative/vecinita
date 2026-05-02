# Contract: Environment wiring — chat frontend, gateway, agent

## Purpose

Define how **documented** environment variables align across the chat SPA (`frontend/`), the unified gateway, and the LangGraph agent so operators can copy from **templates only** (never committed `.env` with secrets).

## ServiceEndpointConfig catalog

Logical names below tie runtime roles to template variables (see root `.env.local.example`, `frontend/.env.example`, and `apps/data-management-frontend/.env.example`). Values are **placeholders** only—never commit real secrets.

| Logical name | Role | Primary template variables (examples) |
|--------------|------|----------------------------------------|
| **gateway** | Chat browser → gateway base URL / Vite proxy | `VITE_GATEWAY_URL`, `VITE_BACKEND_URL`, `VITE_GATEWAY_PROXY_TARGET` |
| **agent** | Gateway process → LangGraph agent HTTP | `AGENT_SERVICE_URL`; Render may use `fromService` in `render.yaml` |
| **dm_api** | DM SPA → data-management scraper HTTP API | `VITE_VECINITA_SCRAPER_API_URL`; optional `VITE_VECINITA_GATEWAY_URL` when modal-jobs flag is on |
| **dm_frontend** | DM SPA dev origin (CORS / local smoke) | Documented dev origin (e.g. `http://localhost:5174`); align with CORS allowlists in `apis/data-management-api/README.md` |

## Variable roles

| Concern | Primary consumer | Template variables |
|--------|------------------|-------------------|
| Browser → gateway base | `frontend` (Vite) | `VITE_GATEWAY_URL`, `VITE_BACKEND_URL`, `VITE_GATEWAY_PROXY_TARGET` |
| Gateway → agent HTTP | `backend` gateway | `AGENT_SERVICE_URL` (local/compose); Render may inject via `render.yaml` `fromService` |
| Contract testing / docs | CI, developers | `GATEWAY_SCHEMA_URL`, `AGENT_SCHEMA_URL`, optional `RENDER_GATEWAY_URL`, `RENDER_AGENT_URL` |
| Server-side timeouts | Gateway | `AGENT_TIMEOUT`, `AGENT_STREAM_TIMEOUT` |

## Precedence and invariants

1. **Browser base URL**: `VITE_GATEWAY_URL` overrides `VITE_BACKEND_URL` when set; implementation detail lives in `frontend/src/app/services/agentService.ts`.
2. **Path shape**: Absolute gateway URLs must normalize to a path that includes the versioned API prefix expected by the client (`/api/v1`); relative `/api` relies on Vite proxy rewriting.
3. **Timeout ordering**: `VITE_AGENT_REQUEST_TIMEOUT_MS` MUST remain greater than gateway `AGENT_TIMEOUT` where documented, so the UI does not abort before the gateway returns a fallback.
4. **Render host heuristics**: Client code may rewrite `*-agent` hosts to `*-gateway` for specific deployment patterns; ops docs must not recommend configuring the browser with an agent-only URL unless that path is explicitly supported.

## Playwright and E2E bases

- E2E config MUST use the same logical URLs as human devs: chat base URL from `VITE_GATEWAY_URL` / proxy; optional `PLAYWRIGHT_*` overrides documented in `quickstart.md` once tasks add them.
- Avoid testing **third-party** origins; stub with Playwright routing when only Vecinita contract is under test ([Playwright best practices](https://playwright.dev/docs/best-practices)).

## Non-goals

- Storing or reproducing real Render URLs or tokens in specs.
- Changing authentication models (`DEV_ADMIN_*`, Supabase keys) beyond noting they remain separate from gateway URL wiring.

# Quickstart — verify wiring and test stack (local)

All steps use **placeholder** values from `.env.local.example` / package `.env.example` files. Do not paste production secrets into shell history or commits.

**ServiceEndpointConfig** (logical names `gateway`, `agent`, `dm_api`, `dm_frontend` → template vars): see [contracts/env-wiring-chat-gateway-agent.md §ServiceEndpointConfig catalog](./contracts/env-wiring-chat-gateway-agent.md#serviceendpointconfig-catalog).

## Prerequisites

- Node and pnpm/npm as per repo root README
- Python 3.11 + `uv`/`pip` for backend services and Schemathesis
- Optional: Docker for gateway/agent/DM Compose
- For Playwright: `pnpm exec playwright install chromium` (or documented workspace command) when running E2E locally

## 1. Chat frontend ↔ gateway ↔ agent

1. Copy env templates: from repo root, `cp .env.local.example .env.local` and adjust **non-secret** URLs only.
2. Ensure **`frontend/.env`** sets `VITE_GATEWAY_URL`, `VITE_GATEWAY_PROXY_TARGET` as in [spec §FR-002](../spec.md).
3. Start gateway and agent per `make` / `backend/` README.
4. Run `pnpm --dir frontend dev`, smoke chat in the browser.

## 2. Data management frontend ↔ data-management API

1. Start **`services/data-management-api`** (convention **8005**).
2. `apps/data-management-frontend/.env` with `VITE_VECINITA_SCRAPER_API_URL=http://localhost:8005` (or your port).
3. Run DM Vite dev server; open scrape jobs and confirm diagnostics + `/health`.

## 3. Pact (consumer) — local

### Env vars (consumer)

| Variable | Where | Purpose |
|----------|--------|---------|
| `PACT_BROKER_BASE_URL` | shell / CI secrets | Optional broker URL for publish/verify |
| `PACT_BROKER_TOKEN` / publish creds | CI secrets only | Broker auth — never commit |
| Consumer name | Pact test source | Use distinct names per [ServiceEndpointConfig / pyramid](./contracts/pact-schemathesis-playwright-pyramid.md) (e.g. `vecinita-chat-frontend`, `vecinita-dm-frontend`) |

### Steps

1. From the package that hosts Pact tests (`frontend/` or `apps/data-management-frontend/`), run **`npm run test:pact`** (stub until consumer tests land).
2. If using a **broker**, set `PACT_BROKER_BASE_URL` and credentials via **local env only** (never commit); for **file** mode, confirm pact JSON lands under the path CI expects.
3. Repeat for **both** consumers so consumer names do not collide ([contract pyramid](./contracts/pact-schemathesis-playwright-pyramid.md)).

## 4. Schemathesis (provider API)

### Env vars (schemas)

| Variable | Purpose |
|----------|---------|
| `GATEWAY_SCHEMA_URL` | Gateway OpenAPI JSON URL |
| `AGENT_SCHEMA_URL` | Agent OpenAPI JSON URL |
| `SCRAPER_API_KEYS` / `SCRAPER_SCHEMATHESIS_BEARER` | DM / scraper schema tests in CI (see `backend/tests/integration/` and `.github/workflows/test.yml`) |

### Steps

1. Point URLs at running services or fixtures per `TESTING_DOCUMENTATION.md` draft § Schemathesis.
2. From repo root: `make test-schemathesis` or `cd backend && make test-schema` / `make test-schema-data-management` (see root **`Makefile`**).
3. Project defaults live in **`backend/schemathesis.toml`**.

## 5. Playwright (E2E)

### Env vars (E2E)

| Variable | Typical use |
|----------|----------------|
| `E2E_BASE_URL` | Chat app base URL (see **T015** when implemented) |
| Playwright `baseURL` / project env | Set in `playwright.config.ts` per package |

### Steps

1. Start the **same** services your E2E config points at (Compose URL or localhost ports).
2. Chat: `frontend/` — `npm run test:e2e` (see `package.json`). DM: `apps/data-management-frontend/` — `npm run test:e2e` or existing `e2e` / `test:e2e:pr` scripts.
3. For CI-like speed: `npx playwright install chromium` and use **sharding** if the suite grows ([Playwright parallelism](https://playwright.dev/docs/best-practices)).

## 6. Typed DTO check

1. After OpenAPI or Zod changes, run **`tsc --noEmit`** (or workspace typecheck) in each frontend so shared types used by Pact and fetch code stay aligned.

## 7. Definition of done (for implementers)

- Env templates consistent (**FR-001**).
- Pact consumer on PR; provider + Schemathesis + Playwright on documented non-PR workflow (**FR-005–FR-008**, **SC-002–SC-005**).
- `make ci` passes on the implementation PR.

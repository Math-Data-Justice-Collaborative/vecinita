# Contract: Data-management API ↔ frontend alignment

## Purpose

Ensure `apps/data-management-frontend` request bodies, query parameters, and JSON response shapes for **scrape jobs** (and any shared types in `modal-types`) remain compatible with the HTTP API served by **`services/data-management-api`** (scraper FastAPI application) and with **`packages/shared-schemas`** where those models are authoritative.

## Source of truth

1. **Runtime behavior**: FastAPI route handlers and response models on the scraper app bundled in the data-management API image.
2. **Shared Python models**: `services/data-management-api/packages/shared-schemas/shared_schemas/scraper.py` (`ScrapeRequest`, `ScrapeResult`, and any job DTOs re-exported from there).
3. **Machine-readable contract**: OpenAPI 3 JSON from the running service (`/openapi.json` when enabled).

## Frontend surfaces

- **Configuration**: `apps/data-management-frontend/src/app/api/scraper-config.ts` (`scraperJobsApiRoot`, env diagnostics).
- **HTTP client**: `apps/data-management-frontend/src/app/api/rag-api.ts` and `modal-types` TypeScript types.
- **Optional gateway mode**: When `VITE_USE_GATEWAY_MODAL_JOBS` is truthy and `VITE_VECINITA_GATEWAY_URL` is a valid URL, job CRUD uses gateway path `/api/v1/modal-jobs/scraper` — contract is owned by the **gateway** OpenAPI for those operations; this must be listed in gateway Schemathesis coverage if enabled in production.

## Alignment workflow (implementers MUST pick one primary automation)

**Option A — Snapshot diff**

1. Export `openapi.json` from a pinned local or CI-started API instance.
2. Store a canonical snapshot under `specs/` or `apps/data-management-frontend/contracts/` (exact path chosen at implementation time).
3. CI step fails if routes used by `rag-api.ts` change without updating the snapshot and TS types.

**Option B — Codegen**

1. Generate TypeScript interfaces from OpenAPI (e.g. `openapi-typescript`) into a generated file consumed by `rag-api.ts`.
2. PRs that touch scrape routes must include regenerated output.

## Breaking change policy

- Removing or renaming JSON fields consumed by the dashboard requires a **migration note** and coordinated bump of snapshot/codegen in the same PR unless behind a versioned API path (not current standard).

## Verification

- Unit tests: existing `rag-api.test.ts`, `scraper-config` behavior.
- Integration: DM frontend integration tests that hit a mock or real base URL per package README.
- **Pact**: consumer tests in `apps/data-management-frontend/` per **FR-008**; provider verification on DM API (and gateway when modal-jobs mode is in scope)—see [pact-schemathesis-playwright-pyramid.md](./pact-schemathesis-playwright-pyramid.md).
- **Schemathesis**: OpenAPI-driven runs against DM (and gateway paths when modal-jobs enabled).
- **Playwright**: E2E journeys for dashboard + scrape flows against wired env.
- **Typed DTOs**: Pact matchers and `rag-api` must import the same TypeScript types or Zod-inferred types (`../data-model.md` §Typed testing artifacts).
- Manual: steps in `../quickstart.md`.

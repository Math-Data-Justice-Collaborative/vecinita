# Research: Service wiring and contract alignment

## 1. Canonical environment documentation

- **Decision**: Treat **`.env.local.example`** (repo root) as the canonical catalog of cross-app variables; keep **`frontend/.env.example`** and **`apps/data-management-frontend/.env.example`** as role-specific views that repeat only the vars each app reads, with identical semantics and placeholder URLs.
- **Rationale**: A single mental model reduces drift between chat (`VITE_GATEWAY_URL`, `VITE_GATEWAY_PROXY_TARGET`) and backend (`AGENT_SERVICE_URL`, `GATEWAY_PORT`, `RENDER_GATEWAY_URL`, `RENDER_AGENT_URL`, `GATEWAY_SCHEMA_URL`, `AGENT_SCHEMA_URL`).
- **Alternatives considered**: Relying only on per-package READMEs — rejected because operators already use a unified `.env` workflow per root comments.

## 2. Chat frontend gateway vs agent hosts

- **Decision**: Keep the **existing resolution pipeline** (`resolveGatewayUrl`, `normalizeAgentApiBaseUrl`, `resolveApiBase`) as authoritative; planning deliverables only **document** how template values (`/api` locally, absolute `https://…-gateway…` on Render) map to `RENDER_AGENT_URL` / `RENDER_GATEWAY_URL` in root templates—**no duplicate client logic**.
- **Rationale**: `frontend/src/app/services/agentService.ts` already encodes deployment edge cases (direct Render agent host, path normalization to `/api/v1`).
- **Alternatives considered**: New `VITE_AGENT_URL` bypassing gateway — rejected; violates gateway-as-single-edge principle from architecture docs.

## 3. Data-management frontend → API base URL

- **Decision**: Standardize on **`VITE_VECINITA_SCRAPER_API_URL`** pointing at the HTTP origin serving scraper-compatible routes (local default **`http://localhost:8005`** per specs and `.env.example` comments). Document **`VITE_USE_GATEWAY_MODAL_JOBS`** + **`VITE_VECINITA_GATEWAY_URL`** as the optional path for gateway-owned Modal job rows.
- **Rationale**: Matches `apps/data-management-frontend/src/app/api/scraper-config.ts` (`scraperJobsApiRoot`, `gatewayModalJobsScraperRoot`).
- **Alternatives considered**: Renaming env vars — deferred; high churn for Docker and Render blueprints.

## 4. Models and contracts alignment (DM)

- **Decision**: Use **OpenAPI as the contract hub**: export JSON from the running data-management API (same app as `apis/data-management-api` image) and either (a) generate TypeScript types for `rag-api` boundaries, or (b) add a CI script that **diffs** exported OpenAPI against a checked-in snapshot and fails on unexpected breaking changes. Treat **`apis/data-management-api/packages/shared-schemas`** (e.g. `ScrapeRequest`) as the semantic source that should match FastAPI route models.
- **Rationale**: Constitution requires explicit contracts; OpenAPI is already the norm for gateway/agent (`GATEWAY_SCHEMA_URL`, `AGENT_SCHEMA_URL`).
- **Alternatives considered**: Manual-only checklist — rejected; does not scale. Full protobuf — rejected; not in stack.

## 5. Pact for consumer-driven contracts (both systems)

- **Decision**: Implement **Pact** per [Pact documentation](https://docs.pact.io/faq): **consumers** own tests in `frontend/` and `apps/data-management-frontend/` that generate contracts; **providers** (gateway, agent, DM API) run verification with explicit **provider states** for data setup. Publish pacts to a **broker** or **checked-in pactfiles** per spec edge-case “two consumers” (shared broker with consumer/version tags vs isolated repos).
- **Rationale**: Contracts catch integration skew early; aligns with spec **FR-007**, **FR-008**, and clarifications. Pact is **not** a full substitute for collaboration between teams working on consumer and provider code.
- **Alternatives considered**: OpenAPI-only — insufficient for consumer expectations on headers/query shapes; E2E-only — slower and flakier for the same signal density.

## 6. Schemathesis for API (provider) testing

- **Decision**: Keep **Schemathesis** as the **OpenAPI-driven** property-style layer on gateway, agent, and (where applicable) DM/gateway modal-jobs OpenAPI—per [Schemathesis docs](https://schemathesis.readthedocs.io/en/stable/) it generates broad input classes from the schema to find crashes and spec violations. It **complements** Pact: Schemathesis stresses **provider conformance to its own OpenAPI**; Pact stresses **consumer–provider agreement** on what is actually used.
- **Rationale**: Already in repo norms (`TESTING_DOCUMENTATION.md`, `backend/schemathesis.toml`); research-validated breadth of defect detection.
- **Alternatives considered**: Replacing Schemathesis with Pact-only — loses schema-wide fuzzing without re-encoding every edge in pact interactions.

## 7. Playwright for end-to-end compatibility

- **Decision**: Add or extend **Playwright** suites for **chat** and **DM** critical paths: env-correct bases, health/diagnostics, one happy-path chat turn, scrape job list/create/cancel smoke. Follow [Playwright best practices](https://playwright.dev/docs/best-practices): **isolate** tests, **shard** heavy suites in CI, prefer **Chromium-only** in CI when acceptable, use **`page.route`** to stub third-party dependencies not owned by the repo.
- **Rationale**: E2E proves wiring + CORS + SPA routing that unit/Pact layers may miss; spec **FR-006** / **SC-003** place full-stack E2E on main/nightly/dispatch while PRs can run slim Playwright against mocks or partial stack.
- **Alternatives considered**: Cypress — not requested; stick Playwright as single E2E stack.

## 8. Typed classes for integration boundaries

- **Decision**: Centralize **TypeScript** types (prefer **OpenAPI codegen** e.g. `openapi-typescript`, or **Zod** schemas with `infer<>`) for JSON bodies used by **both** `rag-api` / `agentService` **and** Pact matchers, so drift fails compile or consumer tests. Python remains **Pydantic** in `shared-schemas`; CI optionally validates OpenAPI generated from FastAPI matches checked-in spec.
- **Rationale**: “Typed classes” gives compile-time integration checks and narrows `any` in pact and fetch layers.
- **Alternatives considered**: Duplicated inline object literals in tests — rejected; causes silent drift.

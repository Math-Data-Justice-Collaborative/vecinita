# Implementation Plan: Wire chat frontend to gateway/agent and align data-management stack

**Branch**: `005-wire-services-dm-front` | **Date**: 2026-04-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/005-wire-services-dm-front/spec.md`, plus stack direction: **[Pact](https://docs.pact.io/)** for consumer-driven contracts, **typed DTOs/classes** for integration boundaries, **[Schemathesis](https://schemathesis.readthedocs.io/)** for OpenAPI-driven API testing on backends, **[Playwright](https://playwright.dev/)** for end-to-end compatibility of **chatbot** (`frontend/` ↔ gateway/agent) and **data-management** (`apps/data-management-frontend/` ↔ API/gateway modal-jobs) systems.

## Summary

Unify env-driven wiring (templates only—no secrets in repo) so the **chat** SPA targets the gateway/agent consistently and the **data-management** SPA targets the DM API (and optional gateway modal-jobs) with explicit bases. Align **both product lines** with a **four-layer test strategy**: (1) **Pact** consumers in each frontend publishing contracts; **provider verification** on gateway, agent, and DM API surfaces; (2) **Schemathesis** fuzzing/property-style checks against OpenAPI for gateway, agent, and DM-relevant paths; (3) **strictly typed** request/response shapes in TypeScript (and parity with Python/Pydantic or OpenAPI codegen) so Pact matchers and HTTP clients share one truth; (4) **Playwright** E2E journeys proving cross-service compatibility under realistic env (local Compose, staging, or `page.route` stubs for third parties per Playwright guidance). PRs stay fast with mocks/Pact consumer tests; real-stack + Playwright follow **FR-006** / **SC-003** cadence.

## Technical Context

**Language/Version**: TypeScript 5.x (Vite/React) for both frontends; Python 3.11 for gateway, agent, and data-management API (scraper FastAPI surface).  
**Primary Dependencies**: Vite env; FastAPI + Pydantic v2; **@pact-foundation/pact** (or Pact JS v10+) in frontends; **schemathesis** + OpenAPI URLs (`GATEWAY_SCHEMA_URL`, `AGENT_SCHEMA_URL`, DM `openapi.json`); **@playwright/test** for E2E in `frontend/` and `apps/data-management-frontend/` (or root orchestration).  
**Storage**: N/A for wiring; scrape/job persistence unchanged.  
**Testing**: **Layer A — Pact**: consumers in `frontend/` and `apps/data-management-frontend/`; providers wired in `backend/` (gateway/agent) and DM API deployable; pact broker or file publish workflow per spec clarifications. **Layer B — Schemathesis**: property/schema exploration on published OpenAPI (`TESTING_DOCUMENTATION.md`, `backend/schemathesis.toml`). **Layer C — Typed integration**: TypeScript types/Zod (or OpenAPI-generated types) shared by Pact matchers and `agentService` / `rag-api`; Python side `shared-schemas` + FastAPI models. **Layer D — Playwright**: smoke and regression E2E for chat + DM against controlled bases (isolate tests, avoid uncontrolled third-party pages per Playwright best practices).  
**Target Platform**: Linux/macOS dev, Docker Compose, Render; CI with optional Playwright `chromium` install for cost.  
**Project Type**: Monorepo multi-SPA + FastAPI services.  
**Performance Goals**: Keep existing timeouts; Pact/Playwright jobs documented with timeouts; Schemathesis budgets per existing CI norms.  
**Constraints**: No secrets in specs; Pact docs stress **consumer + provider collaboration**—encode team ownership in `TESTING_DOCUMENTATION.md`; contracts are not a substitute for communication ([Pact FAQ](https://docs.pact.io/faq)).  
**Scale/Scope**: Two frontends, gateway, agent, DM API image, env templates, CI workflows, and typed contract artifacts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Community benefit**: **Pass**
- **Trustworthy retrieval**: **Pass**
- **Data stewardship**: **Pass** — templates only; no new ingestion.
- **Safety & quality**: **Pass** — Pact + Schemathesis + Playwright + typed DTOs strengthen verifiable delivery ([Schemathesis overview](https://schemathesis.readthedocs.io/en/stable/)).
- **Service boundaries**: **Pass** — HTTP/OpenAPI/Pact boundaries explicit; no cross-runtime imports.

## Project Structure

### Documentation (this feature)

```text
specs/005-wire-services-dm-front/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── env-wiring-chat-gateway-agent.md
│   ├── data-management-openapi-alignment.md
│   └── pact-schemathesis-playwright-pyramid.md
└── tasks.md            # /speckit.tasks
```

### Source code (implementation targets)

```text
frontend/
  src/app/services/agentService.ts
  src/app/lib/{agentApiResolution.ts,apiBaseResolution.ts}
  tests/ or src/**/*.test.ts          # Vitest + Pact consumer
  tests/e2e/                          # Playwright (chat) — canonical for feature 005: tasks.md T015

apps/data-management-frontend/
  src/app/api/{rag-api.ts,scraper-config.ts}
  tests/                              # Vitest + Pact consumer
  tests/e2e/                          # existing Playwright-style tests — extend

backend/                              # gateway + agent — Schemathesis + Pact provider
apis/data-management-api/         # DM API — Schemathesis + Pact provider + shared-schemas

.env.local.example
TESTING_DOCUMENTATION.md              # normative CI matrix
```

**Structure Decision**: Keep tests **close to each deployable**; share **OpenAPI JSON** and **pactfiles** via CI artifacts or broker; document matrix in `contracts/pact-schemathesis-playwright-pyramid.md`. For **this feature**, the normative chat Playwright path is **`frontend/tests/e2e/`** (see **tasks.md** **T015**); other layouts (`e2e/` at package root, etc.) are out of scope unless tasks are revised (**T1** alignment).

## Phase 0 — Research (`research.md`)

Includes: env canonicalization; Pact consumer/provider split per [Pact FAQ](https://docs.pact.io/faq); Schemathesis vs consumer contracts ([Schemathesis FAQ](https://schemathesis.readthedocs.io/en/stable/faq.html)); Playwright E2E scope; typed-class strategy (Zod vs codegen).

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

- **Data model**: Config entities + **typed testing artifacts** (DTO namespaces for Pact + HTTP client).
- **Contracts**: env wiring; DM OpenAPI alignment; **pact-schemathesis-playwright-pyramid.md** (layering + CI).
- **Quickstart**: local Pact, Schemathesis, Playwright entrypoints.

## Testing strategy (required) — two product lines

| Layer | Chatbot system | Data-management system |
|-------|----------------|-------------------------|
| **Pact (consumer)** | `frontend/` → gateway/agent interactions | `apps/data-management-frontend/` → DM API + optional gateway modal-jobs |
| **Pact (provider)** | Gateway + agent verify published pacts | DM API (+ gateway provider for modal-jobs if in scope) |
| **Schemathesis** | `GATEWAY_SCHEMA_URL`, `AGENT_SCHEMA_URL` | DM `openapi.json` + gateway paths used when modal-jobs flag on |
| **Typed DTOs** | Types/Zod/codegen aligned with agent routes | Types aligned with `/jobs`, `/health`, gateway proxy |
| **Playwright E2E** | Chat load, config fetch, send message (stream optional) | Dashboard scrape jobs, health banner, critical CRUD |

**CI split (spec FR-006)**: PR — Pact consumers, Vitest, optional Playwright shard against mocks or lightweight stack; **main / cron / `workflow_dispatch`** — real-stack integration + full Playwright + Schemathesis + provider verification as documented.

## Re-evaluated Constitution Check (Post-design)

- **Community benefit**: **Pass**
- **Trustworthy retrieval**: **Pass**
- **Data stewardship**: **Pass**
- **Safety & quality**: **Pass** — multi-layer automated evidence.
- **Service boundaries**: **Pass**

## Complexity Tracking

No unjustified constitution violations.

## Phase 2 (task generation)

`/speckit.tasks` breaks down Pact broker setup, provider states, Schemathesis inclusion for DM OpenAPI, Playwright projects, and typed DTO consolidation.

**Execution note (O1):** The foundational phase in **tasks.md** finishes **T008** only for **interim** `rag-api` → `types/` imports; switching to **codegen** exports and deleting duplicate hand-written shapes follows **T029** in **User Story 3** (same **T008** task ID, second slice—see **tasks.md** Phase 2 checkpoint and **T008** body).

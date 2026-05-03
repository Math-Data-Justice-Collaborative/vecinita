# Implementation Plan: OpenAPI SDK clients and standardized service URLs

**Branch**: `015-openapi-sdk-clients` | **Date**: 2026-04-24 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification and **Clarifications Session 2026-04-24** (Modal **Option B**: no HTTP(S) to Modal-assigned hostnames from **any** checked-in code; SDK-only orchestration on Modal; OpenAPI Generator clients for Gateway, Data Management, Agent).

## Summary

Deliver **three OpenAPI-driven generated client families** (Python `python-pydantic-v1`, TypeScript `typescript-node`, TypeScript `typescript-axios`) sourced from **`GATEWAY_SCHEMA_URL`**, **`DATA_MANAGEMENT_SCHEMA_URL`**, and **`AGENT_SCHEMA_URL`**, and migrate call sites so **application logic** never hand-rolls HTTP to those services. **Eliminate** deprecated Modal/model/embedding URL environment variables (**FR-005**, **SC-001**) and enforce **FR-001** / **SC-005** with CI-visible static checks against Modal host patterns. **Runtime wiring** for cross-service + DB connectivity uses **only** the approved env set (**FR-004**). **Modal**: all in-repo Modal compute access via **Modal SDK** (`.remote()`, `.spawn`, `.map`, composition)—**no** `httpx`/`requests`/`fetch`/Axios to `*.modal.run` or other Modal deployment hosts. Non-Modal tiers obtain model/embedding behavior through **Render** Gateway / Agent / Data Management HTTP using generated clients. Update **`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`**, **`docs/deployment/MODAL_DEPLOYMENT.md`**, **`.github/workflows`** (including **`docs-gh-pages.yml`** when it documents env or client regen), and **`TESTING_DOCUMENTATION.md`** so operators and contributors see one story. **`make ci`** remains merge-ready gate per constitution.

## Technical Context

**Language/Version**: Python **3.11+** (`backend/`, `apis/data-management-api/`, `modal-apps/scraper/`); TypeScript **5.x** (`frontend/`, `apps/data-management-frontend/`).  
**Primary Dependencies**: **FastAPI** (gateway + agent entrypoints under `backend/src/`); **Modal** Python SDK; **OpenAPI Generator** CLI (pinned version in `Makefile` or `package.json` script—see [research.md](./research.md)); existing **httpx** / **axios** only toward **approved non-Modal** bases (Render gateway/agent/DM). **Pydantic** v2 in app code vs **pydantic v1** in generated Python client (generator constraint—see research).  
**Storage**: **PostgreSQL** via **`DATABASE_URL`** (unchanged contract).  
**Testing**: **`pytest`**, **`vitest`**, **Schemathesis** (`GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, `AGENT_SCHEMA_URL` per `TESTING_DOCUMENTATION.md`); new checks for **SC-005** (Modal HTTP ban). **`make ci`** before merge-ready.  
**Target Platform**: **Render** web services + **Modal** serverless functions; local dev via documented env in [quickstart.md](./quickstart.md).  
**Project Type**: **Monorepo** — gateway/agent (`backend/`), data-management API (`apis/data-management-api/`), scraper Modal apps (`modal-apps/scraper/`), frontends (`frontend/`, `apps/data-management-frontend/`), shared packages (`packages/service-clients/`).  
**Performance Goals**: No stricter latency SLO than current production; client generation is **build-time** / CI, not request-path hot unless explicitly cached.  
**Constraints**: **FR-001** strict (no Modal HTTP in repo); **FR-002** generated clients only for the three HTTP APIs; **FR-004** exclusive URL env set for those connectivity concerns; constitution **service boundaries** and **contract tests**.  
**Scale/Scope**: All references to deprecated URL vars removed (**SC-001**); ≥95% hand-written Gateway/DM/Agent HTTP migrated (**SC-002**); documented regen + validate in ≤30 minutes (**SC-003**).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|--------|
| **Community benefit** | **Pass** | Reduces misconfiguration and secret leakage; keeps RAG/chat paths on governed contracts. |
| **Trustworthy retrieval** | **Pass** | No change to attribution model; stricter client contracts reduce silent drift. |
| **Data stewardship** | **Pass** | Env consolidation does not relax ingestion policies; Modal HTTP ban reduces accidental cross-tier leakage. |
| **Safety & quality** | **Pass** | Adds static + contract gates; `make ci`; Schemathesis/OpenAPI alignment preserved. |
| **Service boundaries** | **Pass** | Strengthens OpenAPI as boundary; Modal only via SDK inside Modal boundary; Render HTTP only via generated clients. |

**Post–Phase 1 re-check**: [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md) defines generator outputs and consumers; [contracts/modal-http-ban-sc005.md](./contracts/modal-http-ban-sc005.md) defines **SC-005** enforcement; [data-model.md](./data-model.md) ties **connection profile** entities to env vars and packages.

## Project Structure

### Documentation (this feature)

```text
specs/015-openapi-sdk-clients/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── openapi-codegen-layout.md
│   └── modal-http-ban-sc005.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit.tasks (not produced by /speckit.plan)
```

### Source code (primary touchpoints)

```text
backend/
  src/
    api/                         # Gateway FastAPI; OpenAPI export already central
    agent/                       # Agent FastAPI entry
    services/modal/              # invoker.py — ensure SDK-only paths; no httpx to *.modal.run
    services/llm/                # client_manager and LLM routing — remove URL env usage
    embedding_service/           # modal_embeddings and HTTP fallbacks audit
  tests/                         # Schemathesis, live tests; add SC-005 lint tests if pytest-based

apis/data-management-api/
  packages/service-clients/      # modal_invoker.py, HTTP clients — migrate to generated DM client

modal-apps/scraper/                # Modal workers — audit for httpx to Modal hosts

frontend/                        # Axios/fetch to gateway/agent — migrate to typescript-axios / node client
apps/data-management-frontend/   # Today: openapi-typescript snapshot; plan alignment with OpenAPI Generator axios stack per spec Assumptions

packages/                        # New or extended subpackages for generated clients (exact paths in contracts/)

.github/workflows/               # CI: fetch schemas, run openapi-generator, fail on drift; docs-gh-pages.yml
docs/deployment/
  RENDER_SHARED_ENV_CONTRACT.md  # Remove deprecated vars; document approved set only
  MODAL_DEPLOYMENT.md            # SDK-only narrative; token secrets vs URL endpoints
Makefile                         # Targets: codegen-verify, modal-host-lint (names TBD in tasks)

.env / .env.local.example        # Strip deprecated keys from committed examples (never commit secrets)
```

**Structure Decision**: Treat **`backend/`** as home for **gateway + agent** OpenAPI sources and Python consumers; **`apis/data-management-api/`** for DM API and its clients; **`frontend/`** and **`apps/data-management-frontend/`** for TypeScript consumers. Centralize **generated output directories** under agreed paths in [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md) (avoid sprawl in `backend/src/api`).

## Complexity Tracking

> No constitution violations requiring justification.

## Phase 0: Research

Consolidated in [research.md](./research.md) — OpenAPI Generator layout, pydantic v1 vs app pydantic v2 coexistence, TypeScript generator choice per surface, Modal HTTP ban enforcement options, and migration from ad hoc `openapi-typescript` where the spec mandates OpenAPI Generator.

## Phase 1: Design & contracts

- [data-model.md](./data-model.md) — connection profile, generated packages, forbidden env keys.  
- [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md) — generators, output dirs, CI drift checks, docs workflow hooks.  
- [contracts/modal-http-ban-sc005.md](./contracts/modal-http-ban-sc005.md) — hostname patterns, tooling (`rg`, `semgrep`, custom script), exclusions (vendor, lockfiles).  
- [quickstart.md](./quickstart.md) — env template, regen commands, smoke paths.

## Next step

Run **`/speckit.tasks`** to produce **`tasks.md`**, then implement with TDD (`/speckit-implement` or manual phases). **`make ci`** must pass before declaring merge-ready.

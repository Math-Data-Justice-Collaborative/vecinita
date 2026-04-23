# Implementation Plan: Modal function calls + API routing (DM stack & gateway/agent)

**Branch**: `008-scraper-via-dm-api` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)  
**Input**: Base spec in `specs/007-scraper-via-dm-api/spec.md`. Planning addendum: use **Modal function invocation** (`Function.from_name` + `.remote()` / `.spawn()` with `FunctionCall` polling where needed) from **`services/data-management-api/`** for **scraper**, **embedding**, and **model** paths used by **ingest** and related DM operations—**not** public `*.modal.run` HTTP entrypoints for those call paths when Modal is the target. **Contracts and integration** between the DM API and Modal-deployed apps **must have automated tests** (mocks/stubs for unit speed; optional live smoke behind flags). **Gateway** (`backend/` gateway surface) continues to call the **agent** service over HTTP; the **agent** must **only** use Modal **function** calls for Modal-backed work (**no** direct Modal web endpoints for those responsibilities). Frontends: **data-management** → DM API only; **main** `frontend/` → gateway only (per spec FR-001/FR-002).

## Summary

Shift **server-side** integration so **data-management-api** orchestrates scraper, embedding, and model work via the **Modal Python SDK** (same pattern as `backend/src/services/modal/invoker.py`: deployed apps, `from_name`, `remote`/`spawn`, env-driven app and function names). Align **gateway → agent** HTTP forwarding with a **hard policy** on the agent: when targets are Modal-hosted, **function invocation** is required (reuse `enforce_modal_function_policy_for_urls` semantics). Add **tests** at the DM API boundary (Modal adapter mocked), plus **contract-level** coverage (OpenAPI/Schemathesis where surfaces are HTTP, and typed envelope tests for RPC payloads) so regressions on routing and invocation mode are caught in CI.

## Terminology (spec ↔ plan)

- **[spec.md](./spec.md) “hosted compute platform”** — vendor-neutral label for where scraper, embedding, and model workloads execute.
- **Modal** — the concrete platform used in-repo; public **`*.modal.run`** HTTP apps are **web entrypoints**, distinct from **deployed Modal Functions** invoked via the Python SDK (`Function.from_name`, `.remote()` / `.spawn()`).
- **tasks.md** may say “Modal” where the spec says “hosted compute platform”; interpret them as the same boundary unless a task explicitly allows the **non-production HTTP fallback** ([spec.md](./spec.md) **FR-009**).

## Technical Context

**Language/Version**: Python 3.11+ for `services/data-management-api/`, gateway, and agent (`backend/`); TypeScript for `frontend/` and `apps/data-management-frontend/`.  
**Primary Dependencies**: FastAPI, Pydantic v2, **modal** SDK (where function invocation runs), httpx, existing `service_clients` / `shared-schemas` in DM API; gateway `src/services/modal/invoker.py` as reference implementation.  
**Storage**: Unchanged for this plan slice (Postgres / gateway persistence as today); focus is transport and invocation.  
**Testing**: **pytest** + `pytest-asyncio` in DM API packages; **monkeypatch** / fakes for `modal.Function`, `FunctionCall`; existing **Schemathesis** norms for HTTP OpenAPI (`TESTING_DOCUMENTATION.md`, `backend/schemathesis.toml`); optional **live** Modal smoke gated on tokens (non-PR).  
**Target Platform**: Linux CI, Docker Compose, Render.  
**Project Type**: Monorepo multi-service (DM API deployable, gateway+agent in `backend/`).  
**Performance Goals**: Preserve current timeouts; Modal `spawn` + poll paths document max wait for job/scrape status.  
**Constraints**: No secrets in repo; `MODAL_FUNCTION_INVOCATION` / token policy consistent across gateway, agent, and DM API; no browser calls to Modal HTTP for DM-owned flows (spec SC-001/SC-003).  
**Scale/Scope**: DM API client refactor (HTTP → Modal functions for configured paths), agent policy enforcement, gateway unchanged except docs/tests if needed, frontend base URL audits, contract test files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Community benefit**: **Pass** — safer ingestion boundaries support trustworthy community RAG operations.
- **Trustworthy retrieval**: **Pass** — no change to citation semantics; ingestion reliability improves.
- **Data stewardship**: **Pass** — auditability FR-006 preserved via structured logs + correlation IDs across DM API and workers.
- **Safety & quality**: **Pass** — explicit tests for Modal integration and OpenAPI contracts (see `../../.specify/memory/constitution.md` safety & quality).
- **Service boundaries**: **Pass** — DM API owns DM→Modal orchestration; gateway owns public edge; agent is internal to gateway for chat/RAG paths; contracts documented.

## Project Structure

### Documentation (this feature)

```text
specs/007-scraper-via-dm-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dm-api-modal-functions.md
│   ├── gateway-agent-modal-policy.md
│   └── testing-contracts-matrix.md
└── tasks.md                 # /speckit.tasks (not produced by this command)
```

### Source code (implementation targets)

```text
services/data-management-api/
  packages/service-clients/          # Modal invoker + HTTP clients (landed: modal_invoker.py)
  apps/backend/                       # FastAPI routers (submodule may be sparse—wire ScraperClient here when present)
  packages/shared-config/            # MODAL_* settings fields (landed)
  tests/                              # unit + integration tests with mocked modal

services/scraper/                     # Modal app definitions (RPC entrypoints already: modal_job_*)
services/embedding-modal/
services/model-modal/

backend/
  src/services/modal/invoker.py      # canonical patterns; consider shared extraction if duplication risk
  src/service_endpoints.py           # SCRAPER_ENDPOINT / policy alignment notes
  src/agent/main.py                  # enforce_modal_function_policy_for_urls (already)
  tests/                             # extend policy + forwarding tests

apps/data-management-frontend/       # VITE_* → DM API base only
frontend/                            # gateway base only

specs/007-scraper-via-dm-api/contracts/
```

**Structure Decision**: Implement Modal invocation in **DM API** as a small **adapter module** (either vendored copy of invoker patterns with DM-specific env names, or a **shared internal package** if the repo already has a path—prefer **one canonical module** in `backend/` imported as a path dependency **only if** packaging allows without cycles; otherwise duplicate minimal `from_name`/`remote` wrapper in DM API with tests). **Do not** import DM API from gateway (wrong direction).

## Phase 0 — Research (`research.md`)

Resolved: Modal SDK vs HTTP for DM paths; test layering; env var naming; duplication vs shared invoker helper.

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

See generated artifacts for entities, RPC envelopes, and operator env quickstart.

## Testing strategy (required)

| Area | Unit / fast | Contract / schema | Notes |
|------|----------------|---------------------|--------|
| **DM API ↔ Modal** | Mock `modal.Function.from_name`, assert `.remote` / `.spawn` args | Typed fixture tests for scraper RPC envelopes (`_rpc_ok` / `_rpc_err` shapes) | Mirror `backend/tests` patterns where scraper Modal job submit is tested |
| **DM API HTTP surface** | Router tests | Schemathesis on DM `openapi.json` for public routes touched | Per `TESTING_DOCUMENTATION.md` |
| **Gateway → agent** | Existing router tests | Schemathesis gateway + agent OpenAPI | Ensure `/ask` proxy unchanged |
| **Agent Modal policy** | Tests for `enforce_modal_function_policy_for_urls` | N/A | Agent must not run with `*.modal.run` URLs unless function invocation on |

**CI**: PR runs fast mocks + Schemathesis where already wired; live Modal optional (`workflow_dispatch` / cron) with secrets.

**Primary-flow release matrix (SC-001 / SC-002):** Release sign-off for “**100%** of **sampled** primary flows” depends on an agreed **row list** (automated tests, optional E2E, manual checklist lines). **Ownership:** define, publish, and link that matrix in **`specs/007-scraper-via-dm-api/quickstart.md`** (canonical during this feature) and mirror or link from **`TESTING_DOCUMENTATION.md`** as CI matures—see **tasks.md** **T034**–**T036**.

## Re-evaluated Constitution Check (Post-design)

- **Community benefit**: **Pass**
- **Trustworthy retrieval**: **Pass**
- **Data stewardship**: **Pass**
- **Safety & quality**: **Pass** — contracts + tests explicit in `contracts/testing-contracts-matrix.md`
- **Service boundaries**: **Pass**

## Complexity Tracking

No unjustified constitution violations.

## Phase 2 (task generation)

Use `/speckit.tasks` to break down: DM API Modal adapter, replace direct Modal HTTP in service-clients, agent/gateway policy alignment, frontend env audits, CI targets, documentation updates for `services/data-management-api/docs/architecture.md` (currently describes direct frontend → Modal; must match spec).

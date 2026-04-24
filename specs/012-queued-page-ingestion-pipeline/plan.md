# Implementation Plan: Queued page ingestion pipeline

**Branch**: `014-queued-page-ingestion-pipeline` | **Date**: 2026-04-24 | **Spec**: [spec.md](./spec.md)  
**Tasks (execution)**: [tasks.md](./tasks.md) — implementation is tracked in **task phases 1–6** below; this plan’s **Phase 0–1** are **design/research artifacts** only (no numbering collision).  
**Input**: Feature specification plus clarifications (gateway canonical contract, single frontend base URL, gateway/co-released workers only → Modal for pipeline compute, stable gateway error JSON, required correlation IDs). User planning notes: **Modal best practices**, **TDD**, **Render deployment best practices** — Modal specifics trace to [research.md](./research.md) **Decision 1–2** (invocation, timeouts, secrets) and Render gates to **Decision 3**.

## Summary

Implement an **end-to-end, queue-driven page ingestion pipeline**: each in-scope page is **enqueued** as a durable job; **scrape → chunk → LLM enrich → embed → persist** runs with **Modal** for heavy/remote steps and **Render-hosted gateway (+ co-released workers)** as the only browser-facing HTTP plane and the only component family that holds credentials to call Modal for this pipeline (**FR-013**). **OpenAPI** for the gateway remains the **contract source of truth** (**FR-011**); **Pact** (checked-in files per `TESTING_DOCUMENTATION.md`) and **Schemathesis** guard regressions. Extend or align **internal gateway pipeline ingest** (`/api/v1/internal/scraper-pipeline/*`) and **Modal scraper workers** so stages are **ordered**, **idempotent where required**, **observable** (structured logs + **FR-015** correlation ID end-to-end), and **mapped to stable gateway errors** for any browser-visible routes (**FR-014**). **TDD**: add/extend failing tests for contracts and pipeline transitions **before** production implementation in each slice. **Render**: keep **`render.yaml`** + env-group discipline (`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`), **`autoDeployTrigger: checksPass`**, health checks, and documented **`DATABASE_URL`** / **`SCRAPER_GATEWAY_BASE_URL`** alignment for Modal→gateway persistence.

## Technical Context

**Language/Version**: Python **3.11+** (`backend/`, `services/scraper/`); TypeScript for **`frontend/`** and **`apps/data-management-frontend/`** Pact consumers.  
**Primary Dependencies**: **FastAPI** (gateway), **Modal** SDK (`modal.Function.from_name`, `.remote()` / `.spawn()`), **Pydantic**, **psycopg2** (gateway-side pipeline persist), **httpx** / worker HTTP to gateway; scraper stack (**Crawl4AI**, **Docling**, etc.) per existing `services/scraper`.  
**Storage**: **PostgreSQL** via **`DATABASE_URL`** on Render for chunks, embeddings, job/crawl metadata; Modal workers may use **gateway HTTP pipeline** (`SCRAPER_GATEWAY_BASE_URL` + `X-Scraper-Pipeline-Ingest-Token`) instead of holding DSN on Modal when configured.  
**Testing**: **`pytest`** (unit → integration; contract suites under `backend/tests/pact/`, `backend/tests/test_api/`); **`npm run test:pact`** for frontends; **Schemathesis** (`backend/schemathesis.toml`, `make test-schemathesis`); **`make ci`** merge gate. **Pact / Schemathesis matrix** (merge-blocking vs optional jobs): repo root **`TESTING_DOCUMENTATION.md`**. **TDD** discipline: red test for each new behavior (status transition, HTTP shape, error envelope field), then minimal green implementation.  
**Target Platform**: **Render** web services + workers (from `render.yaml`); **Modal** Linux containers for scraper/pipeline functions. **Blueprint spot-check (documentation accuracy):** service **`vecinita-gateway`** in `render.yaml` uses **`autoDeployTrigger: checksPass`** and **`healthCheckPath: /health`** as of this plan date—re-verify after editing the blueprint. **Last reverified (no blueprint edits):** 2026-04-24 — `vecinita-gateway` still has **`healthCheckPath: /health`** and **`autoDeployTrigger: checksPass`** (see `render.yaml`).  
**Project Type**: **Monorepo** — `backend/` (gateway + internal routes), `services/scraper/` (Modal app + workers), `frontend/` / DM SPA as consumers.  
**Performance Goals**: Bounded per-page wall time via existing crawl timeouts + explicit queue concurrency caps (plan tasks pick numbers); Modal **`timeout`** / **`max_containers`** style limits per Modal docs patterns in [research.md](./research.md).  
**Constraints**: **Constitution** — robots/licensing, no deceptive scraping; **FR-009**; **no Modal secrets in browser**; **single public gateway base URL** for FR-011 consumers (**FR-012**).  
**Scale/Scope**: Pipeline correctness and contract hardening first; horizontal scale via Modal autoscale + queue depth metrics (deferred tuning in tasks if needed).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|--------|
| **Community benefit** | **Pass** | Corpus growth for public-good RAG; no expansion of paywall circumvention. |
| **Trustworthy retrieval** | **Pass** | FR-007 / traceability: chunk ↔ page URL ↔ job id; enrichment must not erase source linkage. |
| **Data stewardship** | **Pass** | FR-009; audit FR-008; correlation IDs FR-015 for operator join-up. |
| **Safety & quality** | **Pass** | TDD + Pact/Schemathesis + `make ci`; stable error contract FR-014. |
| **Service boundaries** | **Pass** | Modal only from gateway + co-released workers FR-013; OpenAPI canonical FR-011. |

**Post–Phase 1 re-check**: [contracts/gateway-ingestion-http-surface.md](./contracts/gateway-ingestion-http-surface.md) and [contracts/render-modal-pipeline-wiring.md](./contracts/render-modal-pipeline-wiring.md) document HTTP and env boundaries; [data-model.md](./data-model.md) defines states and idempotency expectations.

## Project Structure

### Documentation (this feature)

```text
specs/012-queued-page-ingestion-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── gateway-ingestion-http-surface.md
│   └── render-modal-pipeline-wiring.md
└── tasks.md             # /speckit.tasks — post-analyze remediation tasks **T035–T040** cover FR-002/FR-004 edges, **A1** persistence lock, FR-012 test, dedup
```

### Source code (primary touchpoints)

```text
backend/
  src/api/
    router_modal_jobs.py           # Modal job submit/status; error + correlation ID patterns
    router_scraper_pipeline_ingest.py  # Internal pipeline ingest from Modal workers
    main.py                        # Router inclusion, middleware if needed for X-Request-Id
  src/services/modal/
    invoker.py                     # Modal function handles; timeouts/retries patterns
  src/services/ingestion/
    modal_scraper_pipeline_persist.py  # Postgres writes for pipeline stages
  tests/
    test_api/test_router_scraper_pipeline_ingest.py
    pact/                          # Provider verification for gateway consumers

services/scraper/
  src/vecinita_scraper/
    workers/                       # Queue drain, chunk/embed steps, gateway_http persistence
    persistence/gateway_http.py    # POST pipeline stages to Render gateway
  tests/                           # TDD: unit/integration for stage ordering & payloads

frontend/                          # Pact consumer for gateway (single base URL)
apps/data-management-frontend/     # DM Pact remains DM API–scoped per TESTING_DOCUMENTATION

render.yaml                        # Render best practices: health checks, checksPass, env sync
docs/deployment/
  RENDER_SHARED_ENV_CONTRACT.md    # Env naming for gateway ↔ Modal
  MODAL_DEPLOYMENT.md              # Modal apps, functions, gateway integration
```

**Structure Decision**: Implement pipeline and contracts across **`backend/`** + **`services/scraper/`**; extend **Pact/OpenAPI** artifacts for **gateway** surfaces used by ingestion/chat; **do not** introduce browser calls to Modal.

**Consumer split (FR-012 vs DM):** Main **`frontend/`** Pact + runtime config target the **gateway** origin for chat and **FR-011** ingestion-related HTTP. **`apps/data-management-frontend/`** continues to target the **data-management API** base URL for DM/scraper dashboard flows per **`TESTING_DOCUMENTATION.md`**—do not route DM SPA scrape CRUD through the gateway as a default.

**Net-new modules (tasks; not yet in repo):** [tasks.md](./tasks.md) adds **`backend/src/services/ingestion/pipeline_stage.py`** (**T007**) and **`services/scraper/src/vecinita_scraper/workers/chunking_defaults.py`** (**T037**) plus new tests named there—the tree above lists **integration** targets only; treat these as explicit additions when implementing.

## Complexity Tracking

> No constitution violations requiring justification.

## Documentation drift ownership (**checklist CHK020**)

If a **plan** path, **tasks** path, or **contract** link disagrees with the repo after refactors: **(1)** update **`plan.md` / `tasks.md` first** so they remain the authority, **(2)** adjust `contracts/` and **`spec.md`** only when user-visible behavior or FR text changes, **(3)** run **`specs/012-queued-page-ingestion-pipeline/checklists/repo-alignment.md`** again after edits.

## Phase 0: Research

Consolidated in [research.md](./research.md) — Modal (function decorators, secrets, timeouts, structured logging), Render (blueprint, deploy gates, rollback), and **TDD layering** (unit vs contract vs live).

## Phase 1: Design & contracts

- [data-model.md](./data-model.md) — page job lifecycle, chunk/embedding linkage, pipeline stage rows.  
- [contracts/gateway-ingestion-http-surface.md](./contracts/gateway-ingestion-http-surface.md) — OpenAPI + error envelope + correlation ID (**FR-011–FR-015**).  
- [contracts/render-modal-pipeline-wiring.md](./contracts/render-modal-pipeline-wiring.md) — env vars, URLs, token headers, who calls whom.  
- [quickstart.md](./quickstart.md) — local TDD loop, Pact verify, Modal smoke, Render env checklist.

All of the above paths are relative to **`specs/012-queued-page-ingestion-pipeline/`**; together with [tasks.md](./tasks.md) they form the complete artifact set for this feature before code changes.

## Next step

Follow [tasks.md](./tasks.md) with **TDD**; invoke **`/speckit-implement`** or execute phases manually. **`/speckit.tasks`** has already produced `tasks.md` for this feature.

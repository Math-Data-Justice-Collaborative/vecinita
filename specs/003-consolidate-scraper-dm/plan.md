# Implementation Plan: Consolidate scraper, remote-only DM API integration, and gateway job stability

**Branch**: `003-consolidate-scraper-dm` | **Date**: 2026-04-19 | **Spec**:
[spec.md](./spec.md)

**Input**: Feature specification from `specs/003-consolidate-scraper-dm/spec.md`, plus planning
directive: include **refactoring plans**, **testing for consistency between old and new versions**,
and work that **targets the Schemathesis errors and warnings** (live gateway: `5xx` on Modal scraper
job routes, `504` on ask, missing test data `404`s, schema validation mismatch, TraceCov/coverage
threshold shortfalls).

**Note**: This file is produced by `/speckit.plan`. Execution follows
`.specify/templates/plan-template.md`.

## Summary

Deliver **three** intertwined outcomes: (1) **Operational reliability** — hosted scraping job APIs
and related persistence paths must not return undocumented `5xx` when dependencies are healthy, and
must not leak internal DNS names to clients (per **FR-001** / **FR-002**). (2) **Repository
simplification** — remove `apis/data-management-api` git **submodules** for
`scraper-service`, `embedding-service`, and `model-service` in favor of **remote HTTP integration
only** (clarification **B**), with a **single authoritative** scraper source tree under
`services/scraper`. (3) **Contract-test quality** — drive live **Schemathesis** (and related hooks)
toward **zero server-error class failures**, reduce **404** “missing test data” noise via realistic
fixtures, and align **OpenAPI** constraints with runtime validation so fuzzing/coverage gates are
meaningful.

Parity testing: before removing embedded trees, capture **golden request/response** (or status +
stable JSON subset) for critical DM API → scraper/embedding/model flows; replay against **new**
remote-backed implementation until diffs are empty or explicitly accepted.

## Technical Context

**Language/Version**: Python 3.11 (gateway, scraper service, data-management-api backend).  
**Primary Dependencies**: FastAPI, HTTP clients (`httpx` / existing patterns), Pydantic; Modal for
hosted jobs; Postgres for job registry / scrape history.  
**Storage**: PostgreSQL (`DATABASE_URL` on Render gateway; **external** DB URL for Modal workers
where internal hostnames do not resolve — see
[RENDER_SHARED_ENV_CONTRACT.md](../../docs/deployment/RENDER_SHARED_ENV_CONTRACT.md)).  
**Testing**: `pytest` (gateway `backend/tests`, scraper `services/scraper`); **`make
test-schemathesis-cli`** / `backend/scripts/run_schemathesis_live.sh`; hooks in
`backend/tests/schemathesis_hooks.py`; `make ci` before merge.  
**Target Platform**: Render (gateway, DM API, scraper image); Modal workers; local Docker for parity.  
**Project Type**: Monorepo — `backend/` (gateway), `services/scraper/` (canonical scraper),
`apis/data-management-api/apps/backend/` (DM API; currently **submodules** per
[.gitmodules](../../apis/data-management-api/.gitmodules)).  
**Performance Goals**: Non-streaming **ask** within gateway timeout budget for representative
questions (**FR-007** / **SC-005**); Modal job control plane responsive enough for contract phases
(`request-timeout` in `backend/schemathesis.toml` is 180s baseline).  
**Constraints**: No breaking changes to stable **gateway** `/api/v1/*` contracts without migration;
**FR-002** — production responses must not expose raw infra identifiers; remote-only **B** — no
in-process imports of vendored scraper/embedding/model **implementations** inside DM API.  
**Scale/Scope**: Three submodules removed; DM API gains explicit service URLs + auth; gateway Modal
job persistence split documented (`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`); Schemathesis operations
previously failing + seven “schema mismatch” ops + four “missing data” ops addressed per
[research.md](./research.md).

## Constitution Check

*GATE: Pre–Phase 0 and re-check post–Phase 1 design. Source: `.specify/memory/constitution.md`.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Community benefit | **Pass** | Reliable ingestion and ask paths improve access to public corpus. |
| Trustworthy retrieval | **Pass** | Ask/scrape contracts unchanged in intent; attribution paths preserved. |
| Data stewardship | **Pass** | Scraping jobs remain auditable (job IDs, correlation IDs per **FR-006**). |
| Safety & quality | **Pass** | Adds parity + contract gates; OpenAPI/runtime alignment reduces false negatives. |
| Service boundaries | **Pass** | Clarification **B** strengthens explicit HTTP contracts between DM API and sibling services; documented in [contracts/](./contracts/). |

**Re-evaluation (post-design)**: [contracts/dm-api-remote-service-integration.md](./contracts/dm-api-remote-service-integration.md) and [contracts/gateway-scraper-jobs-stability.md](./contracts/gateway-scraper-jobs-stability.md) bound cross-service behavior; [data-model.md](./data-model.md) names integration entities without collapsing deployables.

## Project Structure

### Documentation (this feature)

```text
specs/003-consolidate-scraper-dm/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
└── tasks.md             # /speckit.tasks (not created here)
```

### Source Code (repository root)

```text
backend/
├── src/api/                    # Gateway routes incl. router_modal_jobs.py
├── tests/schemathesis_hooks.py # Live hooks, job IDs, coverage gate
├── schemathesis.toml
└── scripts/run_schemathesis_live.sh

services/scraper/               # Canonical scraper package + Dockerfile (Render)
├── src/vecinita_scraper/

apis/data-management-api/
├── .gitmodules                 # Submodule definitions to remove (scraper, embedding, model)
├── apps/backend/
│   ├── scraper-service/        # Submodule path → replace with HTTP client to services/scraper deployable
│   ├── embedding-service/      # Submodule path → HTTP client to embedding deployable
│   └── model-service/          # Submodule path → HTTP client to model deployable
│   └── (DM API FastAPI app)    # Consumers refactored to remote calls

docs/deployment/RENDER_SHARED_ENV_CONTRACT.md   # Gateway/Modal DB split (persist-via-gateway)
```

**Structure Decision**: Treat **`services/scraper`** as the **only** scraper **source** tree.
**Data-management-api** stops embedding `vecinita_scraper` (and sibling stacks) as submodules; it
uses **configured base URLs** + documented contracts ([contracts/](./contracts/)). Gateway changes
stay minimal and env-driven per existing deployment contract docs.

## Complexity Tracking

> No constitution violations requiring justification. Remote-only integration adds **operational**
> dependency on service discovery and auth; rejected alternative was **monorepo package imports**,
> superseded by product clarification **B**.

## Phase 0 — Research (`research.md`)

Resolved in [research.md](./research.md): Modal vs Render **Postgres hostname** split, submodule
removal order, **parity** methodology (old vs new), and Schemathesis **errors vs warnings**
remediation strategy (OpenAPI alignment, hook fixtures, optional coverage thresholds).

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

- [data-model.md](./data-model.md): Logical entities for jobs, registry, remote service config, safe errors.  
- [contracts/dm-api-remote-service-integration.md](./contracts/dm-api-remote-service-integration.md):
  Env vars, timeouts, auth expectations, failure mapping.  
- [contracts/gateway-scraper-jobs-stability.md](./contracts/gateway-scraper-jobs-stability.md):
  Status-code expectations and persistence boundary for `/api/v1/modal-jobs/scraper*`.  
- [quickstart.md](./quickstart.md): Parity smoke, Schemathesis live run, env checklist.

## Refactoring plan (high level)

| Phase | Goal | Key actions |
|-------|------|-------------|
| **R0 — Baseline** | Measure and lock behavior | Capture Schemathesis JUnit + coverage HTML; snapshot DM API → submodule call paths; document current env on staging. |
| **R1 — Errors (`5xx`)** | Job APIs healthy when deps healthy | Verify `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` + Modal `MODAL_DATABASE_URL` (external) per deployment doc; add safe error mapping (**FR-002**); gateway tests in `backend/tests/test_api/test_router_modal_jobs.py`. |
| **R2 — Remote clients (DM API)** | Implement clarification **B** | Introduce HTTP clients + config (`SCRAPER_SERVICE_BASE_URL`, `EMBEDDING_SERVICE_BASE_URL`, `MODEL_SERVICE_BASE_URL`, auth headers); route calls through adapters; keep behavior flags for staged rollout if needed. |
| **R3 — Parity** | Old vs new consistency | Automated or scripted comparison: same inputs → compare status codes + normalized JSON bodies (ignore volatile fields); run in CI or nightly against staging. |
| **R4 — Remove submodules** | Repo simplification | Delete submodule entries from `.gitmodules`, remove `apps/backend/{scraper,embedding,model}-service` trees from DM API workspace; update CI, Docker, and contributor docs; **SC-003** binary check. |
| **R5 — Warnings & coverage** | Schemathesis quality | Supply **realistic** `gateway_job_id`, document IDs, scrape job IDs via hooks/env; tighten or loosen OpenAPI where runtime is stricter; address `POST /api/v1/scrape/reindex` / coverage gaps per team policy. |
| **R6 — Ask `504`** | P3 latency | Tune gateway/agent timeouts or async guidance; may be parallel track to R1–R4. |

## Testing strategy (consistency + gates)

1. **Unit / integration**: Gateway modal job router; DM API client adapters (mock remote servers).  
2. **Parity (old vs new)**: Before submodule deletion, run side-by-side or sequential diff on a fixed
   corpus of HTTP calls (stored in repo as **cassettes** or minimal JSON fixtures); after switch,
   same suite must match within allowed tolerances (documented deltas only).  
3. **Contract live**: `make test-schemathesis-cli` — target **zero** `not_a_server_error` on
   `/api/v1/modal-jobs/scraper*`; reduce 404 warnings via bootstrap data; align schema for the seven
   mismatch operations.  
4. **Regression**: `make ci` unchanged as merge gate.

## Execution order (recommended)

1. Read [research.md](./research.md) and [RENDER_SHARED_ENV_CONTRACT.md](../../docs/deployment/RENDER_SHARED_ENV_CONTRACT.md).  
2. Fix **R1** env + error surfacing; re-run live Schemathesis for scraper job cluster.  
3. Implement **R2** behind config; run **R3** parity.  
4. Execute **R4** submodule removal + doc updates.  
5. **R5** Schemathesis warnings and TraceCov thresholds.  
6. **R6** ask timeout as capacity allows.

## Stop / handoff

- **Branch**: `003-consolidate-scraper-dm`  
- **Plan path**: `specs/003-consolidate-scraper-dm/plan.md`  
- **Artifacts**: [research.md](./research.md), [data-model.md](./data-model.md),
  [quickstart.md](./quickstart.md), [contracts/dm-api-remote-service-integration.md](./contracts/dm-api-remote-service-integration.md),
  [contracts/gateway-scraper-jobs-stability.md](./contracts/gateway-scraper-jobs-stability.md)  
- **Next command**: Execute [tasks.md](./tasks.md) (**T001** onward), or run `/speckit.implement` if using Spec Kit automation. (`tasks.md` is already generated for this feature.)

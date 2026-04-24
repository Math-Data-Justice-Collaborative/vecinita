# Implementation Plan: Modal scraper gateway persistence — troubleshoot, harden, test

**Branch**: `011-modal-scraper-gateway-env` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)  
**Input**: [spec.md](./spec.md). Planning addendum: **troubleshoot** production `ConfigError` on Modal workers, **debug** misleading stack traces (double failure during exception handling), and **add testing** so misconfiguration and regression are caught in CI before deploy.

## Summary

Modal cloud workers enforce **no direct Postgres** unless gateway HTTP persistence (`SCRAPER_GATEWAY_BASE_URL` + first segment of `SCRAPER_API_KEYS`) or the documented escape hatch is set (`services/scraper/src/vecinita_scraper/core/db.py`). Production failures occur when Modal secrets omit or mismatch the gateway pair. A **secondary bug** masks the original error: several workers call `get_db()` again inside a generic `except` to mark the job failed; when the first failure is `ConfigError` from `get_db()`, the handler raises the same `ConfigError` again (**chained trace** in Modal logs).

**Technical approach**: (1) Confirm and document the env matrix vs `get_db()` behavior; (2) fix worker exception paths so **configuration errors** do not re-enter `get_db()` for status updates (log + re-raise, or skip DB update when no persistence client was obtained); (3) extend **pytest** coverage for partial configs (base URL without keys, keys without URL, empty first segment), escape hatch, and **worker-level** unit tests that simulate the exception handler with a mocked `get_db` / injected `ConfigError`; (4) optionally align **Render env contract** tests if new keys or validation messages are added; (5) keep operator guidance pointing at `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`.

## Terminology (spec ↔ plan)

- **Gateway HTTP pipeline persistence** — `GatewayHttpPipelinePersistence` (httpx to gateway `/api/v1/internal/scraper-pipeline/*` with `X-Scraper-Pipeline-Ingest-Token`).
- **Modal cloud** — `get_db()` treats runtime as Modal remote via `modal.is_local()` / `MODAL_IS_REMOTE` / `MODAL_TASK_ID` (`_modal_function_running_in_cloud()`).

## Technical Context

**Language/Version**: Python 3.11+ (`services/scraper/`, gateway `backend/` for ingest routes).  
**Primary Dependencies**: FastAPI (gateway ingest), Pydantic, httpx, psycopg2 (Postgres path), Modal SDK (worker packaging), pytest.  
**Storage**: Postgres on Render (gateway / DM API); Modal workers avoid DSN when HTTP pipeline is configured.  
**Testing**: `pytest` in `services/scraper/tests/` (unit today: `test_get_db_modal_gateway.py`); extend same package; follow repo `TESTING_DOCUMENTATION.md` / `make ci` for scraper package gates.  
**Target Platform**: Linux CI, Modal containers, Render.  
**Project Type**: Monorepo — scraper package + gateway internal HTTP API.  
**Performance Goals**: Unchanged; failure-path fix must not add latency on success path.  
**Constraints**: No secrets in repo; do not weaken default “no direct Postgres from Modal cloud” without explicit bypass env; preserve contract doc as SSOT for operators.  
**Scale/Scope**: Small, localized changes in `vecinita_scraper` workers + `db.py` tests; possible tiny gateway test only if ingest contract assertions are added.

**FR-004 / FR-005 traceability**: Gateway job submit (`job_id` injection) and multi-segment pipeline ingest auth are **already regression-tested** in `backend/tests/test_api/test_router_modal_jobs.py` and `backend/tests/test_api/test_router_scraper_pipeline_ingest.py`. Feature 009 **verifies** they remain green via `make ci` and doc cross-links (`tasks.md` T001, T014); new gateway code is out of scope unless a gap appears.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Community benefit**: **Pass** — reliable ingestion supports community RAG freshness.
- **Trustworthy retrieval**: **Pass** — no change to citation; fewer silent failures.
- **Data stewardship**: **Pass** — clearer failures support audit and operator correction; job status best-effort on true persistence errors without masking config policy.
- **Safety & quality**: **Pass** — automated tests for policy matrix and worker failure handling; `make ci` before merge.
- **Service boundaries**: **Pass** — persistence remains gateway-owned HTTP or approved DSN modes per contract; no new cross-service coupling beyond documented internal routes.

## Project Structure

### Documentation (this feature)

```text
specs/009-modal-scraper-gateway-env/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── modal-get-db-persistence-matrix.md
│   └── modal-worker-failure-handling.md
└── tasks.md                 # /speckit.tasks (not produced by this command)
```

### Source code (implementation targets)

```text
services/scraper/src/vecinita_scraper/
├── core/db.py                         # get_db(), gateway vs Postgres policy
├── persistence/gateway_http.py        # HTTP client (unchanged unless timeout/errors refined)
└── workers/
    ├── scraper.py                     # except path calls get_db() — fix
    ├── processor.py                   # same pattern
    ├── chunker.py                     # same pattern
    └── embedder.py                    # get_db() once at batch start; document if ConfigError surfaces differently

services/scraper/tests/
├── unit/test_get_db_modal_gateway.py  # extend matrix cases
└── unit/test_worker_failure_paths.py  # new: handler does not mask ConfigError (recommended)

docs/deployment/RENDER_SHARED_ENV_CONTRACT.md   # align wording if behavior/tests clarify checklist

backend/src/api/router_scraper_pipeline_ingest.py  # reference only for contracts; tests optional if gateway already covered
```

**Structure Decision**: Implement in **`services/scraper`** first (policy + workers + tests). Prefer a **small shared helper** (e.g. in `core/db.py` or `workers/_persistence.py`) for “update job failed if we have a db handle” to avoid four copy-paste divergences, only if it keeps diffs readable.

## Phase 0 — Research (`research.md`)

Resolved: root cause of double traceback; partial-env test gaps; where to centralize safe failure updates.

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

See generated artifacts for configuration state machine, persistence matrix, and operator quickstart.

## Testing strategy (required)

| Area | Unit / fast | Contract / integration | Notes |
|------|-------------|-------------------------|--------|
| **`get_db()` policy** | Extend `test_get_db_modal_gateway.py` for partial env, whitespace, multi-key first segment | N/A | Monkeypatch `_modal_function_running_in_cloud` |
| **Worker exception paths** | New tests: simulate `run_*_job` raising after DB obtained vs `ConfigError` on first `get_db()` | Optional: httpx mock against gateway | Assert **single** `ConfigError` / no chained handler failure |
| **Gateway ingest** | Existing gateway tests if present | Schemathesis only if feature touches OpenAPI | Out of scope unless ingest response shapes change |

**CI**: `make ci` from repo root before declaring merge-ready.

## Re-evaluated Constitution Check (Post-design)

- **Community benefit**: **Pass**
- **Trustworthy retrieval**: **Pass**
- **Data stewardship**: **Pass**
- **Safety & quality**: **Pass** — matrix + failure-path contracts in `contracts/`
- **Service boundaries**: **Pass**

## Complexity Tracking

No unjustified constitution violations.

## Phase 2 (task generation)

Use `/speckit.tasks` to break down: worker exception handling refactor, `get_db` test expansion, doc/checklist tweaks, CI verification.

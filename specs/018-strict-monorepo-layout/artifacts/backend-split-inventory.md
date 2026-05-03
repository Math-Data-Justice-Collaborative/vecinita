# Backend split inventory (gateway vs agent vs shared)

**Feature**: [spec.md](../spec.md) · **Tasks**: [tasks.md](../tasks.md) **T015**  
**Path map**: feeds **PM-007** (`apis/agent/`) and **PM-008** (`apis/gateway/`) before **T016** physical split.

## Scope and method

- **In scope**: `backend/src/` Python packages and top-level modules that participate in the two deployed FastAPI apps:
  - **Agent**: `uvicorn src.agent.main:app` (see `backend/Dockerfile` `CMD`).
  - **Gateway**: `uvicorn src.api.main:app` via `backend/scripts/start_gateway_render.sh` (see `backend/Dockerfile.gateway`).
- **Method (Apr 2026)**: Static review of `backend/src/**` layout, Dockerfile entrypoints, and representative `from src.*` import edges between `api`, `agent`, and `services`. Not a full dependency graph; **T016** should re-verify with `rg`/import-linter after moves.
- **Out of scope for this file**: `backend/tests/` split plan (covered implicitly by **T016**); Modal/scraper trees outside `backend/src/`.

## Executive summary

| Category | Role in split |
|----------|----------------|
| **Gateway-only** | Moves with **`apis/gateway/`**; must not import agent runtime graph. |
| **Agent-only** | Moves with **`apis/agent/`**; hosts LangGraph / ask / tools. |
| **Shared** | Either **extract** to `packages/python/db/` / small shared libs per **Phase 5**, or **duplicate temporarily** only if **T016** explicitly documents removal (per constitution + `contracts/monorepo-layout-boundary.md`). |

**Highest coupling before T016**

1. **`src.api.openapi_examples`** re-exports symbols from **`src.agent.openapi_examples`** — gateway OpenAPI depends on agent module for examples/matchers.
2. **`src.services.agent`** is a **shim** (`server.py` re-exports `src.agent.main`) and **`services/agent/tools/db_search.py`** wraps **`src.agent.tools.db_search`** — duplicate surface; consolidate into **`apis/agent`** only.
3. **`src.config`** and **`src.service_endpoints`** are imported by **both** apps — treat as **shared configuration** until split, then decide single owner + thin re-exports if needed.

---

## Gateway-only (`apis/gateway/` target)

| Path / unit | Rationale |
|-------------|-----------|
| `src/api/` (package) | FastAPI gateway app (`src.api.main:app`), routers (`router_*`), middleware, gateway-specific Pydantic models under `api/models/`, `job_manager.py`. |
| `src/api/openapi_examples.py` | Gateway OpenAPI helpers; **currently imports `src.agent.openapi_examples`** → decouple or move shared examples to neutral package during **T016**. |

---

## Agent-only (`apis/agent/` target)

| Path / unit | Rationale |
|-------------|-----------|
| `src/agent/` (package) | Canonical agent FastAPI app (`src.agent.main:app`), LangGraph wiring, `routers/`, `tools/`, `http_api_schemas.py`, `guardrails_config.py`, `openapi_examples.py`, static/agent assets. |
| `src/services/llm/` | **LocalLLMClientManager** and helpers consumed from **`src.agent.main`** only (no `src.api` imports observed). |

---

## Shared (cross-cutting — decide in T016 / later extraction)

| Path / unit | Used by | Notes |
|-------------|---------|--------|
| `src/config.py` | Agent, gateway, tools, tests | Central env + URL normalization; likely **one shared module** or split into `shared_config` + tiny per-app overrides. |
| `src/service_endpoints.py` | Gateway (`api/*`), lazy use in `agent.main` | Normalized internal service URLs; keep single implementation or move to `packages/` if both images need it. |
| `src/env_deprecation.py` | Via `config` / package init | Alias warnings; stays with whichever package owns `config` or moves to shared. |
| `src/services/modal/` (`invoker.py`, `job_registry.py`) | Gateway routers + **agent** startup policy (`enforce_modal_function_policy_for_urls`) | **True shared** Modal HTTP/SDK guard + job registry; extract or duplicate only with a **single PR removal** follow-up. |
| `src/services/corpus/corpus_projection_service.py` | `api/router_documents.py` | Gateway documents / corpus projection policy; not agent HTTP path. |
| `src/services/ingestion/` | `api/router_modal_jobs.py`, `api/router_scraper_pipeline_ingest.py` | Gateway-side ingestion persistence helpers. |
| `src/services/scraper/` | `api/router_scrape.py` (+ uploader pipeline, CLI, active_crawl, etc.) | **Gateway-scoped** scraping surface; agent does **not** import this tree today. |
| `src/services/embedding/` | Shim re-exporting `src.embedding_service.main` | Legacy/alternate entry; align with **`embedding_service`** during cleanup. |
| `src/embedding_service/` | `agent.main` (embedding client), `services/scraper/uploader.py`, shims | **Shared** embedding HTTP/SDK client + app used by agent and scraper code paths. |
| `src/embedding/` | Re-export of `embedding_service` app | Shim; fold into **`embedding_service`** or gateway-only packaging. |
| `src/utils/tags.py` | `agent` tools + `api/router_documents.py` | Tag parsing/normalization for agent + gateway documents. |
| `src/utils/database_url.py` | `api/main.py`, `api/router_*` | DB URL resolution for gateway and ingestion. |
| `src/utils/postgres_json_sanitize.py` | `api/router_modal_jobs.py`, `services/ingestion/*` | Sanitization for persisted JSON/text. |
| `src/utils/scraper_api_keys.py` | `api/router_scraper_pipeline_ingest.py` | Gateway scraper auth helper. |
| `src/utils/gateway_dependency_errors.py` | `api/router_modal_jobs.py` | Gateway user-facing error shaping. |
| `src/utils/corpus_db_guard.py` | `src/config.py` (+ contract tests) | Canonical DB policy helper pulled into config bootstrap. |
| `src/utils/render_env_contract.py`, `src/utils/resource_metadata.py`, `src/utils/html_cleaner.py`, `src/utils/faq_loader.py`, … | Mixed tests + scraper + agent static paths | Classify per-consumer during **T016**; many are **orthogonal utilities** that can live in a small **`packages/python/vecinita-common`** or stay duplicated **only** if justified. |
| `src/services/db/` | Primarily **tests** (`backend/tests/test_services/db/`) today | Pool/security helpers; confirm runtime callers before extracting to **`packages/python/db`** (**PM-010**). |

---

## Shim / duplicate candidates (resolve during T016)

| Path | Issue | Recommendation |
|------|--------|----------------|
| `src/services/agent/server.py` | Re-exports `src.agent.main` | **Delete or relocate** with agent; avoid two FastAPI entry modules. |
| `src/services/agent/tools/db_search.py` | Thin wrapper over `src.agent.tools.db_search` | **Collapse** into `src.agent.tools` only. |
| `src/services/agent/*` (other) | Parallel copies under `services/agent` vs `agent` | Inventory `services/agent` tree vs `agent/`; keep **one** canonical tree under **`apis/agent`**. |

---

## Tests and scripts (not classified as gateway/agent “src” but blockers for T016)

- **`backend/tests/`**: Many tests import `src.api`, `src.agent`, or `src.services` freely; **T016** must update `PYTHONPATH`, fixtures, and Pact/contract paths together with `Makefile` / CI.
- **`backend/scripts/`**: `start_gateway_render.sh` is **gateway**; agent image CMD is inline in Dockerfile. Any script importing `src.services.scraper` is **gateway-adjacent**.

---

## Sign-off

- **T015** deliverable: this inventory is the **authoritative boundary draft** for **PM-007** / **PM-008** until **T016** updates rows in [path-mapping.md](./path-mapping.md).
- **Next**: **T016** — physical tree move + import rewires; re-run `make ci` and fix any drift (OpenAPI example import is the first likely breakage).

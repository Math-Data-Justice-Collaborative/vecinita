# Modal / HTTP migration inventory (feature 007)

**Purpose**: Track call sites and environment variables for routing scraper, embedding, and model traffic through **Modal deployed functions** (server-side SDK) instead of browser-reachable `*.modal.run` HTTP entrypoints where the spec requires it.

**Spec**: `specs/007-scraper-via-dm-api/spec.md`  
**Tasks**: `specs/007-scraper-via-dm-api/tasks.md` (**T001**–**T003** seed this file; later tasks append).

## Environment variables (DM API + service-clients)

| Variable | Role |
|----------|------|
| `MODAL_FUNCTION_INVOCATION` | `auto` / `1` / `0` / `http` — same semantics as gateway `backend/src/services/modal/invoker.py`. |
| `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` | Modal API credentials (also accept `MODAL_AUTH_KEY` / `MODAL_AUTH_SECRET`). |
| `MODAL_ENVIRONMENT_NAME` / `MODAL_ENV` | Optional `Function.from_name(..., environment_name=...)`. |
| `MODAL_SCRAPER_APP_NAME`, `MODAL_SCRAPER_HEALTH_FUNCTION` | Scraper Modal app + health RPC (default `health_check`). |
| `MODAL_EMBEDDING_APP_NAME`, `MODAL_EMBEDDING_SINGLE_FUNCTION`, `MODAL_EMBEDDING_BATCH_FUNCTION` | Embedding Modal app defaults align with gateway invoker. |
| `MODAL_MODEL_APP_NAME`, `MODAL_MODEL_CHAT_FUNCTION` | Model Modal app (chat path; classify `/predict` may remain HTTP until a Modal RPC is defined). |
| `SCRAPER_SERVICE_BASE_URL` / `VECINITA_SCRAPER_API_URL` | HTTP fallback for **non-production** / tests (`FR-009`). |

## Call sites — Python (`service-clients`)

| Module | Current transport | Modal path (when `MODAL_FUNCTION_INVOCATION` enabled) |
|--------|-------------------|------------------------------------------------------|
| `service_clients/scraper_client.py` | httpx → `{base}/scrape`, `/health` | **health**: Modal `health_check` RPC. **scrape**: httpx (no first-class Modal RPC for sync `/scrape` in inventory; DM orchestration should prefer job APIs on DM HTTP surface). |
| `service_clients/embedding_client.py` | httpx `/embed` | Modal `embed_query` (single text) → map to `EmbedResponse`. |
| `service_clients/model_client.py` | httpx `/predict` | HTTP unless a dedicated Modal predict function is introduced; `chat_completion` exists on model app for LLM-style work. |

## Submodule / backend layout

- **`apis/data-management-api/apps/backend/`**: FastAPI app **`vecinita_dm_api`** (see `README.md` there). **`GET /health`** uses `ScraperClient.health()` (Modal or HTTP). **`/jobs/*`** proxies with `ScraperClient.forward_jobs` to the scraper service. **`POST /embed`** and **`POST /predict`** use `EmbeddingClient` / `ModelClient` (**T017** / **T018**).

## Operator-safe errors (**T033**)

Until `apps/backend/` exposes FastAPI handlers (and any shared error helpers), **FR-006** operator-safe messaging for upstream HTTP failures is implemented in the DM SPA: `apps/data-management-frontend/src/app/api/operatorUpstreamErrors.ts` plus `normalizeUpstreamErrorMessage` in non-OK branches of `rag-api.ts`. When the backend app lands, align JSON error shapes (`detail` / `message`) with the same sanitization rules where appropriate so UI and API stay consistent.

## Schemathesis split (T012)

- **Primary live suite:** `backend/tests/integration/test_data_management_api_schema_schemathesis.py` (parametrized `case.call_and_validate`, hooks in `backend/tests/schemathesis_hooks.py`).
- **Contract-only (no Bearer):** `test_data_management_openapi_defines_scraper_job_paths` in the same file fetches public `openapi.json` and asserts `/health` + `/jobs` exist (skips on auth-gated or unreachable hosts).
- **DM submodule `apis/data-management-api/tests/`:** add ASGITransport-only tests here only if a route cannot be exercised from the backend pytest harness (none required as of this inventory update).

---

## T002 scan — `apps/data-management-frontend/src/app/api/`

**Scope**: direct scraper hosts, Modal browser auth, gateway modal-jobs bypass.

| File | Notes |
|------|--------|
| `scraper-config.ts` | Reads `VITE_DM_API_BASE_URL` (**DM API origin**). Previously supported `VITE_USE_GATEWAY_MODAL_JOBS` + `VITE_VECINITA_GATEWAY_URL` → gateway `/api/v1/modal-jobs/scraper` (**removed** as default path in 007 — jobs use `${DM API}/jobs`). |
| `scraper-config.ts` | `VITE_MODAL_AUTH_KEY` / `VITE_MODAL_AUTH_SECRET` — **deprecated** browser Modal auth (diagnostic only). |
| `rag-api.ts` | Uses `scraperRuntimeConfig.apiBaseUrl` and `scraperJobsApiRoot()` for fetch URLs. |
| `modal-types.ts`, `types/dm-openapi.generated.ts` | Comments / schema text referencing Modal **implementation** (not browser URLs). |

---

## T003 scan — `frontend/src/`

**Scope**: runtime backend hosts vs gateway.

| File | Notes |
|------|--------|
| `app/services/agentService.ts` | Resolves gateway via `VITE_GATEWAY_URL` / `VITE_BACKEND_URL`; dev fallback `http://localhost:8004/api/v1` — **gateway**, acceptable for main app per **FR-002**. |
| `app/services/modelRegistry.ts` | Same gateway pattern. |
| `app/pages/DocumentsDashboard.tsx` | `VITE_GATEWAY_URL` / dev `/api/v1` — gateway-oriented. |
| Tests under `app/services/__tests__/` | Use `localhost:8004` / `8002` as **test doubles**, not product defaults. |

**No `modal.run` literals found** in sampled `frontend/src` app code; continue to guard with **T022** / **SC-005**.

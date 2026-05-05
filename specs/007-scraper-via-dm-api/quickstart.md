# Quickstart — Feature 007 (local dev & env)

## Preconditions

- Monorepo cloned; Python envs for `apis/data-management-api` and `backend/` per root docs.
- Optional: Modal account and tokens for **live** function tests (not required for default `pytest` with mocks).

## Environment variables (conceptual)

### Data-management API (Modal function mode)

Align with gateway naming where possible:

- `MODAL_FUNCTION_INVOCATION` — `auto` | `1` | `0` (same semantics as gateway: `auto` enables when `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` set).
- `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` — Modal API credentials (never commit).
- `MODAL_ENVIRONMENT_NAME` — optional, passed to `Function.from_name`.
- Scraper: `MODAL_SCRAPER_APP_NAME` (default `vecinita-scraper`), `MODAL_SCRAPER_JOB_SUBMIT_FUNCTION`, `MODAL_SCRAPER_JOB_GET_FUNCTION`, `MODAL_SCRAPER_JOB_LIST_FUNCTION`, `MODAL_SCRAPER_JOB_CANCEL_FUNCTION` — override only when Modal app renames functions.
- Embedding: `MODAL_EMBEDDING_APP_NAME`, `MODAL_EMBEDDING_SINGLE_FUNCTION`, `MODAL_EMBEDDING_BATCH_FUNCTION`.
- Model: `MODAL_MODEL_APP_NAME`, `MODAL_MODEL_CHAT_FUNCTION` — when ingest paths require chat/completion from Modal model app.

### Frontends

- **Data-management SPA**: base URL for API calls must point at **data-management-api** host only (e.g. `VITE_DM_API_BASE_URL` or project-specific equivalent—see tasks for canonical name).
- **Main SPA** (`frontend/`): base URL must point at **gateway** only.

### Gateway / agent (unchanged baseline)

- `AGENT_SERVICE_URL` — internal HTTP to agent.
- Agent: `OLLAMA_BASE_URL`, `EMBEDDING_SERVICE_URL` must satisfy `enforce_modal_function_policy_for_urls` when they contain `modal.run`.

## Local commands (illustrative)

```bash
# DM API tests (from data-management-api workspace / uv)
cd apis/data-management-api && uv run pytest packages/service-clients/tests tests -q

# Gateway / agent policy tests
cd backend && pytest tests/test_services tests/test_api -q
```

Use `make ci` from repo root before merge (see `TESTING_DOCUMENTATION.md` for full matrix).

## SC-001 / SC-002: what “sampled” means

For release evidence, **sampled** requests are those (or their **stand-in assertions**) listed in the **primary-flow matrix** for each app: scripted unit/integration tests that fix expected API origins, optional Playwright rows where E2E exists, and optional manual smoke checklist lines. **100%** means every matrix row passes—not an undefined random sample.

## Primary-flow release matrix (artifact)

**Normative for SC-001, SC-002, and SC-003:** maintain one **primary-flow release matrix** that lists every row used for “sampled / 100%” and for “no deprecated scraper URL” checks. **T034** (tasks) fills and links this section before release; **T035** may mirror or link from `TESTING_DOCUMENTATION.md` at repo root.

| Client | Primary flow (short name) | Evidence type | Location (test file, spec path, or checklist ID) |
|--------|---------------------------|---------------|---------------------------------------------------|
| Data-management SPA | DM API base URL + jobs root resolve to one HTTP origin (no `*.modal.run`, no `VITE_*MODAL_TOKEN*`) | Vitest | `apps/data-management-frontend/src/app/api/scraper-config.test.ts` |
| Data-management SPA | Scrape job list uses `{DM}/jobs` (not gateway modal-jobs) | Vitest | `apps/data-management-frontend/src/app/api/rag-api.test.ts` |
| Data-management SPA | Pact: `/health` + `/jobs` on DM host | Pact | `apps/data-management-frontend/tests/pact/dm-api.pact.test.ts` |
| Main SPA | Gateway base resolution on Render-style hosts | Vitest | `frontend/src/app/lib/apiBaseResolution.test.ts` |
| Main SPA | No forbidden Modal hosts or token keys in `VITE_*` | Vitest | `frontend/src/app/lib/frontendViteEnvGuards.test.ts` |
| Main SPA | Chat smoke: no browser requests to `*.modal.run` | Playwright | `frontend/tests/e2e/chat-gateway-smoke.spec.ts` |

Add rows until every **primary flow** in **SC-001** / **SC-002** is covered; extend rows for **SC-003** (deprecated scraper URL) where those flows overlap scraping management.

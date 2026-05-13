# Modal Integration Plan: Gateway
> Auto-generated: 2026-05-12

Source: `apis/gateway/src/services/modal/invoker.py`, `apis/gateway/src/services/modal/job_registry.py`

## Overview

The gateway uses Modal SDK to invoke serverless functions for embedding, scraping, and reindex operations. This replaces the earlier HTTP-to-Modal pattern where the gateway called `*.modal.run` HTTP endpoints.

## Invocation Pattern

All Modal calls use the **deployed function** pattern:

```python
fn = modal.Function.from_name(app_name, function_name, environment_name=env)
result = fn.remote(...)      # blocking
call = fn.spawn(...)          # non-blocking, returns FunctionCall
result = call.get(timeout=N)  # poll result
```

Source: Modal SDK docs — "Trigger deployed functions" guide.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODAL_FUNCTION_INVOCATION` | (empty = off) | `auto`, `1`/`true`, `0`/`false`/`http` |
| `MODAL_TOKEN_ID` | — | SDK authentication |
| `MODAL_TOKEN_SECRET` | — | SDK authentication |
| `MODAL_ENVIRONMENT_NAME` | — | Optional deployment environment (staging/production) |

### Auto Mode

When `MODAL_FUNCTION_INVOCATION=auto`:
- Enabled only if both `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` are set
- Falls back to HTTP if tokens are absent
- Safe default for mixed environments

## Registered Functions

### Embedding Functions

| App | Function | Invocation | Gateway Caller |
|-----|----------|-----------|---------------|
| `vecinita-embedding` | `embed_query` | `.remote(text)` | `invoke_modal_embedding_single()` |
| `vecinita-embedding` | `embed_batch` | `.remote(texts)` | `invoke_modal_embedding_batch()` |

Env overrides: `MODAL_EMBEDDING_APP_NAME`, `MODAL_EMBEDDING_SINGLE_FUNCTION`, `MODAL_EMBEDDING_BATCH_FUNCTION`

### Scraper Functions

| App | Function | Invocation | Gateway Caller |
|-----|----------|-----------|---------------|
| `vecinita-scraper` | `modal_scrape_job_submit` | `.remote(payload)` | `invoke_modal_scrape_job_submit()` |
| `vecinita-scraper` | `modal_scrape_job_get` | `.remote(job_id)` | `invoke_modal_scrape_job_get()` |
| `vecinita-scraper` | `modal_scrape_job_list` | `.remote(user_id, limit)` | `invoke_modal_scrape_job_list()` |
| `vecinita-scraper` | `modal_scrape_job_cancel` | `.remote(job_id)` | `invoke_modal_scrape_job_cancel()` |
| `vecinita-scraper` | `trigger_reindex` | `.spawn(...)` then `.get(timeout)` | `invoke_modal_scraper_reindex()`, `spawn_modal_scraper_reindex()` |

Env overrides: `MODAL_SCRAPER_APP_NAME`, `MODAL_SCRAPER_*_FUNCTION`

### Model Functions

| App | Function | Invocation | Gateway Caller |
|-----|----------|-----------|---------------|
| `vecinita-model` | `chat_completion` | `.remote(model, messages, temperature)` | `invoke_modal_model_chat()` |

## Startup Policy Enforcement

`enforce_modal_function_policy_for_urls()` runs at startup (in `lifespan()`):

1. Scans endpoint URLs: `MODEL_ENDPOINT`, `EMBEDDING_SERVICE_URL`, `SCRAPER_ENDPOINT`, `REINDEX_SERVICE_URL`
2. If any URL contains `modal.run` **and** `MODAL_FUNCTION_INVOCATION` is not enabled → **fail fast** with `RuntimeError`
3. If invocation enabled but tokens missing → **fail fast**

This prevents silent HTTP-to-Modal fallbacks that bypass authentication.

## Function Lookup Cache

`_lookup_function()` is `@lru_cache(maxsize=32)` — function references are resolved once per `(app_name, function_name, environment_name)` tuple and cached for the process lifetime.

## Job Registry

Source: `apis/gateway/src/services/modal/job_registry.py`

Tracks spawned Modal `FunctionCall` handles for async operations (e.g., reindex).

| Property | Value |
|----------|-------|
| Primary store | `modal.Dict` (named `vecinita-gateway-modal-jobs`) |
| Fallback store | In-memory Python dict |
| Key prefix | `mj:` |
| Index limit | 200 most recent |
| Disable Modal Dict | `MODAL_JOB_REGISTRY_DISABLE=true` |

### Registry Operations

| Operation | Endpoint | Behavior |
|-----------|----------|----------|
| Create | `POST /modal-jobs/reindex/spawn` | Stores `gateway_job_id` → `{ kind, status, modal_function_call_id, ... }` |
| Read | `GET /modal-jobs/registry/{id}` | Optionally refreshes by calling `FunctionCall.get(timeout=0.05)` |
| List | `GET /modal-jobs/registry` | Returns most recent IDs from index |
| Delete | `DELETE /modal-jobs/registry/{id}` | Removes from Dict and memory |

## Pipeline Callback Flow

When `MODAL_SCRAPER_PERSIST_VIA_GATEWAY=true`:

1. Gateway creates `scraping_jobs` row in Postgres on submit
2. Modal `scraper_worker` processes the URL
3. Worker calls back to gateway internal endpoints:
   - `POST /internal/scraper-pipeline/jobs/{id}/status` — stage transitions
   - `POST /internal/scraper-pipeline/crawled-urls` — crawled URL artifacts
   - `POST /internal/scraper-pipeline/extracted-content` — extracted text
   - `POST /internal/scraper-pipeline/processed-documents` — markdown
   - `POST /internal/scraper-pipeline/chunks` — document chunks
   - `POST /internal/scraper-pipeline/embeddings` — vector embeddings
4. Auth: `X-Scraper-Pipeline-Ingest-Token` header validated against `SCRAPER_API_KEYS`

## Threading Model

Modal SDK is synchronous; all invocations are wrapped in `asyncio.to_thread()` to avoid blocking the FastAPI event loop.

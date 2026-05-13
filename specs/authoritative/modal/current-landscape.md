# Current Modal Integration Landscape

> Auto-generated: 2026-05-11

## Summary

The Vecinita platform uses Modal for GPU-burst and CPU-intensive serverless workloads that are cost-prohibitive to run persistently on Render. Three Modal apps handle embedding generation, LLM chat completion, and web scraping pipelines. The gateway and agent services invoke Modal functions via the `modal.Function.from_name` SDK pattern, controlled by `MODAL_FUNCTION_INVOCATION`.

## Apps and Functions

### vecinita-embedding (`modal-apps/embedding-modal/`)

| Property | Value |
|----------|-------|
| App name | `vecinita-embedding` |
| Python | >=3.11 |
| Image | debian_slim + fastembed>=0.7.4 |
| Volume | `vecinita-embedding-models` (model cache) |
| Secrets | None (standalone) |
| Deploy | `modal deploy src/vecinita/app.py` |

**Functions:**

| Function | Timeout | CPU | Purpose |
|----------|---------|-----|---------|
| `embed_query` | 600s | default | Single text → embedding vector |
| `embed_batch` | 600s | default | Batch texts → embedding vectors |

**Model:** BAAI/bge-small-en-v1.5 (via fastembed, cached on Modal Volume)

---

### vecinita-model (`modal-apps/model-modal/`)

| Property | Value |
|----------|-------|
| App name | configurable via `settings.app_name` |
| Python | >=3.11 |
| Image | Custom Ollama image (debian + ollama binary) |
| Volume | `vecinita-models` (Ollama model weights) |
| Secrets | None (auth via Modal tokens) |
| Deploy | `modal deploy src/vecinita/app.py` |

**Functions:**

| Function | Timeout | CPU | Purpose |
|----------|---------|-----|---------|
| `chat_completion` | configurable (settings.timeout) | 4.0 | Ollama chat completion (gemma3 default) |
| `download_model` | 3600s | default | Pull model weights to volume |
| `download_default_model` | 3600s | default | Ensure default model cached |

**Lifecycle:** Startup preload with retry loop → Ollama serve → chat → teardown (cache-preserving). Scaledown window is configurable.

---

### vecinita-scraper (`modal-apps/scraper/`)

| Property | Value |
|----------|-------|
| App name | `vecinita-scraper` |
| Python | >=3.11 |
| Image | debian_slim + crawl4ai, docling, langchain, playwright, psycopg2, etc. |
| Queues | 5 (scrape-jobs, process-jobs, chunk-jobs, embed-jobs, store-jobs) |
| Secrets | `vecinita-scraper-env` (DB, Modal tokens, API keys) |
| Deploy | `modal deploy src/vecinita_scraper/app.py` |

**Functions:**

| Function | Timeout | Purpose |
|----------|---------|---------|
| `health_check` | default | Worker health probe |
| `modal_scrape_job_submit` | 300s | Create scraping job (Postgres + queue) |
| `modal_scrape_job_get` | 120s | Return job status |
| `modal_scrape_job_list` | 120s | List jobs for user |
| `modal_scrape_job_cancel` | 120s | Cancel job |
| `trigger_reindex` | 60s | Kick pipeline drainers |
| `scraper_worker` | (workers module) | Execute scrape for a single URL |
| `drain_scrape_queue` | (workers module) | Pull from scrape-jobs queue |
| `drain_process_queue` | (workers module) | Pull from process-jobs queue |
| `drain_chunk_queue` | (workers module) | Pull from chunk-jobs queue |
| `drain_embed_queue` | (workers module) | Pull from embed-jobs queue |
| `drain_store_queue` | (workers module) | Pull from store-jobs queue |

**Pipeline architecture:** Job submission → scrape-jobs queue → scraper_worker → process-jobs → chunker → chunk-jobs → embedder → embed-jobs → finalizer → store-jobs. Each stage uses `Function.spawn` / `spawn_map.aio` for bounded concurrency.

**HTTP API:** A separate FastAPI ASGI app (`vecinita_scraper/api/`) is also deployed on Modal for REST access (used by DM frontend and external callers).

---

## Caller Integration (Gateway → Modal)

The gateway uses `apis/gateway/src/services/modal/invoker.py` to call all Modal functions.

| Gateway function | Modal app | Modal function | Pattern |
|-----------------|-----------|----------------|---------|
| `invoke_modal_embedding_single` | vecinita-embedding | `embed_query` | `.remote()` |
| `invoke_modal_embedding_batch` | vecinita-embedding | `embed_batch` | `.remote()` |
| `invoke_modal_model_chat` | vecinita-model | `chat_completion` | `.remote()` |
| `invoke_modal_scraper_reindex` | vecinita-scraper | `trigger_reindex` | `.spawn()` + `.get(timeout)` |
| `spawn_modal_scraper_reindex` | vecinita-scraper | `trigger_reindex` | `.spawn()` (fire-and-forget) |
| `invoke_modal_scrape_job_submit` | vecinita-scraper | `modal_scrape_job_submit` | `.remote()` |
| `invoke_modal_scrape_job_get` | vecinita-scraper | `modal_scrape_job_get` | `.remote()` |
| `invoke_modal_scrape_job_list` | vecinita-scraper | `modal_scrape_job_list` | `.remote()` |
| `invoke_modal_scrape_job_cancel` | vecinita-scraper | `modal_scrape_job_cancel` | `.remote()` |
| `get_modal_function_call_result` | (any) | (by call ID) | `FunctionCall.from_id` + `.get()` |

**Resolution pattern:** Each invoker function reads app name and function name from environment variables with sensible defaults, then uses `modal.Function.from_name(app, fn)` to get a handle. LRU cache avoids repeated lookups.

**Invocation policy:**
- `MODAL_FUNCTION_INVOCATION=auto` — enabled only when tokens are configured
- `MODAL_FUNCTION_INVOCATION=on/1/true` — always require Modal SDK
- Unset or `off/false/http` — use HTTP fallback
- `enforce_modal_function_policy_for_urls` fails fast if `*.modal.run` URLs exist without Modal function mode enabled

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODAL_TOKEN_ID` | (required) | SDK auth token ID |
| `MODAL_TOKEN_SECRET` | (required) | SDK auth token secret |
| `MODAL_FUNCTION_INVOCATION` | (empty = off) | Master toggle: auto/on/off |
| `MODAL_ENVIRONMENT_NAME` | (empty) | Staging/production env |
| `MODAL_EMBEDDING_APP_NAME` | vecinita-embedding | Embedding app name override |
| `MODAL_EMBEDDING_SINGLE_FUNCTION` | embed_query | Single embed function name |
| `MODAL_EMBEDDING_BATCH_FUNCTION` | embed_batch | Batch embed function name |
| `MODAL_MODEL_APP_NAME` | vecinita-model | Model app name override |
| `MODAL_MODEL_CHAT_FUNCTION` | chat_completion | Chat function name |
| `MODAL_SCRAPER_APP_NAME` | vecinita-scraper | Scraper app name override |
| `MODAL_SCRAPER_JOB_SUBMIT_FUNCTION` | modal_scrape_job_submit | Job submit function |
| `MODAL_SCRAPER_JOB_GET_FUNCTION` | modal_scrape_job_get | Job get function |
| `MODAL_SCRAPER_JOB_LIST_FUNCTION` | modal_scrape_job_list | Job list function |
| `MODAL_SCRAPER_JOB_CANCEL_FUNCTION` | modal_scrape_job_cancel | Job cancel function |
| `MODAL_SCRAPER_REINDEX_FUNCTION` | trigger_reindex | Reindex function |
| `MODAL_SCRAPER_REINDEX_FUNCTION_TIMEOUT` | 120 | Reindex spawn get timeout |
| `MODAL_WORKSPACE` | vecinita | Modal workspace name |
| `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` | 1 | Gateway-owned scraping_jobs persistence |

## Deploy Pipeline

| Step | Command / Config |
|------|------------------|
| Local dev | `modal serve modal-apps/<name>/src/vecinita/app.py` |
| CI deploy | `.github/workflows/modal-deploy.yml` (per-app flags) |
| Manual deploy | `modal deploy modal-apps/<name>/src/vecinita/app.py` |
| Post-deploy (model) | `download_default_model` runs automatically |
| Makefile | `make modal-deploy`, `make modal-serve` |

**CI trigger:** Modal deploy runs after Tests pass on `main` branch. Each app can be deployed independently via `deploy_<name>=true` workflow dispatch input.

## Capacity Profile

| App | Expected cold start | Typical invocations/day | Avg duration |
|-----|---------------------|------------------------|--------------|
| vecinita-embedding | ~5–10s (model load) | 50–500 | <2s per query |
| vecinita-model | ~15–30s (Ollama + model) | 10–100 | 5–30s per chat |
| vecinita-scraper | ~10–20s (playwright) | 10–50 jobs | 30–120s per scrape |

## Spec-driven development context

This document is part of the project's spec-driven development workflow. Feature specs live under `specs/NNN-slug-name/`. Key related specs:
- `specs/004-modal-model-prepull/` — Model pre-pull workflow
- `specs/007-scraper-via-dm-api/` — Scraper invocation via DM API
- `specs/009-modal-scraper-gateway-env/` — Modal-gateway env wiring
- `specs/012-queued-page-ingestion-pipeline/` — Queue-based pipeline architecture

Cross-reference `specs/authoritative/` for other authoritative documents (dependencies, Render integration, changelogs).

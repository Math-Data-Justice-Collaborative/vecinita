# Modal Integration Plan: Scraper Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/scraper/src/vecinita_scraper/app.py`

## Overview

The scraper worker is a Modal-native application. All compute runs on Modal serverless; the queue-based pipeline is built entirely on Modal primitives. This document details the Modal app configuration, queue architecture, secrets, spawn patterns, and resource allocation.

## Modal App Configuration

| Property | Value |
|----------|-------|
| App name | `vecinita-scraper` |
| Deploy command | `modal deploy src/vecinita_scraper/app.py` |
| Python | ≥3.11 |
| Image base | `debian_slim` |
| ASGI app | FastAPI mounted via `@app.function(asgi_app=...)` |

### Image Build

```python
image = (
    modal.Image.debian_slim()
    .pip_install(
        "crawl4ai>=0.4.0",
        "docling>=0.4.0",
        "langchain>=0.1.0",
        "playwright",
        "psycopg2-binary",
        "tiktoken",
        "structlog",
        "pypdf",
        "fastembed",
        "pydantic>=2.0",
        "fastapi",
        "modal>=0.59.0",
    )
    .run_commands("playwright install chromium")
)
```

## Function Definitions

### Job Management Functions

| Function | Decorator | Timeout | Secrets | Purpose |
|----------|-----------|---------|---------|---------|
| `health_check` | `@app.function()` | Default | `vecinita-scraper-env` | Health probe |
| `modal_scrape_job_submit` | `@app.function(timeout=300)` | 300s | `vecinita-scraper-env` | Create job, enqueue |
| `modal_scrape_job_get` | `@app.function(timeout=120)` | 120s | `vecinita-scraper-env` | Read job status |
| `modal_scrape_job_list` | `@app.function(timeout=120)` | 120s | `vecinita-scraper-env` | List user jobs |
| `modal_scrape_job_cancel` | `@app.function(timeout=120)` | 120s | `vecinita-scraper-env` | Cancel job |
| `trigger_reindex` | `@app.function(timeout=60)` | 60s | `vecinita-scraper-env` | Drain all queues |

### Worker Functions

| Function | Decorator | Resources | Purpose |
|----------|-----------|-----------|---------|
| `scraper_worker` | `@app.function()` | 1-2 CPU, 1-2GB RAM | Scrape single URL |
| `drain_scrape_queue` | `@app.function()` | Default | Pull from scrape-jobs |
| `drain_process_queue` | `@app.function()` | Default | Pull from process-jobs |
| `drain_chunk_queue` | `@app.function()` | Default | Pull from chunk-jobs |
| `drain_embed_queue` | `@app.function()` | Default | Pull from embed-jobs |
| `drain_store_queue` | `@app.function()` | Default | Pull from store-jobs |

## Queue Architecture

### Queue Definitions

5 Modal queues provide inter-stage decoupling in the pipeline.

| Queue Name | Producer | Consumer | Payload Schema |
|------------|----------|----------|---------------|
| `scrape-jobs` | `modal_scrape_job_submit` | `drain_scrape_queue` | `{ job_id: str, url: str, depth: int, timeout: int }` |
| `process-jobs` | `scraper_worker` | `drain_process_queue` | `{ job_id: str, crawled_url_id: str, content: str, metadata: dict }` |
| `chunk-jobs` | `drain_process_queue` | `drain_chunk_queue` | `{ job_id: str, document_id: str }` |
| `embed-jobs` | `drain_chunk_queue` | `drain_embed_queue` | `{ job_id: str, chunk_ids: list[str] }` |
| `store-jobs` | `drain_embed_queue` | `drain_store_queue` | `{ job_id: str, finalize: bool }` |

### Queue Flow

```
modal_scrape_job_submit
    │
    ▼
[scrape-jobs] ──► drain_scrape_queue ──► scraper_worker
                                              │
                                              ▼
                                        [process-jobs] ──► drain_process_queue
                                                                │
                                                                ▼
                                                          [chunk-jobs] ──► drain_chunk_queue
                                                                                │
                                                                                ▼
                                                                          [embed-jobs] ──► drain_embed_queue
                                                                                                │
                                                                                                ▼
                                                                                          [store-jobs] ──► drain_store_queue
                                                                                                                │
                                                                                                                ▼
                                                                                                          Job complete
```

### Queue Behavior

| Property | Value |
|----------|-------|
| Delivery | At-least-once |
| Ordering | Not guaranteed |
| Visibility timeout | Modal-managed |
| Dead letter | Not configured (items retry on next drain) |
| Manual drain | `trigger_reindex` kicks all drainers |

## Spawn Patterns

### Function.spawn (Non-blocking)

Used for fire-and-forget invocations and pipeline parallelism.

```python
# Gateway fire-and-forget reindex
fn = modal.Function.from_name("vecinita-scraper", "trigger_reindex")
call = fn.spawn()
# No .get() — fire and forget

# Pipeline: spawn workers for each URL
for url in urls:
    scraper_worker.spawn(job_id=job_id, url=url, depth=depth)
```

### spawn_map.aio (Bounded Parallelism)

Used for batch processing with bounded concurrency.

```python
# Process multiple URLs with bounded concurrency
async for result in scraper_worker.spawn_map.aio(
    [(job_id, url, depth) for url in urls]
):
    # Results arrive as workers complete
    process_result(result)
```

### Function.remote (Blocking)

Used for synchronous job management calls from the gateway.

```python
# Gateway blocking call
fn = modal.Function.from_name("vecinita-scraper", "modal_scrape_job_submit")
result = fn.remote(payload)  # Blocks until complete or timeout
```

### spawn + get (Blocking with Timeout)

Used for reindex with a timeout.

```python
# Gateway blocking reindex with timeout
fn = modal.Function.from_name("vecinita-scraper", "trigger_reindex")
call = fn.spawn()
result = call.get(timeout=60)  # Wait up to 60s
```

## Secrets Configuration

### Secret Group: `vecinita-scraper-env`

| Secret | Required | Purpose |
|--------|----------|---------|
| `MODAL_TOKEN_ID` | Yes | Modal SDK authentication |
| `MODAL_TOKEN_SECRET` | Yes | Modal SDK authentication |
| `MODAL_WORKSPACE` | Yes | Modal workspace identifier |
| `MODAL_DATABASE_URL` | Yes | PostgreSQL connection (Modal context) |
| `DATABASE_URL` | Yes | PostgreSQL connection (Render context) |
| `SUPABASE_PROJECT_URL` | Conditional | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Conditional | Supabase service role key |
| `EMBEDDING_UPSTREAM_URL` | Yes | Embedding service URL |
| `OLLAMA_BASE_URL` | Yes | Ollama model server URL |
| `SCRAPER_API_KEYS` | Yes (prod) | API authentication keys |

### Secret Access Pattern

```python
@app.function(secrets=[modal.Secret.from_name("vecinita-scraper-env")])
def modal_scrape_job_submit(payload):
    db_url = os.environ["DATABASE_URL"]
    # Secrets are injected as environment variables
```

## Environment Variables (Non-Secret)

| Variable | Default | Purpose |
|----------|---------|---------|
| `CHUNK_MAX_SIZE_TOKENS` | 1024 | Max tokens per chunk |
| `CHUNK_MIN_SIZE_TOKENS` | 256 | Min tokens per chunk |
| `CHUNK_OVERLAP_RATIO` | 0.2 | Overlap between chunks |
| `CRAWL4AI_MAX_DEPTH` | 3 | Max recursive crawl depth |
| `CRAWL4AI_TIMEOUT_SECONDS` | 60 | Per-URL crawl timeout |
| `ENVIRONMENT` | development | Runtime environment |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `MODAL_PROXY_AUTH_ENABLED` | true | Enable proxy auth |

## Container Lifecycle

| Phase | Duration | Resource Impact |
|-------|----------|----------------|
| Image pull | First deploy only | One-time |
| Container start | 1-2s | Minimal |
| Playwright init | 10-20s (cold) | ~500MB RAM |
| Function execution | 1s-300s | Varies by function |
| Keep-alive | 5-15 min | Warm containers reused |
| Scale-to-zero | Automatic | No cost when idle |

## ASGI Deployment

The FastAPI app is also deployed on Modal as an ASGI endpoint:

```python
@app.function(asgi_app=fastapi_app)
def api():
    pass
```

This provides a Modal-native HTTPS URL for the REST API, in addition to the Render deployment.

## Monitoring

| Metric | Source | Dashboard |
|--------|--------|-----------|
| Function invocations | Modal | Modal dashboard → Functions |
| Function errors | Modal | Modal dashboard → Functions → Errors |
| Container count | Modal | Modal dashboard → Containers |
| Queue depth | Modal | Modal dashboard → Queues |
| Function duration P50/P99 | Modal | Modal dashboard → Functions → Latency |
| Cold start rate | Modal | Modal dashboard → Containers → Cold starts |

## Deployment Workflow

```
1. Push to vecinita-scraper submodule (main branch)
2. Update submodule reference in monorepo
3. Run: modal deploy src/vecinita_scraper/app.py
4. Verify: health_check.remote() returns healthy
5. Smoke test: submit test job, verify pipeline completes
```

### Rollback

```
1. Identify last-known-good commit in submodule
2. Checkout that commit: cd modal-apps/scraper && git checkout <sha>
3. Redeploy: modal deploy src/vecinita_scraper/app.py
4. Verify health
```

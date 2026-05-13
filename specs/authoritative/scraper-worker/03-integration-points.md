# Integration Points: Scraper Worker
> Auto-generated: 2026-05-12

See [diagrams/integration-points.md](diagrams/integration-points.md) for the connectivity diagram.

## Overview

The scraper worker integrates with the gateway (inbound calls), PostgreSQL (persistence), embedding service (vector generation), and external web content (scraping targets). All inbound invocations arrive via Modal SDK function calls or the FastAPI REST facade on Render.

## Integration Map

| Direction | Service | Protocol | Purpose |
|-----------|---------|----------|---------|
| ← inbound | Gateway | Modal SDK `.remote()` / `.spawn()` | Job CRUD, reindex triggers |
| ← inbound | DM Frontend | HTTP REST | Job browsing, document browsing |
| → outbound | PostgreSQL (Render) | psycopg2 TCP | Job state, crawled URLs, chunks, embeddings |
| → outbound | Embedding service | HTTP / Modal SDK | Generate chunk embeddings |
| → outbound | Web targets | HTTP (Playwright) | Crawl and scrape web pages |
| ↔ callback | Gateway | HTTP POST | Pipeline stage callbacks (when gateway persistence enabled) |

## Inbound: Gateway → Scraper (Modal SDK)

Source: `apis/gateway/src/services/modal/invoker.py`

| Gateway Function | Modal Function | Pattern | Timeout | Purpose |
|-----------------|---------------|---------|---------|---------|
| `invoke_modal_scrape_job_submit` | `modal_scrape_job_submit` | `.remote()` | 300s | Create scraping job |
| `invoke_modal_scrape_job_get` | `modal_scrape_job_get` | `.remote()` | 120s | Get job status |
| `invoke_modal_scrape_job_list` | `modal_scrape_job_list` | `.remote()` | 120s | List user's jobs |
| `invoke_modal_scrape_job_cancel` | `modal_scrape_job_cancel` | `.remote()` | 120s | Cancel job |
| `invoke_modal_scraper_reindex` | `trigger_reindex` | `.spawn()` + `.get(timeout)` | 60s | Blocking reindex |
| `spawn_modal_scraper_reindex` | `trigger_reindex` | `.spawn()` | fire-and-forget | Non-blocking reindex |

### Error Handling (Gateway → Scraper)

| Error | Gateway Behavior |
|-------|-----------------|
| `modal.exception.TimeoutError` | Return 504 Gateway Timeout to client |
| `modal.exception.FunctionTimeoutError` | Return 504 with function timeout details |
| `modal.exception.RemoteError` | Return 502 Bad Gateway |
| Connection failure | Return 503 Service Unavailable |

## Inbound: DM Frontend → Scraper REST API

The FastAPI ASGI app deployed on Render serves as the DM API facade.

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/v1/jobs` | POST | API key | Submit scrape job |
| `/api/v1/jobs/{id}` | GET | API key | Get job status |
| `/api/v1/jobs` | GET | API key | List jobs |
| `/api/v1/jobs/{id}/cancel` | POST | API key | Cancel job |
| `/api/v1/documents` | GET | API key | List documents |
| `/api/v1/documents/{id}` | GET | API key | Get document |
| `/api/v1/health` | GET | None | Health check |

Auth: `SCRAPER_API_KEYS` validated via middleware or dependency.

## Outbound: Scraper → PostgreSQL

Source: `modal-apps/scraper/src/vecinita_scraper/`

| Operation | Table | Trigger | SQL |
|-----------|-------|---------|-----|
| Create job | `scraping_jobs` | `modal_scrape_job_submit` | `INSERT` |
| Update status | `scraping_jobs` | Each pipeline stage transition | `UPDATE SET status, pipeline_stage, updated_at` |
| Store crawled URL | `crawled_urls` | `scraper_worker` completion | `INSERT` |
| Store document | `documents` | `drain_process_queue` | `INSERT` or `UPSERT` |
| Store chunks | `document_chunks` | `drain_chunk_queue` | `INSERT` batch |
| Store embeddings | `chunk_embeddings` | `drain_embed_queue` | `INSERT` batch |
| Mark complete | `scraping_jobs` | `drain_store_queue` final | `UPDATE SET status='completed', completed_at` |
| Cancel job | `scraping_jobs` | `modal_scrape_job_cancel` | `UPDATE SET status='cancelled'` |

### Connection Configuration

| Property | Value |
|----------|-------|
| Driver | `psycopg2-binary` |
| Connection string | `DATABASE_URL` env var (Render internal URL) |
| Connection pooling | Per-function invocation (Modal containers are ephemeral) |
| SSL | Required in production (Render enforces) |

## Outbound: Scraper → Embedding Service

| Property | Value |
|----------|-------|
| Target | `EMBEDDING_UPSTREAM_URL` or Modal `vecinita-embedding` |
| Protocol | HTTP POST or Modal SDK `.remote()` |
| Payload | `{ "texts": ["chunk1", "chunk2", ...] }` |
| Response | `{ "embeddings": [[0.1, ...], [0.2, ...]] }` |
| Batch size | Configurable, typically 32-64 texts per call |
| Retry | 3 attempts with exponential backoff |
| Timeout | `UPSTREAM_TIMEOUT_SECONDS` (default 55s) |

## Outbound: Scraper → Web Targets (Playwright + Crawl4AI)

| Property | Value |
|----------|-------|
| Browser | Chromium via Playwright |
| Crawl engine | Crawl4AI |
| Max depth | `CRAWL4AI_MAX_DEPTH` (default 3) |
| Per-URL timeout | `CRAWL4AI_TIMEOUT_SECONDS` (default 60s) |
| Content extraction | Crawl4AI for HTML, Docling for PDFs |
| Robots.txt | Respected by default |
| Rate limiting | Built-in Crawl4AI throttling |

### Error Handling (Crawl)

| Error | Behavior |
|-------|----------|
| DNS failure | Mark URL as `failed`, log error, continue other URLs |
| HTTP 4xx | Mark URL as `failed` with status code |
| HTTP 5xx | Retry once, then mark as `failed` |
| Timeout | Mark URL as `failed`, `error_message = "timeout"` |
| JavaScript rendering error | Fall back to static HTML extraction |

## Callback: Scraper → Gateway (Pipeline Persistence)

When `MODAL_SCRAPER_PERSIST_VIA_GATEWAY=true`, the scraper worker calls back to gateway internal endpoints during pipeline execution.

| Callback | Gateway Endpoint | Purpose |
|----------|-----------------|---------|
| Stage transition | `POST /api/v1/internal/scraper-pipeline/jobs/{id}/status` | Update pipeline stage |
| Crawled URL | `POST /api/v1/internal/scraper-pipeline/crawled-urls` | Store crawled URL artifact |
| Chunks | `POST /api/v1/internal/scraper-pipeline/chunks` | Store document chunks |
| Embeddings | `POST /api/v1/internal/scraper-pipeline/embeddings` | Store embeddings |

Auth: `X-Scraper-Pipeline-Ingest-Token` header, validated against `SCRAPER_API_KEYS`.

## External Dependencies

| Provider | Purpose | Auth | Failure Mode |
|----------|---------|------|-------------|
| Web servers (various) | Content to scrape | None (public web) | Per-URL failure, job continues |
| Supabase (conditional) | Alternative data store | `SUPABASE_SERVICE_KEY` | Feature degradation |
| Modal platform | Compute, queues, secrets | `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` | Complete service outage |
| Render PostgreSQL | Primary data store | `DATABASE_URL` | Complete service outage |

# Architecture: Scraper Worker
> Auto-generated: 2026-05-12

See [diagrams/architecture.md](diagrams/architecture.md) for the component diagram.

## Architectural Style

**Serverless queue-based pipeline** — Python functions deployed on Modal serverless, organized as a 5-stage processing pipeline with Modal queues for inter-stage communication. A secondary FastAPI ASGI app is deployed on both Modal and Render for REST access.

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | ≥3.11 |
| Serverless platform | Modal | ≥0.59.0 |
| Web framework (REST) | FastAPI | Latest |
| Browser automation | Playwright | Latest |
| Crawl engine | Crawl4AI | ≥0.4.0 |
| PDF extraction | Docling | ≥0.4.0 |
| Text processing | LangChain | ≥0.1.0 |
| Tokenization | tiktoken | Latest |
| Embeddings (local) | FastEmbed | Latest |
| Database driver | psycopg2-binary | Latest |
| Validation | Pydantic | ≥2.0 |
| Logging | structlog | Latest |

## Internal Components

### Modal App (`vecinita-scraper`)

Source: `modal-apps/scraper/src/vecinita_scraper/app.py`

The Modal app defines all serverless functions and their configurations.

| Component | Purpose |
|-----------|---------|
| `app.py` | Modal app definition, function decorators, image config |
| `workers/` | Pipeline stage implementations (scraper, processor, chunker, embedder, finalizer) |
| `api/` | FastAPI ASGI application for REST access |
| `config.py` | Environment variable loading, defaults |
| `models/` | Pydantic models for request/response validation |
| `db/` | Database connection management and queries |

### Function Registry

| Function | Module | Type | Purpose |
|----------|--------|------|---------|
| `health_check` | `app.py` | Synchronous | Worker health probe |
| `modal_scrape_job_submit` | `app.py` | Synchronous (300s) | Create scraping job |
| `modal_scrape_job_get` | `app.py` | Synchronous (120s) | Return job status |
| `modal_scrape_job_list` | `app.py` | Synchronous (120s) | List jobs for user |
| `modal_scrape_job_cancel` | `app.py` | Synchronous (120s) | Cancel job |
| `trigger_reindex` | `app.py` | Synchronous (60s) | Kick all pipeline drainers |
| `scraper_worker` | `workers/` | Async worker | Execute scrape for single URL |
| `drain_scrape_queue` | `workers/` | Queue drainer | Pull from scrape-jobs |
| `drain_process_queue` | `workers/` | Queue drainer | Pull from process-jobs |
| `drain_chunk_queue` | `workers/` | Queue drainer | Pull from chunk-jobs |
| `drain_embed_queue` | `workers/` | Queue drainer | Pull from embed-jobs |
| `drain_store_queue` | `workers/` | Queue drainer | Pull from store-jobs |

### Queue Architecture

5 Modal queues provide inter-stage decoupling:

| Queue | Producer | Consumer | Payload |
|-------|----------|----------|---------|
| `scrape-jobs` | `modal_scrape_job_submit` | `drain_scrape_queue` | URL + job config |
| `process-jobs` | `scraper_worker` | `drain_process_queue` | Raw content + metadata |
| `chunk-jobs` | `drain_process_queue` | `drain_chunk_queue` | Document reference |
| `embed-jobs` | `drain_chunk_queue` | `drain_embed_queue` | Chunk references |
| `store-jobs` | `drain_embed_queue` | `drain_store_queue` | Finalization reference |

### FastAPI ASGI App

Source: `modal-apps/scraper/src/vecinita_scraper/api/`

| Component | Purpose |
|-----------|---------|
| `main.py` | FastAPI app creation, middleware, router mounting |
| `routes/` | REST endpoint handlers |
| `middleware.py` | API key validation, CORS, logging |
| `schemas/` | Request/response Pydantic models |

## Concurrency Model

| Concern | Pattern |
|---------|---------|
| Function invocation | Modal auto-scales containers per function |
| Pipeline parallelism | `Function.spawn()` / `spawn_map.aio()` for bounded concurrency |
| Browser sessions | One Playwright browser per `scraper_worker` invocation |
| Queue consumption | Serial within a drainer, parallel across drainer instances |
| Database writes | Per-invocation `psycopg2` connections (no pooling needed in ephemeral containers) |
| Embedding batches | Batch HTTP calls with configurable batch size |

## Container Lifecycle

| Phase | Duration | Notes |
|-------|----------|-------|
| Cold start | 10-20s | Playwright browser initialization dominates |
| Warm invocation | <1s overhead | Container reuse within Modal's keep-alive window |
| Max duration | Function-dependent (60s-300s) | See function registry for per-function timeouts |
| Scale-to-zero | Automatic | Modal deprovisioning when idle |

## Image Configuration

The Modal image is built from `debian_slim` with the following layers:

| Layer | Packages |
|-------|----------|
| System | Chromium dependencies for Playwright |
| Python | crawl4ai, docling, langchain, playwright, psycopg2-binary, tiktoken, structlog, pypdf, fastembed, pydantic, fastapi |
| Browser | Playwright Chromium binary (installed via `playwright install chromium`) |

## Module Dependency Graph

```
app.py (Modal app entry)
├── workers/scraper.py (Stage 1)
│   ├── Playwright + Crawl4AI
│   └── db/ (crawled_urls persistence)
├── workers/processor.py (Stage 2)
│   ├── content extraction
│   └── db/ (documents persistence)
├── workers/chunker.py (Stage 3)
│   ├── tiktoken
│   └── db/ (document_chunks persistence)
├── workers/embedder.py (Stage 4)
│   ├── embedding upstream client
│   └── db/ (chunk_embeddings persistence)
├── workers/finalizer.py (Stage 5)
│   └── db/ (job status finalization)
├── api/ (FastAPI ASGI)
│   ├── routes/
│   ├── middleware.py
│   └── schemas/
├── config.py
├── models/
└── db/
    ├── connection.py
    └── queries.py
```

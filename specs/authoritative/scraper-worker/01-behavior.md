# Behavior: Scraper Worker
> Auto-generated: 2026-05-12

## Purpose

The scraper worker is the **web scraping and content extraction pipeline** for the Vecinita civic/community information RAG system. It accepts scrape job requests, crawls target URLs using Playwright and Crawl4AI, extracts text content, chunks documents, generates embeddings, and persists results to PostgreSQL — all as asynchronous background jobs on Modal serverless.

Source: `modal-apps/scraper/src/vecinita_scraper/app.py`

## Core Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| 1 | Job lifecycle management | Create, track, cancel, and list scraping jobs with status persistence in PostgreSQL |
| 2 | Web scraping execution | Crawl target URLs using Playwright + Crawl4AI with configurable depth and timeouts |
| 3 | Content extraction | Extract text from HTML pages (Crawl4AI) and PDFs (Docling) into structured documents |
| 4 | Document chunking | Split extracted content into token-bounded chunks using configurable size and overlap |
| 5 | Embedding generation | Generate vector embeddings for chunks via upstream embedding service (FastEmbed or Modal) |
| 6 | Pipeline persistence | Write crawled URLs, chunks, and embeddings to `data_mgmt.documents` and related tables |
| 7 | Queue-based orchestration | Route work through 5 Modal queues for bounded concurrency at each pipeline stage |
| 8 | Reindexing | Trigger full pipeline drain across all queues for batch reprocessing |
| 9 | REST API facade | Expose FastAPI endpoints for DM frontend and external callers via Render deployment |

## Key Behaviors

### Job Submission (modal_scrape_job_submit)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `modal_scrape_job_submit.remote(payload)` | Create job record in PostgreSQL, enqueue URL(s) to `scrape-jobs` queue | Job ID returned, status = `queued` |
| Payload includes URL, depth, user_id | Validate URL, set default crawl depth from `CRAWL4AI_MAX_DEPTH` | Job created with configuration |
| Timeout: 300s | If submission exceeds timeout, Modal raises `TimeoutError` | Gateway receives error response |

### Job Status Tracking (modal_scrape_job_get)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `modal_scrape_job_get.remote(job_id)` | Query PostgreSQL for job record and pipeline stage | Job status with `pipeline_stage` field |
| Job not found | Return error/null response | 404-equivalent status |
| Timeout: 120s | Read-only query, typically completes in <1s | Fast response |

### Job Listing (modal_scrape_job_list)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `modal_scrape_job_list.remote(user_id, limit)` | Query PostgreSQL for user's jobs, ordered by creation date | List of job summaries |
| Timeout: 120s | Paginated query with default limit | Bounded result set |

### Job Cancellation (modal_scrape_job_cancel)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `modal_scrape_job_cancel.remote(job_id)` | Update job status to `cancelled` in PostgreSQL | Job marked cancelled |
| In-flight pipeline stages | Subsequent queue drainers skip cancelled jobs | Graceful termination |
| Timeout: 120s | Status update only | Fast response |

### Pipeline Execution (scraper_worker → drain_*_queue)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| `scrape-jobs` queue has entries | `drain_scrape_queue` pulls URLs, spawns `scraper_worker` per URL | Crawled HTML/content placed on `process-jobs` |
| `process-jobs` queue has entries | `drain_process_queue` extracts/normalizes content | Processed documents placed on `chunk-jobs` |
| `chunk-jobs` queue has entries | `drain_chunk_queue` splits into token-bounded chunks | Chunks placed on `embed-jobs` |
| `embed-jobs` queue has entries | `drain_embed_queue` generates embeddings via upstream service | Embeddings placed on `store-jobs` |
| `store-jobs` queue has entries | `drain_store_queue` persists chunks + embeddings to PostgreSQL | Data written to `data_mgmt.documents` |

### Reindexing (trigger_reindex)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `trigger_reindex.spawn(...)` | Kick all 5 queue drainers to process pending items | Pipeline fully drained |
| Fire-and-forget variant | Gateway uses `.spawn()` without `.get()` | No response waited |
| Blocking variant | Gateway uses `.spawn()` then `.get(timeout=60)` | Waits for completion |

### REST API (FastAPI ASGI)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| HTTP request to Render-deployed DM API | FastAPI routes handle CRUD for jobs, document browsing | JSON responses |
| Used by DM frontend | Direct HTTP access without Modal SDK | Standard REST interface |

## Service Boundaries (Does NOT Own)

| Concern | Owned By |
|---------|----------|
| Job orchestration routing (which service to call) | gateway service |
| Embedding model execution | Modal `vecinita-embedding` app |
| LLM inference and RAG retrieval | agent service |
| User authentication and rate limiting | gateway middleware |
| Frontend rendering | data-management-frontend |
| Database schema migrations | shared Alembic/migration tooling |

# User Journeys: Scraper Worker
> Auto-generated: 2026-05-12

See [diagrams/user-journeys.md](diagrams/user-journeys.md) for the journey diagrams.

## Journey 1: Submit and Track a Scrape Job

**Persona:** P2 (DM Frontend User) via P1 (Gateway)
**Goal:** Scrape a website and ingest its content into the knowledge base.

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | DM User | Enter URL in DM frontend, click "Scrape" | Frontend sends POST to gateway |
| 2 | Gateway | `invoke_modal_scrape_job_submit(url, user_id, depth)` | Modal function invoked |
| 3 | Scraper | Create `scraping_jobs` row, enqueue to `scrape-jobs` | Return `{ job_id, status: "queued" }` |
| 4 | Gateway | Return job_id to frontend | Frontend shows "Job submitted" |
| 5 | DM User | Poll job status (refresh or auto-poll) | Frontend sends GET to gateway |
| 6 | Gateway | `invoke_modal_scrape_job_get(job_id)` | Modal function invoked |
| 7 | Scraper | Query `scraping_jobs` for current status | Return `{ status: "scraping", pipeline_stage, pages_scraped }` |
| 8 | Pipeline | `drain_scrape_queue` → `drain_process_queue` → ... → `drain_store_queue` | Each stage updates `pipeline_stage` |
| 9 | Scraper | Final stage completes, set `status = completed` | Job marked complete |
| 10 | DM User | See "Completed" status with page counts | Browse ingested documents |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| URL unreachable | `scraper_worker` gets DNS/connection error | Job continues for other URLs; failed URL logged in `crawled_urls` |
| Timeout on single URL | Playwright timeout exceeds `CRAWL4AI_TIMEOUT_SECONDS` | URL marked `failed`, remaining URLs continue |
| All URLs fail | All `crawled_urls` entries have `status = failed` | Job marked `failed` with aggregate error |
| Modal cold start timeout | Gateway `.remote()` exceeds 300s | Gateway returns 504, user retries |
| Database connection failure | `psycopg2.OperationalError` | Job fails with DB error, operator investigates |
| Embedding service unavailable | HTTP timeout to embedding upstream | `drain_embed_queue` retries; job stalls at `embedding` stage |

## Journey 2: Cancel a Running Job

**Persona:** P2 (DM Frontend User) via P1 (Gateway)
**Goal:** Stop a scrape job that was submitted by mistake or is taking too long.

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | DM User | Click "Cancel" on running job in DM frontend | Frontend sends POST to gateway |
| 2 | Gateway | `invoke_modal_scrape_job_cancel(job_id)` | Modal function invoked |
| 3 | Scraper | Update `scraping_jobs.status = 'cancelled'` | Return updated job record |
| 4 | Pipeline | `drain_*_queue` workers check job status before processing | Skip cancelled job items |
| 5 | DM User | See "Cancelled" status | Job stops consuming resources |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Job already completed | Status is `completed` at cancel time | Return current status, no-op |
| Job not found | Invalid `job_id` | Return 404-equivalent |
| Race condition | Stage completes between cancel and check | Partial data may be persisted; acceptable |

## Journey 3: Trigger Reindex

**Persona:** P3 (System Operator) via P1 (Gateway)
**Goal:** Drain all pipeline queues to ensure pending work is processed.

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Operator | Trigger reindex via gateway API or direct call | Gateway invokes `trigger_reindex` |
| 2 | Gateway (blocking) | `invoke_modal_scraper_reindex()` via `.spawn()` + `.get(timeout=60)` | Wait for result |
| 2-alt | Gateway (fire-and-forget) | `spawn_modal_scraper_reindex()` via `.spawn()` | Return immediately |
| 3 | Scraper | Kick all 5 drain functions | Each drainer processes pending items |
| 4 | Pipeline | Queues drain from `scrape-jobs` through `store-jobs` | All pending data persisted |
| 5 | Operator | Verify via job status queries or Modal dashboard | All jobs at terminal states |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Timeout (>60s) | `.get(timeout=60)` raises `TimeoutError` | Drainers continue in background; operator checks later |
| Queue stuck | Items remain after drain attempt | Operator inspects Modal dashboard for errors |
| Partial drain | Some stages complete, others fail | Rerun `trigger_reindex`; idempotent by design |

## Journey 4: Browse Ingested Documents

**Persona:** P2 (DM Frontend User) via DM API
**Goal:** View documents and chunks that were ingested from a scrape job.

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | DM User | Navigate to "Documents" section in DM frontend | Frontend sends GET to DM API |
| 2 | DM API | Query `documents` table with pagination | Return document list |
| 3 | DM User | Click on a document | Frontend sends GET for document detail |
| 4 | DM API | Query `document_chunks` for that document | Return chunks with metadata |
| 5 | DM User | Review content quality and chunk breakdown | Assess scrape quality |

## Journey 5: Debug a Failed Job

**Persona:** P3 (System Operator)
**Goal:** Investigate why a scrape job failed and determine corrective action.

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Operator | Query failed jobs via API or direct DB query | List of jobs with `status = failed` |
| 2 | Operator | Check `error_message` and `pipeline_stage` on job | Identify failure stage |
| 3 | Operator | Query `crawled_urls` for the job | See per-URL success/failure breakdown |
| 4 | Operator | Check Modal function logs for the failed invocation | Detailed error traces |
| 5 | Operator | Fix root cause (URL, network, config) and resubmit | New job succeeds |

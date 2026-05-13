# Data Flow: Scraper Worker
> Auto-generated: 2026-05-12

See [diagrams/data-flow.md](diagrams/data-flow.md) for the pipeline flow diagram.

## Overview

The scraper worker implements a **5-stage queue-based pipeline** that transforms URLs into indexed, searchable document chunks with embeddings. Each stage is decoupled via Modal queues, enabling bounded concurrency and independent scaling.

## Pipeline Stages

```
URL submission → [scrape-jobs] → scraper_worker → [process-jobs] → processor
  → [chunk-jobs] → chunker → [embed-jobs] → embedder → [store-jobs] → finalizer
```

### Stage 1: Scrape (scrape-jobs queue)

| Property | Value |
|----------|-------|
| Queue | `scrape-jobs` |
| Worker | `scraper_worker` |
| Input | `{ job_id, url, depth, timeout }` |
| Output | Raw HTML/text content per URL |
| Concurrency | Bounded by `Function.spawn` / `spawn_map.aio` |
| Persistence | `crawled_urls` rows (one per URL) |

**Processing:**
1. Pull URL from `scrape-jobs` queue
2. Launch Playwright browser (Chromium, headless)
3. Navigate to URL, wait for JavaScript rendering
4. Extract content via Crawl4AI (HTML) or Docling (PDF)
5. Store raw content in `crawled_urls.raw_content`
6. Store extracted text in `crawled_urls.extracted_text`
7. If `depth > 0`, discover linked URLs and enqueue children (up to `CRAWL4AI_MAX_DEPTH`)
8. Enqueue extracted content to `process-jobs` queue
9. Update `scraping_jobs.pipeline_stage = 'scraping'`, increment `pages_scraped`

### Stage 2: Process (process-jobs queue)

| Property | Value |
|----------|-------|
| Queue | `process-jobs` |
| Worker | `drain_process_queue` |
| Input | Raw extracted content from Stage 1 |
| Output | Cleaned, normalized document content |
| Persistence | `documents` rows |

**Processing:**
1. Pull content from `process-jobs` queue
2. Clean HTML artifacts, normalize whitespace
3. Extract metadata (title, content type, source URL)
4. Create `documents` record with full content
5. Enqueue document reference to `chunk-jobs` queue
6. Update `scraping_jobs.pipeline_stage = 'processing'`

### Stage 3: Chunk (chunk-jobs queue)

| Property | Value |
|----------|-------|
| Queue | `chunk-jobs` |
| Worker | `drain_chunk_queue` |
| Input | Document content from Stage 2 |
| Output | Token-bounded text chunks |
| Persistence | `document_chunks` rows |

**Processing:**
1. Pull document from `chunk-jobs` queue
2. Tokenize content using `tiktoken` (`cl100k_base` encoding)
3. Split into chunks respecting:
   - Max size: `CHUNK_MAX_SIZE_TOKENS` (default 1024)
   - Min size: `CHUNK_MIN_SIZE_TOKENS` (default 256)
   - Overlap: `CHUNK_OVERLAP_RATIO` (default 0.2)
4. Prefer sentence/paragraph boundaries for split points
5. Create `document_chunks` records with `chunk_index` ordering
6. Enqueue chunk references to `embed-jobs` queue
7. Update `scraping_jobs.pipeline_stage = 'chunking'`

### Stage 4: Embed (embed-jobs queue)

| Property | Value |
|----------|-------|
| Queue | `embed-jobs` |
| Worker | `drain_embed_queue` |
| Input | Text chunks from Stage 3 |
| Output | Vector embeddings (384-dimensional) |
| Persistence | `chunk_embeddings` rows |

**Processing:**
1. Pull chunk batch from `embed-jobs` queue
2. Batch chunks for embedding (typically 32-64 per call)
3. Send to embedding upstream (`EMBEDDING_UPSTREAM_URL` or Modal `vecinita-embedding`)
4. Receive embedding vectors
5. Create `chunk_embeddings` records (1:1 with chunks)
6. Enqueue references to `store-jobs` queue
7. Update `scraping_jobs.pipeline_stage = 'embedding'`

### Stage 5: Store (store-jobs queue)

| Property | Value |
|----------|-------|
| Queue | `store-jobs` |
| Worker | `drain_store_queue` |
| Input | Finalization references from Stage 4 |
| Output | Updated job status |
| Persistence | Final `scraping_jobs` status update |

**Processing:**
1. Pull finalization entry from `store-jobs` queue
2. Verify all chunks and embeddings are persisted
3. Update `scraping_jobs.status = 'completed'`
4. Set `scraping_jobs.completed_at = now()`
5. Update final `pages_scraped` / `pages_failed` counts

## Data Transformation Summary

| Stage | Input Format | Output Format | Size Change |
|-------|-------------|---------------|-------------|
| Scrape | URL string | HTML/text (KB-MB) | 1 URL → 1+ pages |
| Process | Raw HTML/text | Cleaned text | ~50-70% of raw |
| Chunk | Full document text | 256-1024 token chunks | 1 doc → N chunks |
| Embed | Text chunk | 384-dim float vector | ~1KB per chunk → ~1.5KB |
| Store | References | Status update | Metadata only |

## Data Entry Points

| Entry Point | Source | Format | Trigger |
|-------------|--------|--------|---------|
| Modal SDK invocation | Gateway service | Python function args | User submits scrape via frontend |
| REST API | DM Frontend | HTTP JSON | Direct API call |
| Reindex trigger | Gateway / Operator | `.spawn()` call | Manual or automated reindex |

## Data Exit Points

| Exit Point | Destination | Format | Consumer |
|------------|-------------|--------|----------|
| `scraping_jobs` | PostgreSQL | SQL rows | Gateway (status), DM frontend (browse) |
| `crawled_urls` | PostgreSQL | SQL rows | DM frontend (browse crawled pages) |
| `documents` | PostgreSQL | SQL rows | Agent (RAG), gateway (corpus) |
| `document_chunks` | PostgreSQL | SQL rows | Agent (similarity search) |
| `chunk_embeddings` | PostgreSQL | SQL rows + vectors | Agent (vector similarity) |
| Pipeline callbacks | Gateway REST | HTTP JSON | Gateway persistence (optional) |

## Data Retention

| Data | Retention Policy | Notes |
|------|-----------------|-------|
| `scraping_jobs` | Indefinite | Job history for audit trail |
| `crawled_urls` | Indefinite | Raw content may be pruned in future |
| `documents` | Indefinite | Core knowledge base content |
| `document_chunks` | Indefinite | Required for RAG retrieval |
| `chunk_embeddings` | Until re-embedding | Re-generated if embedding model changes |

## Failure and Recovery

| Stage Failure | Impact | Recovery |
|--------------|--------|----------|
| Stage 1 (scrape) | Individual URL fails | Other URLs continue; `crawled_urls.status = 'failed'` |
| Stage 2 (process) | Document extraction fails | Job continues with other docs; error logged |
| Stage 3 (chunk) | Chunking fails | Rare (text-only operation); logged |
| Stage 4 (embed) | Embedding service down | Items remain in `embed-jobs` queue; retry on next drain |
| Stage 5 (store) | DB write fails | Items remain in `store-jobs` queue; retry on next drain |
| Full pipeline | All stages backed up | `trigger_reindex` drains all queues |

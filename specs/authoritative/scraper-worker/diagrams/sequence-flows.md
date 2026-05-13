# Scraper Worker — Sequence Flow Diagrams
> Auto-generated: 2026-05-12

## Job Submission Flow

```mermaid
sequenceDiagram
    participant DMFE as DM Frontend
    participant GW as Gateway
    participant SW as Scraper Worker
    participant DB as PostgreSQL
    participant Q as Modal Queue

    DMFE->>GW: POST /api/v1/modal-jobs/scraper
    GW->>SW: modal_scrape_job_submit.remote(url, user_id, options)
    SW->>DB: INSERT scraping_job (status=pending)
    SW->>Q: scrape-jobs.put(job_id, url)
    SW-->>GW: {job_id, status: "pending"}
    GW-->>DMFE: 201 {job_id}
```

## Five-Stage Pipeline Execution

```mermaid
sequenceDiagram
    participant SQ as scrape-jobs Queue
    participant SW as scraper_worker
    participant PQ as process-jobs Queue
    participant Proc as Processor
    participant CQ as chunk-jobs Queue
    participant Chunk as Chunker
    participant EQ as embed-jobs Queue
    participant Embed as Embedder
    participant StQ as store-jobs Queue
    participant Store as Finalizer
    participant DB as PostgreSQL

    Note over SQ,DB: Stage 1 — Scrape
    SQ->>SW: drain_scrape_queue pulls job
    SW->>SW: Crawl4AI fetch URL + extract content
    SW->>DB: INSERT crawled_url (raw HTML + extracted text)
    SW->>PQ: process-jobs.put(crawled_url_id)

    Note over PQ,DB: Stage 2 — Process
    PQ->>Proc: drain_process_queue pulls item
    Proc->>Proc: Clean, normalize, extract metadata
    Proc->>DB: UPDATE crawled_url (processed content)
    Proc->>CQ: chunk-jobs.put(crawled_url_id)

    Note over CQ,DB: Stage 3 — Chunk
    CQ->>Chunk: drain_chunk_queue pulls item
    Chunk->>Chunk: Split text (tiktoken, max/min/overlap)
    Chunk->>DB: INSERT document_chunks[]
    Chunk->>EQ: embed-jobs.put(chunk_ids[])

    Note over EQ,DB: Stage 4 — Embed
    EQ->>Embed: drain_embed_queue pulls item
    Embed->>Embed: Generate embeddings (fastembed / upstream)
    Embed->>DB: UPDATE chunks with embedding vectors
    Embed->>StQ: store-jobs.put(chunk_ids[])

    Note over StQ,DB: Stage 5 — Store / Finalize
    StQ->>Store: drain_store_queue pulls item
    Store->>DB: UPDATE scraping_job (status=complete, stats)
    Store->>DB: INSERT/UPDATE agent.vectors
```

## Job Status Query

```mermaid
sequenceDiagram
    participant Client as DM Frontend
    participant GW as Gateway
    participant SW as Scraper Worker
    participant DB as PostgreSQL

    Client->>GW: GET /api/v1/modal-jobs/scraper/{job_id}
    alt Gateway-owned persistence
        GW->>DB: SELECT FROM gateway.scraping_jobs
        DB-->>GW: job record
    else Modal direct
        GW->>SW: modal_scrape_job_get.remote(job_id)
        SW->>DB: SELECT FROM scraping_jobs
        DB-->>SW: job record
        SW-->>GW: job status
    end
    GW-->>Client: {job_id, status, pipeline_stage, stats}
```

## Job Cancellation

```mermaid
sequenceDiagram
    participant Client as DM Frontend
    participant GW as Gateway
    participant SW as Scraper Worker
    participant DB as PostgreSQL

    Client->>GW: POST /api/v1/modal-jobs/scraper/{job_id}/cancel
    GW->>SW: modal_scrape_job_cancel.remote(job_id)
    SW->>DB: UPDATE scraping_job SET status='cancelled'
    SW-->>GW: {job_id, status: "cancelled"}
    GW-->>Client: 200 {status: "cancelled"}
```

## Reindex Trigger (Fire-and-Forget)

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant SW as Scraper Worker
    participant Q1 as scrape-jobs
    participant Q2 as process-jobs
    participant Q3 as chunk-jobs
    participant Q4 as embed-jobs
    participant Q5 as store-jobs

    GW->>SW: trigger_reindex.spawn() (fire-and-forget)
    activate SW
    SW->>Q1: drain_scrape_queue.spawn()
    SW->>Q2: drain_process_queue.spawn()
    SW->>Q3: drain_chunk_queue.spawn()
    SW->>Q4: drain_embed_queue.spawn()
    SW->>Q5: drain_store_queue.spawn()
    Note over SW,Q5: All drain functions run concurrently
    deactivate SW
```

## Health Check

```mermaid
sequenceDiagram
    participant Monitor as Monitoring
    participant SW as Scraper Worker
    participant DB as PostgreSQL

    Monitor->>SW: health_check.remote()
    SW->>DB: SELECT 1 (connection test)
    DB-->>SW: OK
    SW-->>Monitor: {status: "healthy", db: "connected", queues: {lengths}}
```

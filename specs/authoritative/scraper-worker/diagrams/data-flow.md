# Data Flow Diagram: Scraper Worker
> Auto-generated: 2026-05-12

## 5-Stage Pipeline Flow

```mermaid
flowchart TD
    subgraph "Input"
        URL[URL + Config]
        GW[Gateway .remote call]
    end

    subgraph "Stage 1 — Scrape"
        Q1[(scrape-jobs<br/>queue)]
        SW[scraper_worker<br/>Playwright + Crawl4AI]
        CU[(crawled_urls<br/>table)]
    end

    subgraph "Stage 2 — Process"
        Q2[(process-jobs<br/>queue)]
        PROC[drain_process_queue<br/>Content extraction]
        DOC[(documents<br/>table)]
    end

    subgraph "Stage 3 — Chunk"
        Q3[(chunk-jobs<br/>queue)]
        CHUNK[drain_chunk_queue<br/>tiktoken splitting]
        DC[(document_chunks<br/>table)]
    end

    subgraph "Stage 4 — Embed"
        Q4[(embed-jobs<br/>queue)]
        EMBED[drain_embed_queue<br/>Embedding upstream]
        CE[(chunk_embeddings<br/>table)]
    end

    subgraph "Stage 5 — Store"
        Q5[(store-jobs<br/>queue)]
        STORE[drain_store_queue<br/>Finalization]
        SJ[(scraping_jobs<br/>status: completed)]
    end

    GW -->|submit job| URL
    URL -->|enqueue| Q1
    Q1 -->|pull| SW
    SW -->|crawl web| WEB((Web))
    SW -->|write| CU
    SW -->|enqueue| Q2

    Q2 -->|pull| PROC
    PROC -->|clean + extract| DOC
    PROC -->|enqueue| Q3

    Q3 -->|pull| CHUNK
    CHUNK -->|split by tokens| DC
    CHUNK -->|enqueue| Q4

    Q4 -->|pull| EMBED
    EMBED -->|batch call| EMB((Embedding<br/>Service))
    EMBED -->|write| CE
    EMBED -->|enqueue| Q5

    Q5 -->|pull| STORE
    STORE -->|finalize| SJ
```

## Data Transformation Detail

```mermaid
flowchart LR
    subgraph "Raw Input"
        A1[URL string<br/>~100 bytes]
    end

    subgraph "Stage 1 Output"
        B1[HTML/text content<br/>10KB - 5MB per page]
    end

    subgraph "Stage 2 Output"
        C1[Cleaned text<br/>50-70% of raw]
    end

    subgraph "Stage 3 Output"
        D1[Token-bounded chunks<br/>256-1024 tokens each<br/>N chunks per document]
    end

    subgraph "Stage 4 Output"
        E1[384-dim float vectors<br/>~1.5KB per embedding]
    end

    subgraph "Stage 5 Output"
        F1[Status update<br/>metadata only]
    end

    A1 --> B1
    B1 --> C1
    C1 --> D1
    D1 --> E1
    E1 --> F1
```

## Job Status State Machine

```mermaid
stateDiagram-v2
    [*] --> queued: Job created
    queued --> scraping: drain_scrape_queue picks up
    scraping --> processing: All URLs scraped
    processing --> chunking: Content extracted
    chunking --> embedding: Chunks created
    embedding --> storing: Embeddings generated
    storing --> completed: Finalization done

    queued --> cancelled: User cancels
    scraping --> cancelled: User cancels
    processing --> cancelled: User cancels
    chunking --> cancelled: User cancels
    embedding --> cancelled: User cancels

    scraping --> failed: All URLs fail
    processing --> failed: Extraction error
    chunking --> failed: Chunking error
    embedding --> failed: Embedding service down
    storing --> failed: DB write error

    completed --> [*]
    cancelled --> [*]
    failed --> [*]
```

## Data Volume Estimates

```mermaid
flowchart LR
    subgraph "Per Job (1 URL, depth=1)"
        A[1 URL] -->|crawl| B[5-20 pages]
        B -->|extract| C[5-20 documents]
        C -->|chunk| D[50-200 chunks]
        D -->|embed| E[50-200 embeddings]
    end
```

| Metric | Per Page | Per Job (avg) |
|--------|----------|--------------|
| Raw HTML | 50-500 KB | 500 KB - 5 MB |
| Extracted text | 5-50 KB | 50 KB - 500 KB |
| Chunks | 5-20 | 50-200 |
| Embeddings | 5-20 | 50-200 |
| DB storage | ~10 KB | ~100 KB - 1 MB |

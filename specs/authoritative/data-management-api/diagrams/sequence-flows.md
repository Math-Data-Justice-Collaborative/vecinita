# Data Management API — Sequence Flow Diagrams

> Auto-generated: 2026-05-12

## Job Submission Flow

```mermaid
sequenceDiagram
    participant SPA as DM Frontend
    participant DM as DM API
    participant SC as ScraperClient
    participant Scraper as Scraper Service
    participant DB as PostgreSQL

    SPA->>DM: POST /jobs (Bearer token, ScrapeJobRequest)
    DM->>SC: forward_jobs("POST", "", body, headers)
    SC->>Scraper: POST /jobs (forwarded)
    Scraper->>DB: INSERT INTO scraping_jobs
    DB-->>Scraper: job_id
    Scraper-->>SC: 201 ScrapeJobCreatedResponse
    SC-->>DM: httpx.Response
    DM->>DM: Enrich with source_of_truth metadata
    DM-->>SPA: 201 JSON (enriched)
```

## Job Status Polling Flow

```mermaid
sequenceDiagram
    participant SPA as DM Frontend
    participant DM as DM API
    participant SC as ScraperClient
    participant Scraper as Scraper Service
    participant DB as PostgreSQL

    SPA->>DM: GET /jobs/{job_id} (Bearer token)
    DM->>SC: forward_jobs("GET", job_id)
    SC->>Scraper: GET /jobs/{job_id}
    Scraper->>DB: SELECT with aggregate counts
    DB-->>Scraper: JobStatusResponse
    Scraper-->>SC: 200 JSON
    SC-->>DM: httpx.Response
    DM-->>SPA: 200 JSON (passthrough)
```

## Embed Flow (Modal SDK Path)

```mermaid
sequenceDiagram
    participant Client as SPA / Caller
    participant DM as DM API
    participant EC as EmbeddingClient
    participant MI as modal_invoker
    participant Modal as Modal embed_query

    Client->>DM: POST /embed {text, model_version}
    DM->>EC: embed(text, model_version)
    EC->>MI: modal_function_invocation_enabled?
    MI-->>EC: true
    EC->>MI: embedding_embed_single_modal(text, model_version)
    MI->>MI: asyncio.to_thread(sync call)
    MI->>Modal: Function.from_name("vecinita-embedding", "embed_query").remote(text)
    Modal-->>MI: {embedding, model_version}
    MI-->>EC: raw dict
    EC->>EC: EmbedResponse.model_validate(raw)
    EC-->>DM: EmbedResponse
    DM->>DM: Enrich metadata (source_of_truth)
    DM-->>Client: 200 EmbedResponse
```

## Embed Flow (HTTP Path)

```mermaid
sequenceDiagram
    participant Client as SPA / Caller
    participant DM as DM API
    participant EC as EmbeddingClient
    participant Upstream as Embedding Service

    Client->>DM: POST /embed {text, model_version}
    DM->>EC: embed(text, model_version)
    EC->>EC: modal_function_invocation_enabled? → false
    EC->>Upstream: POST EMBEDDING_SERVICE_BASE_URL/embed
    Upstream-->>EC: 200 {embedding, model_version}
    EC->>EC: EmbedResponse.model_validate(json)
    EC-->>DM: EmbedResponse
    DM-->>Client: 200 EmbedResponse
```

## Health Check Flow

```mermaid
sequenceDiagram
    participant Probe as Render / Client
    participant DM as DM API
    participant Guard as corpus_db_guard
    participant SC as ScraperClient
    participant Scraper as Scraper Service

    Probe->>DM: GET /health
    DM->>Guard: validate_canonical_database_url()
    Guard-->>DM: OK (or RuntimeError)
    DM->>SC: health()
    alt Modal enabled
        SC->>SC: modal_invoker.scraper_health_modal()
    else HTTP
        SC->>Scraper: GET /health
        Scraper-->>SC: {status: "ok"}
    end
    SC-->>DM: health dict
    DM-->>Probe: 200 {status: "ok", service: "vecinita-scraper"}
```

## Error Flow — Scraper Unreachable

```mermaid
sequenceDiagram
    participant SPA as DM Frontend
    participant DM as DM API
    participant SC as ScraperClient

    SPA->>DM: POST /jobs (Bearer token, body)
    DM->>SC: forward_jobs("POST", "", body)
    SC->>SC: httpx.RequestError (connection refused)
    SC-->>DM: ScraperUpstreamError(503)
    DM-->>SPA: 503 "Scraper service unreachable"
```

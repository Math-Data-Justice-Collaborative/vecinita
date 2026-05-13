# Data Flow Diagrams: Gateway
> Auto-generated: 2026-05-12

## Q&A Request Flow

```mermaid
flowchart LR
    A[Chat Frontend] -->|GET /ask/stream| B[Gateway]
    B -->|Validate auth| B
    B -->|Rate limit check| B
    B -->|Assign correlation ID| B
    B -->|Forward params| C[Agent /ask-stream]
    C -->|SSE events| B
    B -->|Raw byte forward| A
```

## Scrape Job Flow

```mermaid
flowchart TD
    A[Data Mgmt UI] -->|POST /modal-jobs/scraper| B[Gateway]
    B -->|Check dedup| DB[(Postgres)]
    B -->|Create job row| DB
    B -->|invoke_modal_scrape_job_submit| C[Modal scraper_worker]
    B -->|spawn trigger_reindex| D[Modal drain workers]

    C -->|POST /internal/scraper-pipeline/jobs/status| B
    C -->|POST /internal/scraper-pipeline/crawled-urls| B
    C -->|POST /internal/scraper-pipeline/chunks| B
    C -->|POST /internal/scraper-pipeline/embeddings| B
    B -->|UPDATE scraping_jobs| DB

    A -->|GET /modal-jobs/scraper/{id}| B
    B -->|SELECT scraping_jobs| DB
    B -->|Return status + pipeline_stage| A
```

## Embedding Flow

```mermaid
flowchart LR
    A[Client] -->|POST /embed| B[Gateway]
    B -->|modal_function_invocation?| C{Mode?}
    C -->|Modal SDK| D[Modal embed_query]
    C -->|HTTP| E[Embedding Service]
    D -->|dict result| B
    E -->|JSON response| B
    B -->|EmbedResponse| A
```

## Documents Read Flow

```mermaid
flowchart LR
    A[Frontend] -->|GET /documents/overview| B[Gateway]
    B -->|psycopg2.connect| C[(Postgres)]
    C -->|SELECT sources| B
    C -->|SELECT document_chunks| B
    B -->|Normalize + merge| B
    B -->|Filter test artifacts| B
    B -->|DocumentsOverviewResponse| A
```

## Health Probe Flow

```mermaid
flowchart TD
    A[Operator / Render] -->|GET /health| B[Gateway]
    B -->|Parallel probes| C[Agent HTTP /health]
    B -->|Parallel probes| D[Postgres TCP socket]
    C -->|ok / error| B
    D -->|ok / error| B
    B -->|HealthCheck JSON| A
```

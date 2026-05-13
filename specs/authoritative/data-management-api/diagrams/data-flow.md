# Data Management API — Data Flow Diagram

> Auto-generated: 2026-05-12

## Primary Data Flow — Job Proxy

```mermaid
flowchart LR
    SPA[DM SPA] -->|POST /jobs<br/>Bearer token| DM[DM API]
    DM -->|forward_jobs| SCR[Scraper Service]
    SCR -->|INSERT| DB[(PostgreSQL)]
    SCR -->|201 Created| DM
    DM -->|enrich metadata<br/>source_of_truth| SPA
```

## Embed Flow

```mermaid
flowchart LR
    Client[SPA / Caller] -->|POST /embed<br/>text, model_version| DM[DM API]
    DM -->|MODAL_FUNCTION_INVOCATION?| Check{Modal<br/>enabled?}
    Check -->|yes| Modal[Modal SDK<br/>embed_query]
    Check -->|no| HTTP[HTTP<br/>EMBEDDING_SERVICE_BASE_URL/embed]
    Modal -->|EmbedResponse| DM
    HTTP -->|EmbedResponse| DM
    DM -->|enrich metadata| Client
```

## Predict Flow

```mermaid
flowchart LR
    Client[SPA / Caller] -->|POST /predict<br/>text, model_version| DM[DM API]
    DM -->|MODAL_FUNCTION_INVOCATION?| Check{Modal<br/>enabled?}
    Check -->|yes| Modal[Modal SDK<br/>predict]
    Check -->|no| HTTP[HTTP<br/>MODEL_SERVICE_BASE_URL/predict]
    Modal -->|PredictResponse| DM
    HTTP -->|PredictResponse| DM
    DM --> Client
```

## Health Check Flow

```mermaid
flowchart TD
    Probe[Render / Client] -->|GET /health| DM[DM API]
    DM --> Guard{DATABASE_URL<br/>valid?}
    Guard -->|no| Fail[RuntimeError]
    Guard -->|yes| Scraper{Scraper<br/>health}
    Scraper -->|Modal| ModalHealth[Modal health_check]
    Scraper -->|HTTP| HTTPHealth[GET /health]
    ModalHealth --> OK[200 OK]
    HTTPHealth --> OK
```

## Scraper Pipeline Data Flow (upstream context)

```mermaid
flowchart TD
    Submit[POST /jobs] --> Job[scraping_jobs]
    Job --> Crawl[Crawl URLs]
    Crawl --> CrawledURLs[crawled_urls]
    CrawledURLs --> Extract[Extract Content]
    Extract --> ExtContent[extracted_content]
    ExtContent --> Process[Docling Processing]
    Process --> ProcDocs[processed_documents]
    ProcDocs --> Chunk[Semantic Chunking]
    Chunk --> Chunks[chunks]
    Chunks --> Embed[Embedding]
    Embed --> Embeddings[embeddings]
```

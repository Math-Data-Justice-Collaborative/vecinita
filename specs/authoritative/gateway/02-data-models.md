# Data Models: Gateway
> Auto-generated: 2026-05-12

## Database Tables (gateway-owned)

The gateway reads and writes tables in the `public` schema of the shared Render Postgres instance. Gateway-managed persistence is activated by `MODAL_SCRAPER_PERSIST_VIA_GATEWAY=true`.

Source: `apis/gateway/src/services/ingestion/modal_scraper_persist.py`, `apis/gateway/src/services/ingestion/modal_scraper_pipeline_persist.py`

### scraping_jobs

Job tracking for Modal scrape operations, persisted by the gateway when it owns the scraper control plane.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen | Job identifier |
| url | TEXT | NOT NULL | Target URL to scrape |
| user_id | TEXT | NOT NULL | Submitting user |
| status | TEXT | NOT NULL | `queued`, `running`, `completed`, `failed`, `cancelled`, `duplicate_skipped` |
| crawl_config | JSONB | nullable | Crawl depth, max pages, etc. |
| chunking_config | JSONB | nullable | Chunk size, overlap settings |
| metadata | JSONB | nullable | Correlation ID, pipeline stage, error category |
| error_message | TEXT | nullable | Failure detail |
| created_at | TIMESTAMPTZ | NOT NULL, default now | Job creation time |
| updated_at | TIMESTAMPTZ | NOT NULL, default now | Last status change |

### crawled_urls (pipeline persist)

Individual URLs crawled within a scrape job, used by the internal pipeline ingest API.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | PK |
| job_id | UUID | FK → scraping_jobs |
| url | TEXT | Crawled page URL |
| raw_content | TEXT | Raw HTML/content |
| content_hash | TEXT | Deduplication hash |
| status | TEXT | `success` / `error` |
| error_message | TEXT | Failure detail |

### extracted_content, processed_documents, document_chunks (pipeline persist)

Pipeline stages stored by the internal scraper-pipeline ingest endpoints. These hold intermediate results from Modal scraper workers writing back to the Render gateway.

## Read-only Tables (not gateway-owned)

The documents router reads from these `public` schema tables:

| Table | Owner | Gateway Access | Source |
|-------|-------|---------------|--------|
| `document_chunks` | scraper/agent | SELECT (overview, preview, tags, chunk stats) | `router_documents.py` |
| `sources` | scraper/agent | SELECT (overview, download URL) | `router_documents.py` |

## Pydantic Models

Source: `apis/gateway/src/api/models/`

### Request Models

| Model | Router | Fields |
|-------|--------|--------|
| `GatewayAskQueryParams` | ask | question, thread_id, lang, provider, model, tags, tag_match_mode, rerank, rerank_top_k |
| `ScrapeRequest` | scrape | urls: list[str], force_loader: LoaderType, stream: bool |
| `EmbedRequest` | embed | text: str, model: str (optional) |
| `EmbedBatchRequest` | embed | texts: list[str], model: str (optional) |
| `SimilarityRequest` | embed | text1, text2, model (optional) |
| `GatewayModalScrapeSubmitRequest` | modal-jobs | url: HttpUrl, user_id, crawl_config, chunking_config, metadata |
| `UpdateJobStatusBody` | scraper-pipeline | status, error_message, pipeline_stage, error_category |

### Response Models

| Model | Router | Key Fields |
|-------|--------|------------|
| `AskResponse` | ask | question, answer, sources: list[SourceCitation], language, model, response_time_ms, token_usage |
| `HealthCheck` | health | status, agent_service, embedding_service, database, timestamp |
| `IntegrationsStatus` | health | status, gateway, components: dict, active/degraded_integrations |
| `EmbedResponse` | embed | text, embedding: list[float], model, dimension |
| `ScrapeResponse` | scrape | job_id, status, message |
| `GatewayModalScrapeJobBody` | modal-jobs | job_id, status, pipeline_stage, error_category, correlation_id, timestamps |
| `DocumentsOverviewResponse` | documents | total_chunks, unique_sources, avg_chunk_size, embedding_model, sources |
| `DocumentsPreviewResponse` | documents | source_url, chunks: list[DocumentsPreviewChunk] |
| `DocumentsTagsResponse` | documents | tags, tag_counts, locale, total |

See [diagrams/data-models.md](diagrams/data-models.md) for the ER diagram.

# Data Models: Scraper Worker
> Auto-generated: 2026-05-12

See [diagrams/data-models.md](diagrams/data-models.md) for the ER diagram.

## Overview

The scraper worker owns the write path for scraping job lifecycle and document ingestion. It writes to tables in the `public` and `data_mgmt` schemas of the shared Render PostgreSQL database.

Source: `modal-apps/scraper/src/vecinita_scraper/`

## Core Entities

### scraping_jobs

Tracks the lifecycle of each scraping request.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Job identifier |
| `user_id` | `VARCHAR(255)` | NOT NULL | Requesting user/system ID |
| `url` | `TEXT` | NOT NULL | Target URL to scrape |
| `status` | `VARCHAR(50)` | NOT NULL, default `queued` | `queued`, `scraping`, `processing`, `chunking`, `embedding`, `storing`, `completed`, `failed`, `cancelled` |
| `pipeline_stage` | `VARCHAR(50)` | | Current stage in the 5-stage pipeline |
| `max_depth` | `INTEGER` | default 3 | Max crawl depth (recursive scraping) |
| `timeout_seconds` | `INTEGER` | default 60 | Per-URL crawl timeout |
| `pages_scraped` | `INTEGER` | default 0 | Count of successfully scraped pages |
| `pages_failed` | `INTEGER` | default 0 | Count of failed page scrapes |
| `error_message` | `TEXT` | | Last error message if `status = failed` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Job creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Last status update |
| `completed_at` | `TIMESTAMPTZ` | | Pipeline completion timestamp |
| `metadata` | `JSONB` | default `{}` | Extensible metadata (crawl config, tags) |

Indexes: `idx_scraping_jobs_user_id`, `idx_scraping_jobs_status`, `idx_scraping_jobs_created_at`

### crawled_urls

Stores per-URL results during the scrape stage.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Crawled URL identifier |
| `job_id` | `UUID` | FK → `scraping_jobs.id`, NOT NULL | Parent job |
| `url` | `TEXT` | NOT NULL | Actual URL crawled |
| `status` | `VARCHAR(50)` | NOT NULL | `pending`, `scraped`, `failed`, `skipped` |
| `http_status` | `INTEGER` | | HTTP response code |
| `content_type` | `VARCHAR(255)` | | Response content type |
| `raw_content` | `TEXT` | | Raw HTML/text content |
| `extracted_text` | `TEXT` | | Cleaned/extracted text |
| `title` | `TEXT` | | Page title |
| `depth` | `INTEGER` | default 0 | Crawl depth from root URL |
| `parent_url` | `TEXT` | | URL that linked to this page |
| `error_message` | `TEXT` | | Error details if failed |
| `scraped_at` | `TIMESTAMPTZ` | | Scrape completion time |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Record creation |

Indexes: `idx_crawled_urls_job_id`, `idx_crawled_urls_url`

### documents (data_mgmt.documents)

Final document records written at the end of the pipeline.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Document identifier |
| `job_id` | `UUID` | FK → `scraping_jobs.id` | Originating scrape job |
| `source_url` | `TEXT` | NOT NULL | Source URL |
| `title` | `TEXT` | | Document title |
| `content` | `TEXT` | NOT NULL | Full extracted text content |
| `content_type` | `VARCHAR(50)` | | `html`, `pdf`, `text` |
| `metadata` | `JSONB` | default `{}` | Source metadata, tags |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Ingestion timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Last update |

### document_chunks

Token-bounded chunks of documents for RAG retrieval.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Chunk identifier |
| `document_id` | `UUID` | FK → `documents.id`, NOT NULL | Parent document |
| `job_id` | `UUID` | FK → `scraping_jobs.id` | Originating job |
| `chunk_index` | `INTEGER` | NOT NULL | Position within document |
| `content` | `TEXT` | NOT NULL | Chunk text content |
| `token_count` | `INTEGER` | | Token count (tiktoken) |
| `metadata` | `JSONB` | default `{}` | Chunk-level metadata |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Creation timestamp |

Indexes: `idx_document_chunks_document_id`, `idx_document_chunks_job_id`

### chunk_embeddings

Vector embeddings for document chunks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Embedding identifier |
| `chunk_id` | `UUID` | FK → `document_chunks.id`, NOT NULL, UNIQUE | Parent chunk (1:1) |
| `embedding` | `VECTOR(384)` | NOT NULL | Embedding vector (model-dependent dimension) |
| `model_name` | `VARCHAR(255)` | NOT NULL | Embedding model used |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Generation timestamp |

Indexes: `idx_chunk_embeddings_chunk_id`, HNSW/IVFFlat index on `embedding` column for similarity search.

## Entity Relationships

| Relationship | Cardinality | FK |
|-------------|-------------|-----|
| `scraping_jobs` → `crawled_urls` | 1:N | `crawled_urls.job_id` → `scraping_jobs.id` |
| `scraping_jobs` → `documents` | 1:N | `documents.job_id` → `scraping_jobs.id` |
| `documents` → `document_chunks` | 1:N | `document_chunks.document_id` → `documents.id` |
| `document_chunks` → `chunk_embeddings` | 1:1 | `chunk_embeddings.chunk_id` → `document_chunks.id` |
| `scraping_jobs` → `document_chunks` | 1:N | `document_chunks.job_id` → `scraping_jobs.id` (denormalized) |

## Pydantic Models (API Layer)

### ScrapeJobRequest

```python
class ScrapeJobRequest(BaseModel):
    url: str
    user_id: str
    max_depth: int = 3
    timeout_seconds: int = 60
    metadata: dict = {}
```

### ScrapeJobResponse

```python
class ScrapeJobResponse(BaseModel):
    id: UUID
    user_id: str
    url: str
    status: str
    pipeline_stage: str | None
    pages_scraped: int
    pages_failed: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
```

### ScrapeJobListResponse

```python
class ScrapeJobListResponse(BaseModel):
    jobs: list[ScrapeJobResponse]
    total: int
```

## Chunking Configuration

Controlled by environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CHUNK_MAX_SIZE_TOKENS` | 1024 | Maximum tokens per chunk |
| `CHUNK_MIN_SIZE_TOKENS` | 256 | Minimum tokens per chunk (merge small remainders) |
| `CHUNK_OVERLAP_RATIO` | 0.2 | Overlap ratio between consecutive chunks |

Token counting uses `tiktoken` with the `cl100k_base` encoding.

## Cross-Service Data Boundaries

| Table | Write Owner | Read Consumers |
|-------|------------|----------------|
| `scraping_jobs` | scraper-worker | gateway (status queries), DM frontend |
| `crawled_urls` | scraper-worker | DM frontend (browse crawled pages) |
| `documents` | scraper-worker | agent (RAG retrieval), gateway (corpus projection) |
| `document_chunks` | scraper-worker | agent (similarity search), gateway (chunk stats) |
| `chunk_embeddings` | scraper-worker | agent (vector similarity) |

# Data Management API — Data Models

> Auto-generated: 2026-05-12

## Overview

The data-management API itself is **stateless** — it does not own database
tables directly. However, it delegates to the scraper service which owns the
**scraper pipeline schema** in Postgres. The models below are defined in the
scraper codebase (`modal-apps/scraper/src/vecinita_scraper/core/`) and are the
authoritative representation of the data this API proxies.

## API-Layer Models (Pydantic — request/response)

### EmbedRequest / EmbedResponse

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| text | `str` | required | Text to embed |
| model_version | `str \| None` | optional | Target model version |
| embedding | `list[float]` | response only | Resulting embedding vector |

**Source:** `apis/data-management-api/packages/shared-schemas/shared_schemas/embedding.py`

### PredictRequest / PredictResponse

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| text | `str` | required | Text to classify |
| model_version | `str \| None` | optional | Target model version |
| label | `str` | response only | Predicted category |
| score | `float` | response only | Confidence score |

**Source:** `apis/data-management-api/packages/shared-schemas/shared_schemas/model.py`

### ScrapeRequest / ScrapeResult

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| url | `HttpUrl` | required | Seed URL |
| depth | `int` | default 1 | Crawl depth |
| title | `str \| None` | response only | Page title |
| text | `str \| None` | response only | Extracted text |
| metadata | `dict` | response only | Arbitrary metadata |

**Source:** `apis/data-management-api/packages/shared-schemas/shared_schemas/scraper.py`

## Scraper Pipeline Models (Postgres — owned by scraper service)

### scraping_jobs

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | `UUID` | PK | Job identifier |
| url | `text` | NOT NULL | Seed URL |
| user_id | `text` | NOT NULL | Operator/tenant identifier |
| status | `text` | NOT NULL | Pipeline status enum |
| crawl_config | `jsonb` | nullable | Crawl overrides |
| chunking_config | `jsonb` | nullable | Chunking overrides |
| metadata | `jsonb` | nullable | Arbitrary job metadata |
| error_message | `text` | nullable | Failure description |
| created_at | `timestamp` | NOT NULL | Creation time |
| updated_at | `timestamp` | NOT NULL | Last update time |

**Source:** `modal-apps/scraper/src/vecinita_scraper/core/db.py` (SQL in `PostgresDB.create_scraping_job`)

### crawled_urls

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | `UUID` | PK | Crawled URL identifier |
| job_id | `UUID` | FK → scraping_jobs | Parent job |
| url | `text` | NOT NULL | Crawled URL |
| raw_content_hash | `text` | NOT NULL | Content hash for dedup |
| status | `text` | NOT NULL | success / failed / timeout |
| error_message | `text` | nullable | Failure reason |
| crawled_at | `timestamp` | NOT NULL | Crawl timestamp |

**Unique constraint:** `(job_id, url)` — upsert on conflict

**Source:** `modal-apps/scraper/src/vecinita_scraper/core/db.py` (SQL in `PostgresDB.store_crawled_url`)

### extracted_content

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | `UUID` | PK | Extraction identifier |
| crawled_url_id | `UUID` | FK → crawled_urls | Source crawled URL |
| content_type | `text` | NOT NULL | markdown / html / pdf |
| raw_content | `text` | NOT NULL | Raw extracted text |
| processing_status | `text` | NOT NULL | pending / processing / completed / failed |

**Source:** `modal-apps/scraper/src/vecinita_scraper/core/db.py`

### processed_documents

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | `UUID` | PK | Document identifier |
| extracted_content_id | `UUID` | FK → extracted_content | Source extraction |
| markdown_content | `text` | NOT NULL | Docling-processed markdown |
| tables_json | `text` | nullable | Extracted table data |
| metadata_json | `jsonb` | nullable | Document metadata |

**Source:** `modal-apps/scraper/src/vecinita_scraper/core/db.py`

### chunks

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | `UUID` | PK | Chunk identifier |
| processed_doc_id | `UUID` | FK → processed_documents | Parent document |
| chunk_text | `text` | NOT NULL | Chunk content |
| position | `int` | NOT NULL | Order within document |
| token_count | `int` | NOT NULL | Token count |
| semantic_boundary | `bool` | NOT NULL | At semantic boundary |

**Source:** `modal-apps/scraper/src/vecinita_scraper/core/db.py`

### embeddings

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | `UUID` | PK | Embedding identifier |
| job_id | `UUID` | FK → scraping_jobs | Parent job |
| chunk_id | `UUID` | FK → chunks | Source chunk |
| embedding_vector | `vector` | NOT NULL | pgvector embedding |
| model_name | `text` | NOT NULL | e.g. `BAAI/bge-small-en-v1.5` |
| dimensions | `int` | NOT NULL | Vector dimensions (e.g. 384) |
| created_at | `timestamp` | NOT NULL | Creation time |

**Source:** `modal-apps/scraper/src/vecinita_scraper/core/db.py`

## Relationships

| From | To | Cardinality | FK | Description |
|------|----|-------------|-----|-------------|
| scraping_jobs | crawled_urls | 1:N | `crawled_urls.job_id` | Job spawns multiple URL crawls |
| crawled_urls | extracted_content | 1:N | `extracted_content.crawled_url_id` | Each URL yields extractions |
| extracted_content | processed_documents | 1:1 | `processed_documents.extracted_content_id` | Docling processes extraction |
| processed_documents | chunks | 1:N | `chunks.processed_doc_id` | Document split into chunks |
| scraping_jobs | embeddings | 1:N | `embeddings.job_id` | Job tracks all embeddings |
| chunks | embeddings | 1:1 | `embeddings.chunk_id` | Each chunk gets one embedding |

## Diagrams

- [ER Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)

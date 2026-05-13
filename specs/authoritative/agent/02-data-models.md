# Vecinita Agent — Data Models

> Auto-generated: 2026-05-12

## Overview

The agent service reads from the `document_chunks` and `processing_queue` tables in the shared `vecinita-postgres` database. It does not own a separate schema namespace — all tables live in the `public` schema. The agent performs read-only vector searches against `document_chunks` at query time; write operations (embedding, ingestion) are performed by the vector loader utility and the scraping pipeline.

## Models

### DocumentChunk

Primary table for RAG retrieval. Stores content, source attribution, and pgvector embeddings.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Auto-generated chunk identifier |
| content | TEXT | NOT NULL | Raw text content of the chunk |
| source_url | TEXT | NOT NULL | URL of the original scraped document |
| chunk_index | INTEGER | NOT NULL | Position of this chunk within its source document |
| total_chunks | INTEGER | | Total number of chunks for the source document |
| document_id | UUID | | Logical document grouping identifier |
| document_title | TEXT | | Human-readable title for the source |
| embedding | VECTOR(384) | | pgvector embedding (all-MiniLM-L6-v2, 384 dimensions) |
| is_processed | BOOLEAN | DEFAULT true | Whether the chunk has been successfully embedded |
| processing_status | TEXT | | Status: `completed`, `pending`, `no_embedding`, `failed` |
| error_message | TEXT | | Error details if processing failed |
| metadata | JSONB | DEFAULT '{}' | Flexible metadata: `tags`, `source_domain`, `char_start`, `char_end` |
| scraped_at | TIMESTAMPTZ | | When the source was scraped |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Row creation time |
| updated_at | TIMESTAMPTZ | | Last modification time |

**Source:** `apis/agent/src/agent/utils/vector_loader.py` (VecinitaLoader._upsert_postgres_chunks)

**Constraints:**
- `unique_content_source` — UNIQUE on (`content`, `source_url`) for upsert deduplication

**RPC Function:**
- `search_similar_documents(query_embedding VECTOR, match_threshold FLOAT, match_count INT)` — cosine similarity search used by `GET /test-db-search` diagnostics

### ProcessingQueue

Tracks batch data loading operations for observability.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID/SERIAL | PK | Queue entry identifier |
| file_path | TEXT | | Source file being processed |
| file_size | BIGINT | | Size of the source file in bytes |
| status | TEXT | NOT NULL | `processing`, `completed`, `failed` |
| started_at | TIMESTAMPTZ | | When processing began |
| completed_at | TIMESTAMPTZ | | When processing finished |
| chunks_processed | INTEGER | | Number of chunks successfully inserted |
| total_chunks | INTEGER | | Total chunks in the file |
| error_message | TEXT | | Error details if failed |

**Source:** `apis/agent/src/agent/utils/vector_loader.py` (VecinitaLoader._insert_processing_queue_postgres)

### AgentAskJsonResponse (API schema)

Pydantic model for the `/ask` endpoint response body.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| answer | str | required | Generated answer text |
| thread_id | str | default "default" | Conversation thread identifier |
| response_time_ms | int | >= 0 | Total request latency in milliseconds |
| sources | list[dict] | | Source documents referenced in the answer |
| latency_breakdown | dict \| None | | Timing breakdown: `retrieval_invoke_ms`, `llm_ms`, `db_search` |

**Source:** `apis/agent/src/agent/http_api_schemas.py`

### ModelSelection (runtime state)

In-memory and file-persisted model selection state.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| provider | str | always "ollama" | LLM provider identifier |
| model | str \| None | | Active model tag (e.g., `gemma3`, `mistral`) |
| locked | bool | | Whether selection changes are blocked |

**Source:** `apis/gateway/src/services/agent/models.py`, `apis/gateway/src/services/llm/client_manager.py`

### GuardResult (internal)

Lightweight result from guardrails validation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| passed | bool | required | Whether the input/output passed validation |
| reason | str | | Localized rejection message if failed |
| redacted | str \| None | | Sanitized version of the text if PII was found |

**Source:** `apis/agent/src/agent/guardrails_config.py`

## Relationships

| From | To | Cardinality | Description |
|------|----|-------------|-------------|
| DocumentChunk | DocumentChunk | N:1 (by source_url) | Multiple chunks share a single source URL |
| DocumentChunk | ProcessingQueue | N:1 | Chunks loaded by a queue entry share the file_path |
| DocumentChunk.metadata.tags | (query filter) | M:N | JSONB tag arrays enable tag-based retrieval filtering |

## Diagrams

- [ER Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)

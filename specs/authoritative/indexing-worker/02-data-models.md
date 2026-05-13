# Data Models: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker will interact with two PostgreSQL schemas. It **reads** from `data_mgmt` (document source data) and **writes** to `agent` (vector storage). It will also manage its own indexing job metadata. All models below are **planned** — Pydantic schemas for the application layer and SQL DDL for the database layer.

See: [Data Models Diagram](diagrams/data-models.md)

## Database Tables

### Tables Read (Owned by data-management-api)

#### `data_mgmt.documents`

Source of truth for document content. The indexing-worker reads from this table but never writes to it.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | `uuid` | PK | Document identifier |
| source_id | `uuid` | FK → sources | Parent source/site |
| url | `text` | NOT NULL | Original document URL |
| title | `text` | — | Document title |
| content | `text` | NOT NULL | Full document text (markdown) |
| content_hash | `text` | — | SHA-256 hash of content (if populated by data-mgmt) |
| metadata | `jsonb` | DEFAULT '{}' | Arbitrary metadata |
| created_at | `timestamptz` | NOT NULL | Creation timestamp |
| updated_at | `timestamptz` | NOT NULL | Last modification timestamp |

### Tables Written (Owned by indexing-worker)

#### `agent.vectors`

Stores chunked document embeddings for pgvector similarity search.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | `uuid` | PK, DEFAULT gen_random_uuid() | Vector record identifier |
| document_id | `uuid` | FK → data_mgmt.documents, NOT NULL | Source document |
| chunk_index | `integer` | NOT NULL | Position within the document (0-based) |
| chunk_text | `text` | NOT NULL | Raw text of the chunk |
| embedding | `vector(384)` | NOT NULL | Dense vector (384 dims for bge-small-en-v1.5) |
| embedding_model | `text` | NOT NULL | Model identifier used to generate this vector |
| token_count | `integer` | — | Token count of the chunk |
| metadata | `jsonb` | DEFAULT '{}' | Chunk-level metadata (source_url, title, etc.) |
| created_at | `timestamptz` | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | `timestamptz` | NOT NULL, DEFAULT now() | Last update timestamp |

**Indexes (planned):**

| Index | Type | Columns | Purpose |
|-------|------|---------|---------|
| `idx_vectors_embedding` | ivfflat / hnsw | `embedding` | Approximate nearest neighbor search |
| `idx_vectors_document_id` | btree | `document_id` | Lookup vectors by source document |
| `idx_vectors_model` | btree | `embedding_model` | Filter/delete by model version |

#### `agent.content_hashes`

Tracks content hashes for selective re-indexing. Allows the indexing-worker to detect which documents have changed since last indexing.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | `uuid` | PK, DEFAULT gen_random_uuid() | Record identifier |
| document_id | `uuid` | UNIQUE, FK → data_mgmt.documents | One hash per document |
| content_hash | `text` | NOT NULL | SHA-256 hash of document content at last indexing |
| indexed_at | `timestamptz` | NOT NULL, DEFAULT now() | When this document was last indexed |
| embedding_model | `text` | NOT NULL | Model version used for this index pass |
| chunk_count | `integer` | NOT NULL | Number of chunks produced |

#### `agent.indexing_jobs`

Tracks indexing job execution for observability and idempotency.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | `uuid` | PK, DEFAULT gen_random_uuid() | Job identifier |
| job_type | `text` | NOT NULL | `single`, `batch`, `reindex_changed`, `rebuild_all` |
| status | `text` | NOT NULL, DEFAULT 'pending' | `pending`, `running`, `completed`, `failed`, `cancelled` |
| document_ids | `uuid[]` | — | Array of targeted document IDs |
| source_id | `uuid` | — | Source scope (for re-index operations) |
| total_documents | `integer` | DEFAULT 0 | Total documents in scope |
| processed_documents | `integer` | DEFAULT 0 | Documents successfully processed |
| failed_documents | `integer` | DEFAULT 0 | Documents that failed |
| skipped_documents | `integer` | DEFAULT 0 | Documents skipped (unchanged) |
| error_message | `text` | — | Error details if status = failed |
| embedding_model | `text` | NOT NULL | Model used for this job |
| started_at | `timestamptz` | — | When processing began |
| completed_at | `timestamptz` | — | When processing finished |
| created_at | `timestamptz` | NOT NULL, DEFAULT now() | Job creation timestamp |

## Pydantic Schemas (Application Layer)

### IndexDocumentRequest

```python
class IndexDocumentRequest(BaseModel):
    document_id: UUID
    force: bool = False  # bypass content hash check
    correlation_id: str | None = None
```

### IndexBatchRequest

```python
class IndexBatchRequest(BaseModel):
    document_ids: list[UUID]
    force: bool = False
    correlation_id: str | None = None

    @field_validator("document_ids")
    @classmethod
    def validate_batch_size(cls, v: list[UUID]) -> list[UUID]:
        if len(v) > settings.INDEX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(v)} exceeds max {settings.INDEX_BATCH_SIZE}")
        return v
```

### ReindexChangedRequest

```python
class ReindexChangedRequest(BaseModel):
    source_id: UUID
    correlation_id: str | None = None
```

### RebuildAllRequest

```python
class RebuildAllRequest(BaseModel):
    reason: str  # "model_change", "schema_migration", "manual"
    confirm: bool = False  # safety flag — must be True to proceed
    correlation_id: str | None = None
```

### IndexingResult

```python
class IndexingResult(BaseModel):
    job_id: UUID
    job_type: str
    status: str  # "completed", "failed", "partial"
    total_documents: int
    processed_documents: int
    failed_documents: int
    skipped_documents: int
    duration_seconds: float
    errors: list[DocumentError] = []
```

### DocumentError

```python
class DocumentError(BaseModel):
    document_id: UUID
    error: str
    stage: str  # "read", "chunk", "embed", "store"
```

### DocumentChunk

Internal model representing a chunked document segment.

```python
class DocumentChunk(BaseModel):
    document_id: UUID
    chunk_index: int
    text: str
    token_count: int
    metadata: dict = {}
```

### VectorRecord

Internal model representing a vector ready for PostgreSQL insertion.

```python
class VectorRecord(BaseModel):
    document_id: UUID
    chunk_index: int
    chunk_text: str
    embedding: list[float]
    embedding_model: str
    token_count: int
    metadata: dict = {}
```

### ContentHashRecord

```python
class ContentHashRecord(BaseModel):
    document_id: UUID
    content_hash: str
    embedding_model: str
    chunk_count: int
    indexed_at: datetime
```

## Entity Relationships

```
data_mgmt.documents (read) ─── 1:N ──→ agent.vectors (write)
data_mgmt.documents (read) ─── 1:1 ──→ agent.content_hashes (write)
agent.indexing_jobs           ─── 1:N ──→ agent.vectors (via document_ids)
```

See: [Data Models Diagram](diagrams/data-models.md) for visual ER representation.

## Schema Ownership

| Table | Schema | Owner | Indexing Worker Access |
|-------|--------|-------|----------------------|
| `documents` | `data_mgmt` | data-management-api | **Read only** |
| `sources` | `data_mgmt` | data-management-api | **Read only** |
| `vectors` | `agent` | indexing-worker | **Read/Write** |
| `content_hashes` | `agent` | indexing-worker | **Read/Write** |
| `indexing_jobs` | `agent` | indexing-worker | **Read/Write** |

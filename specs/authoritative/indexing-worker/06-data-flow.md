# Data Flow: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker implements a multi-stage data pipeline: **read → chunk → embed → store**. Each stage transforms data from one representation to the next, with the final output being dense vector embeddings stored in PostgreSQL via pgvector.

See: [Data Flow Diagram](diagrams/data-flow.md)

## Pipeline Stages

### Stage 1: Document Ingestion (Read)

| Property | Value |
|----------|-------|
| Source | `data_mgmt.documents` table in PostgreSQL |
| Trigger | Modal function invocation with `document_id` or `source_id` |
| Output | `Document` object: `{ id, content, content_hash, metadata }` |
| Format | Raw text (markdown) |

**Data transformation:**
- Raw PostgreSQL row → Pydantic `Document` model
- Content validated as non-empty
- Metadata extracted for downstream enrichment of vector records

### Stage 2: Content Hashing (Optional — Selective Re-Index Only)

| Property | Value |
|----------|-------|
| Input | Document content (text) |
| Algorithm | SHA-256 |
| Output | 64-character hex digest |
| Storage | `agent.content_hashes` table |

**Data transformation:**
- `content` → `hashlib.sha256(content.encode("utf-8")).hexdigest()`
- Compared against stored hash to determine if re-indexing is needed
- If hashes match: document is skipped (no GPU cost)
- If hashes differ or no stored hash exists: document proceeds to chunking

### Stage 3: Document Chunking

| Property | Value |
|----------|-------|
| Input | Full document text (markdown) |
| Tool | LlamaIndex `SentenceSplitter` |
| Chunk size | 512 tokens (configurable via `CHUNK_SIZE`) |
| Chunk overlap | 50 tokens (configurable via `CHUNK_OVERLAP`) |
| Output | List of `DocumentChunk` objects |

**Data transformation:**
- Single document text → N overlapping text chunks
- Each chunk tagged with `chunk_index` (0-based position)
- Token count computed per chunk
- Metadata from parent document propagated to each chunk

**Chunking strategy rationale:**
- Sentence-aware splitting preserves semantic boundaries
- Overlap ensures no information is lost at chunk boundaries
- 512-token chunks balance retrieval precision with context length

### Stage 4: Embedding Generation

| Property | Value |
|----------|-------|
| Input | List of chunk texts (strings) |
| Model | BAAI/bge-small-en-v1.5 (384 dimensions) |
| Library | fastembed (via LlamaIndex adapter) |
| Hardware | GPU (Modal container) |
| Output | List of 384-dimensional float vectors |

**Data transformation:**
- List of text strings → List of `list[float]` vectors
- Batch processing: all chunks from a document are embedded in a single GPU call
- Model loaded from shared volume (`vecinita-embedding-models`) on cold start
- Subsequent calls use in-memory model (warm container)

**Performance characteristics:**
- Cold start: ~10-30s (model download + GPU initialization)
- Warm embedding: ~50-200ms per batch of chunks
- Memory: ~500MB GPU memory for bge-small-en-v1.5

### Stage 5: Vector Persistence (Store)

| Property | Value |
|----------|-------|
| Input | List of `VectorRecord` objects |
| Target | `agent.vectors` table (pgvector) |
| Operation | Upsert (INSERT ON CONFLICT DO UPDATE) |
| Output | Row count of inserted/updated records |

**Data transformation:**
- `VectorRecord` → SQL INSERT with pgvector `vector(384)` type
- Existing vectors for the document are deleted first (atomic replacement)
- Content hash updated in `agent.content_hashes` after successful vector write
- Job status updated in `agent.indexing_jobs`

**Write pattern:**
```sql
DELETE FROM agent.vectors WHERE document_id = $1;

INSERT INTO agent.vectors (document_id, chunk_index, chunk_text, embedding, embedding_model, token_count, metadata)
VALUES ($1, $2, $3, $4::vector, $5, $6, $7);
```

## Data Volume Estimates

| Metric | Estimate | Basis |
|--------|----------|-------|
| Average document size | ~5,000 tokens | Typical web page after markdown conversion |
| Chunks per document | ~10-12 | 5000 tokens / 512 chunk size with overlap |
| Vector size per chunk | 1.5 KB | 384 floats × 4 bytes |
| Storage per document | ~18 KB vectors + ~50 KB text | Vectors + chunk_text storage |
| Embedding time per document | ~200-500ms | GPU warm, 10-12 chunks batched |

## Data Retention

| Data | Retention Policy |
|------|-----------------|
| Vectors (`agent.vectors`) | Kept until document is deleted or model changes trigger rebuild |
| Content hashes (`agent.content_hashes`) | Kept indefinitely; updated on each re-index |
| Indexing jobs (`agent.indexing_jobs`) | Kept for 90 days (planned cleanup job) |
| Document content (`data_mgmt.documents`) | Managed by data-management-api (not this service) |

## Data Flow per Indexing Mode

### Single-Document Flow

```
Gateway/Scraper → index_document(doc_id)
  → READ: data_mgmt.documents WHERE id = doc_id
  → CHUNK: SentenceSplitter(512, 50)
  → EMBED: fastembed on GPU
  → DELETE: agent.vectors WHERE document_id = doc_id
  → INSERT: agent.vectors (N rows)
  → UPSERT: agent.content_hashes
  → UPDATE: agent.indexing_jobs
  → RETURN: IndexingResult
```

### Batch Flow

```
Gateway → index_batch(doc_ids)
  → VALIDATE: len(doc_ids) <= INDEX_BATCH_SIZE
  → CREATE: agent.indexing_jobs
  → SPAWN_MAP: index_document for each doc_id
    → (each runs Single-Document Flow in parallel)
  → AGGREGATE: collect results
  → UPDATE: agent.indexing_jobs
  → RETURN: IndexingResult (aggregated)
```

### Selective Re-Index Flow

```
Gateway → reindex_changed(source_id)
  → READ: data_mgmt.documents WHERE source_id = source_id
  → READ: agent.content_hashes WHERE document_id IN (...)
  → COMPUTE: SHA-256 of each document content
  → COMPARE: current hash vs stored hash
  → FILTER: only changed document IDs
  → SPAWN_MAP: index_document for changed docs
  → RETURN: IndexingResult (with skipped count)
```

### Full Rebuild Flow

```
Operator → rebuild_all(reason, confirm=True)
  → CHECK: no concurrent rebuild running
  → CREATE: agent.indexing_jobs
  → DELETE: ALL FROM agent.vectors
  → DELETE: ALL FROM agent.content_hashes
  → READ: ALL FROM data_mgmt.documents
  → BATCH SPAWN_MAP: index_document in batches of INDEX_BATCH_SIZE
  → AGGREGATE: collect all results
  → UPDATE: agent.indexing_jobs
  → RETURN: IndexingResult
```

## Cross-References

- Data models: [02-data-models.md](02-data-models.md)
- Integration points: [03-integration-points.md](03-integration-points.md)
- Architecture: [07-architecture.md](07-architecture.md)

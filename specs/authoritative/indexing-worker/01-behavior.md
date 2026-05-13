# Behavior: Indexing Worker
> Auto-generated: 2026-05-12

## Purpose

The indexing-worker is a **planned** serverless document indexing pipeline deployed on Modal GPU. It will convert scraped documents into chunked, embedded vector representations stored in PostgreSQL (pgvector). The service separates the indexing concern from scraping, enabling independent scaling of the compute-intensive embedding step and supporting multiple indexing strategies.

Target path: `apps/indexing-worker/`

## Core Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| 1 | Single-document indexing | Chunk and embed a single document on demand, writing vectors to `agent.vectors` |
| 2 | Batch indexing | Index multiple documents in parallel using Modal `spawn_map` |
| 3 | Selective re-indexing | Detect changed content via content hash comparison, re-index only modified documents |
| 4 | Full vector rebuild | Rebuild all vectors from scratch when the embedding model changes |
| 5 | Content chunking | Split documents into overlapping token-based chunks using LlamaIndex text splitters |
| 6 | Embedding generation | Generate dense vector embeddings using BAAI/bge-small-en-v1.5 (or configured model) on GPU |
| 7 | Vector persistence | Write embedding vectors to PostgreSQL `agent.vectors` via pgvector |
| 8 | Health reporting | Expose a lightweight CPU-only health probe for monitoring |

## Key Behaviors

### Single-Document Indexing (index_document)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway invokes `index_document(document_id)` via Modal SDK | Read document from `data_mgmt.documents`, chunk text, generate embeddings on GPU, write vectors to `agent.vectors` | Vector records created/updated, indexing status returned to caller |
| Scraper-worker completes a scrape | Triggers `index_document` for the newly scraped document | Newly scraped content is immediately searchable |
| Document not found in database | Return error with `document_not_found` status | Caller receives structured error, no vectors written |
| Embedding generation fails | Retry up to 3 times with exponential backoff, then return `indexing_failed` | Partial results are not persisted; operation is atomic per document |

### Batch Indexing (index_batch)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway invokes `index_batch(document_ids)` | Fan out to `spawn_map` over `index_document` for each document ID | Parallel GPU execution, aggregated results returned |
| Batch size exceeds `INDEX_BATCH_SIZE` (default 100) | Reject with `batch_too_large` error | Caller must split into smaller batches |
| Individual document fails within batch | Mark that document as `failed` in results, continue processing others | Partial success: successful vectors are persisted, failures are reported |

### Selective Re-Indexing (reindex_changed)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway invokes `reindex_changed(source_id)` | Compute SHA-256 content hashes for all documents under `source_id`, compare against stored hashes in `agent.content_hashes` | Only changed documents are re-indexed, unchanged documents are skipped |
| No documents have changed | Return `no_changes` status with zero documents processed | No GPU resources consumed |
| Content hash table does not exist or is empty | Treat all documents as changed, index all, populate hash table | First-time indexing for a source behaves like a full index |

### Full Vector Rebuild (rebuild_all)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway invokes `rebuild_all(reason)` | Delete all existing vectors, re-chunk and re-embed every document, write new vectors | Complete vector store refresh (used after model change) |
| Embedding model configuration has changed | Caller sets `reason="model_change"` | Old vectors are incompatible; full rebuild ensures consistency |
| Rebuild is already in progress | Return `rebuild_in_progress` status, reject concurrent rebuild | Prevents duplicate GPU utilization |
| Rebuild exceeds 3600s timeout | Modal terminates the function | Partial progress is lost; caller must retry |

### Health Check (health_check)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Monitoring probe calls `health_check()` | Verify database connectivity, check model availability | `{ status: "healthy" }` or `{ status: "degraded", reason: "..." }` |

## Service Boundaries (Does NOT Own)

| Concern | Owned By |
|---------|----------|
| Web scraping, content extraction, crawling | scraper-worker (`vecinita-scraper`) |
| Raw embedding generation (standalone) | embedding-worker (`vecinita-embedding`) |
| RAG retrieval, LLM inference, agent orchestration | agent service |
| Document storage, source management | data-management-api (`data_mgmt` schema) |
| HTTP API surface, authentication, rate limiting | gateway service |
| Frontend rendering | chat-frontend, data-management-frontend |

## Relationship to Embedding Worker

The indexing-worker and embedding-worker share the same embedding model (`BAAI/bge-small-en-v1.5`) and model cache volume (`vecinita-embedding-models`). The key distinction:

| Aspect | Embedding Worker | Indexing Worker (planned) |
|--------|-----------------|--------------------------|
| Scope | Raw text → vector (stateless) | Document → chunk → embed → store (stateful pipeline) |
| Input | Arbitrary text strings | Document IDs referencing PostgreSQL rows |
| Output | Vector arrays returned to caller | Vectors written directly to `agent.vectors` |
| Persistence | None (pure function) | Writes to PostgreSQL |
| Batch strategy | Simple `embed_batch` | `spawn_map` with per-document parallelism |
| Change detection | N/A | Content hash comparison |

# User Journeys: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

Each indexing mode represents a distinct user journey, though all "users" are automated systems. These journeys trace the complete flow from trigger to outcome, including failure modes.

See: [User Journeys Diagram](diagrams/user-journeys.md), [Sequence Flows](diagrams/sequence-flows.md)

## Journey 1: Single-Document Indexing

**Persona:** Gateway Service (P1) or Scraper Worker (P2)
**Goal:** Index a single document so it becomes searchable via RAG

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Gateway / Scraper | Invoke `index_document(document_id=<uuid>)` via Modal SDK | Function starts on GPU container |
| 2 | Indexing Worker | Read document from `data_mgmt.documents` | Document content and metadata loaded |
| 3 | Indexing Worker | Create `indexing_jobs` record with status `running` | Job tracking begins |
| 4 | Indexing Worker | Chunk document using LlamaIndex `SentenceSplitter(chunk_size=512, chunk_overlap=50)` | N chunks produced |
| 5 | Indexing Worker | Generate embeddings for all chunks on GPU | N 384-dim vectors produced |
| 6 | Indexing Worker | Delete existing vectors for this document_id | Old vectors removed |
| 7 | Indexing Worker | Insert new vector records into `agent.vectors` | Vectors persisted |
| 8 | Indexing Worker | Update content hash in `agent.content_hashes` | Hash stored for future change detection |
| 9 | Indexing Worker | Update `indexing_jobs` record with status `completed` | Job marked complete |
| 10 | Indexing Worker | Return `IndexingResult` to caller | Gateway/scraper receives success confirmation |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Document not found in database | `SELECT` returns no rows | Return `IndexingResult(status="failed", errors=[...])` |
| Chunking produces zero chunks | Empty chunk list after splitting | Return failure — document may be empty |
| GPU out of memory | Modal container OOM | Modal auto-retries on a new container (up to 3 attempts) |
| Database write failure | psycopg2 exception | Retry 3x with backoff, then fail the job |
| Modal function timeout (300s) | `FunctionTimeoutError` | Caller receives timeout error, job stays in `running` (requires cleanup) |

## Journey 2: Batch Indexing

**Persona:** Gateway Service (P1)
**Goal:** Index multiple documents in parallel for efficiency

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Gateway | Invoke `index_batch(document_ids=[uuid1, uuid2, ...])` via Modal SDK | Function starts on GPU container |
| 2 | Indexing Worker | Validate batch size ≤ `INDEX_BATCH_SIZE` (100) | Pass or reject with `batch_too_large` |
| 3 | Indexing Worker | Create `indexing_jobs` record with type `batch` | Job tracking begins |
| 4 | Indexing Worker | Fan out via `index_document.spawn_map(document_ids)` | Parallel GPU containers launched |
| 5 | Modal Platform | Execute each `index_document` independently on GPU | Parallel processing |
| 6 | Indexing Worker | Aggregate results from all spawned calls | Collect successes and failures |
| 7 | Indexing Worker | Update `indexing_jobs` with aggregated stats | `processed_documents`, `failed_documents` tallied |
| 8 | Indexing Worker | Return aggregated `IndexingResult` | Gateway receives summary with per-document status |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Batch size exceeds limit | Schema validation at step 2 | Immediate rejection, caller splits batch |
| Individual document fails | `spawn_map` result contains error | Other documents still succeed; partial result returned |
| Modal platform overloaded | spawn_map calls queue or timeout | Some documents may timeout; reported in result |
| All documents fail | Every spawn_map result is an error | `IndexingResult(status="failed")` with all errors |

## Journey 3: Selective Re-Indexing

**Persona:** Gateway Service (P1)
**Goal:** Re-index only documents that have changed since last indexing

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Gateway | Invoke `reindex_changed(source_id=<uuid>)` via Modal SDK | Function starts on GPU container |
| 2 | Indexing Worker | Load all documents for `source_id` from `data_mgmt.documents` | Document list loaded |
| 3 | Indexing Worker | Load existing content hashes from `agent.content_hashes` | Stored hashes loaded |
| 4 | Indexing Worker | Compute SHA-256 hash of each document's current content | Current hashes computed |
| 5 | Indexing Worker | Compare current hashes against stored hashes | Changed document IDs identified |
| 6 | Indexing Worker | Skip unchanged documents | `skipped_documents` count incremented |
| 7 | Indexing Worker | Index changed documents via `spawn_map` | Only changed documents consume GPU |
| 8 | Indexing Worker | Update content hashes for re-indexed documents | Hashes refreshed |
| 9 | Indexing Worker | Return `IndexingResult` with skipped/processed counts | Gateway sees efficiency metrics |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| No documents for source_id | Empty `SELECT` result | Return `IndexingResult(status="completed", total=0)` |
| Content hash table empty (first run) | No stored hashes found | Treat all documents as changed, index all |
| Hash computation mismatch (encoding) | Unlikely but possible | Use consistent UTF-8 normalization before hashing |

## Journey 4: Full Vector Rebuild

**Persona:** Platform Operator (P3) via Gateway
**Goal:** Rebuild all vectors after an embedding model change

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Operator | Triggers rebuild via gateway (or direct Modal CLI) | Gateway invokes `rebuild_all.spawn(reason="model_change", confirm=True)` |
| 2 | Indexing Worker | Verify `confirm=True` safety flag | Proceed or reject |
| 3 | Indexing Worker | Check for concurrent rebuild (query `indexing_jobs` for `running` + `rebuild_all`) | Block if another rebuild is active |
| 4 | Indexing Worker | Create `indexing_jobs` record with type `rebuild_all` | Job tracking begins |
| 5 | Indexing Worker | Load all documents from `data_mgmt.documents` | Full document inventory loaded |
| 6 | Indexing Worker | Delete all existing vectors from `agent.vectors` | Clean slate |
| 7 | Indexing Worker | Clear all content hashes from `agent.content_hashes` | Hashes invalidated |
| 8 | Indexing Worker | Process documents in batches via `spawn_map` | Parallel GPU processing |
| 9 | Indexing Worker | Write new vectors and hashes for all documents | Complete vector store refreshed |
| 10 | Indexing Worker | Update `indexing_jobs` with final stats | Rebuild complete |
| 11 | Indexing Worker | Return `IndexingResult` | Operator receives confirmation |

### Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| `confirm=False` | Safety check at step 2 | Reject with clear error message |
| Concurrent rebuild already running | Query `indexing_jobs` | Reject with `rebuild_in_progress` status |
| Timeout at 3600s | Modal terminates function | Partial vectors exist; operator must re-run or resume |
| Database connection loss mid-rebuild | psycopg2 exception | Partial state — operator must run `rebuild_all` again |
| Model not available in cache | fastembed download fails | Fail early before deleting existing vectors |

## Journey 5: Health Check

**Persona:** Platform Operator (P3) / Monitoring System
**Goal:** Verify the indexing-worker is operational

### Happy Path

| Step | Actor | Action | System Response |
|------|-------|--------|----------------|
| 1 | Monitor | Invoke `health_check()` via Modal SDK | Function starts on CPU container |
| 2 | Indexing Worker | Test database connectivity | `SELECT 1` succeeds |
| 3 | Indexing Worker | Verify model cache availability | Model files present on volume |
| 4 | Indexing Worker | Return `{ status: "healthy" }` | Monitor records healthy state |

### Failure Modes

| Failure | Response |
|---------|----------|
| Database unreachable | `{ status: "degraded", reason: "database_unavailable" }` |
| Model cache empty | `{ status: "degraded", reason: "model_not_cached" }` |
| Both failing | `{ status: "unhealthy", reasons: [...] }` |

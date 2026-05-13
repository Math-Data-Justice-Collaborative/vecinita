# API Contract: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker exposes **no HTTP endpoints**. All interaction is via Modal SDK function invocations. The "API contract" is the set of Modal function signatures, their input/output types, and behavioral guarantees.

## Function Signatures

### index_document

Index a single document: read → chunk → embed → store vectors.

| Property | Value |
|----------|-------|
| Modal app | `vecinita-indexing` |
| Function name | `index_document` |
| GPU | T4 (or A10G) |
| Timeout | 300s |
| Retries | 2 |
| Idempotent | Yes (deletes existing vectors, re-creates) |

**Invocation:**
```python
fn = modal.Function.from_name("vecinita-indexing", "index_document")
result = fn.remote(document_id="<uuid>", force=False, correlation_id="<optional>")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| document_id | `str` (UUID) | Yes | — | ID of the document in `data_mgmt.documents` |
| force | `bool` | No | `False` | If `True`, bypass content hash check and always re-index |
| correlation_id | `str` | No | `None` | Tracing correlation ID propagated from gateway |

**Return value:** `dict` (serialized `IndexingResult`)

```json
{
  "job_id": "uuid",
  "job_type": "single",
  "status": "completed",
  "total_documents": 1,
  "processed_documents": 1,
  "failed_documents": 0,
  "skipped_documents": 0,
  "duration_seconds": 1.23,
  "errors": []
}
```

**Error responses:**

| Status | Condition | Error in Result |
|--------|-----------|-----------------|
| `failed` | Document not found | `{"document_id": "...", "error": "document_not_found", "stage": "read"}` |
| `failed` | Embedding generation error | `{"document_id": "...", "error": "...", "stage": "embed"}` |
| `failed` | Database write error | `{"document_id": "...", "error": "...", "stage": "store"}` |
| `skipped` | Content unchanged and `force=False` | `skipped_documents: 1` |

---

### index_batch

Index multiple documents in parallel via `spawn_map`.

| Property | Value |
|----------|-------|
| Modal app | `vecinita-indexing` |
| Function name | `index_batch` |
| GPU | None (orchestrator) |
| Timeout | 600s |
| Retries | 0 |
| Idempotent | Yes (each sub-call is idempotent) |

**Invocation:**
```python
fn = modal.Function.from_name("vecinita-indexing", "index_batch")
result = fn.remote(document_ids=["uuid1", "uuid2", ...], force=False, correlation_id="<optional>")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| document_ids | `list[str]` | Yes | — | List of document UUIDs (max `INDEX_BATCH_SIZE`, default 100) |
| force | `bool` | No | `False` | Bypass content hash checks for all documents |
| correlation_id | `str` | No | `None` | Tracing correlation ID |

**Return value:** `dict` (serialized `IndexingResult`)

```json
{
  "job_id": "uuid",
  "job_type": "batch",
  "status": "completed",
  "total_documents": 25,
  "processed_documents": 23,
  "failed_documents": 2,
  "skipped_documents": 0,
  "duration_seconds": 45.6,
  "errors": [
    {"document_id": "uuid-a", "error": "document_not_found", "stage": "read"},
    {"document_id": "uuid-b", "error": "embedding_failed", "stage": "embed"}
  ]
}
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| `failed` | All documents failed |
| `partial` | Some documents failed, some succeeded |
| `completed` | All documents succeeded |
| Validation error | `document_ids` exceeds `INDEX_BATCH_SIZE` → `ValueError` raised by Modal |

---

### reindex_changed

Compare content hashes and re-index only changed documents for a given source.

| Property | Value |
|----------|-------|
| Modal app | `vecinita-indexing` |
| Function name | `reindex_changed` |
| GPU | None (orchestrator) |
| Timeout | 600s |
| Retries | 0 |
| Idempotent | Yes |

**Invocation:**
```python
fn = modal.Function.from_name("vecinita-indexing", "reindex_changed")
result = fn.remote(source_id="<uuid>", correlation_id="<optional>")
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| source_id | `str` (UUID) | Yes | — | Source/site ID to check for changes |
| correlation_id | `str` | No | `None` | Tracing correlation ID |

**Return value:** `dict` (serialized `IndexingResult`)

```json
{
  "job_id": "uuid",
  "job_type": "reindex_changed",
  "status": "completed",
  "total_documents": 50,
  "processed_documents": 5,
  "failed_documents": 0,
  "skipped_documents": 45,
  "duration_seconds": 12.3,
  "errors": []
}
```

---

### rebuild_all

Delete all vectors and rebuild from scratch. Used after embedding model changes.

| Property | Value |
|----------|-------|
| Modal app | `vecinita-indexing` |
| Function name | `rebuild_all` |
| GPU | None (orchestrator) |
| Timeout | 3600s |
| Retries | 0 |
| Idempotent | Yes (destructive but repeatable) |

**Invocation (non-blocking spawn recommended):**
```python
fn = modal.Function.from_name("vecinita-indexing", "rebuild_all")
call = fn.spawn(reason="model_change", confirm=True, correlation_id="<optional>")
# poll later:
result = call.get(timeout=3600)
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| reason | `str` | Yes | — | Why rebuild is needed: `"model_change"`, `"schema_migration"`, `"manual"` |
| confirm | `bool` | Yes | `False` | Safety flag — must be `True` to proceed |
| correlation_id | `str` | No | `None` | Tracing correlation ID |

**Return value:** `dict` (serialized `IndexingResult`)

```json
{
  "job_id": "uuid",
  "job_type": "rebuild_all",
  "status": "completed",
  "total_documents": 500,
  "processed_documents": 498,
  "failed_documents": 2,
  "skipped_documents": 0,
  "duration_seconds": 1234.5,
  "errors": [...]
}
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| `failed` | `confirm=False` → safety rejection |
| `failed` | Another rebuild already running → `rebuild_in_progress` |
| `partial` | Some documents failed during rebuild |
| FunctionTimeoutError | Exceeded 3600s timeout |

---

### health_check

Lightweight probe for monitoring.

| Property | Value |
|----------|-------|
| Modal app | `vecinita-indexing` |
| Function name | `health_check` |
| GPU | None (CPU only) |
| Timeout | 30s |
| Retries | 1 |

**Invocation:**
```python
fn = modal.Function.from_name("vecinita-indexing", "health_check")
result = fn.remote()
```

**Parameters:** None

**Return value:**

```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "model_cache": "ok"
  },
  "timestamp": "2026-05-12T12:00:00Z"
}
```

## Versioning

| Property | Value |
|----------|-------|
| Strategy | No explicit versioning (Modal function names are stable) |
| Breaking changes | Coordinate with gateway team; update function signatures in lockstep |
| Backward compatibility | New optional parameters only; return shape is additive |

## Rate Limits

| Limit | Value | Enforced By |
|-------|-------|-------------|
| Max batch size | 100 documents | `IndexBatchRequest` validator |
| Concurrent rebuilds | 1 | `indexing_jobs` table check |
| Modal container concurrency | Platform-managed | Modal platform |

## Cross-References

- Function deployment config: [13-modal-integration-plan.md](13-modal-integration-plan.md)
- Data models: [02-data-models.md](02-data-models.md)
- Gateway invocation pattern: [Gateway 13-modal-integration-plan](../gateway/13-modal-integration-plan.md)

# Integration Points: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker will integrate with three systems: two **inbound** callers (gateway, scraper-worker) and one **outbound** dependency (PostgreSQL). All inbound invocations use Modal SDK function calls — there are no HTTP endpoints.

See: [Integration Points Diagram](diagrams/integration-points.md)

## Inbound Integrations

### Gateway → Indexing Worker

| Property | Value |
|----------|-------|
| Direction | Inbound |
| Protocol | Modal SDK (`Function.from_name().remote()`) |
| Auth | Modal token-based (MODAL_TOKEN_ID / MODAL_TOKEN_SECRET) |
| Purpose | Trigger on-demand indexing (single, batch, re-index, rebuild) |

**Functions invoked by gateway:**

| Function | Gateway Call Pattern | Use Case |
|----------|---------------------|----------|
| `index_document` | `.remote(document_id=..., force=False)` | Single-doc indexing after manual request |
| `index_batch` | `.remote(document_ids=[...], force=False)` | Bulk indexing from data management UI |
| `reindex_changed` | `.remote(source_id=...)` | Selective update of changed content |
| `rebuild_all` | `.spawn(reason="model_change", confirm=True)` | Full rebuild (non-blocking spawn) |

**Error handling:**

| Scenario | Gateway Behavior |
|----------|-----------------|
| Modal function timeout | Gateway receives `modal.exception.FunctionTimeoutError`, surfaces to caller |
| Worker returns error result | Gateway reads `IndexingResult.status == "failed"` and reports errors |
| Modal platform unavailable | Gateway falls back to queuing the request for retry |

### Scraper Worker → Indexing Worker

| Property | Value |
|----------|-------|
| Direction | Inbound |
| Protocol | Modal SDK (cross-app function call) |
| Auth | Implicit — both apps share Modal workspace tokens |
| Purpose | Trigger indexing immediately after a scrape completes |

**Invocation pattern:**

```python
index_fn = modal.Function.from_name("vecinita-indexing", "index_document")
result = index_fn.remote(document_id=newly_scraped_doc_id)
```

**Error handling:**

| Scenario | Scraper Behavior |
|----------|-----------------|
| Indexing function unavailable | Log warning, mark document as `scraped_not_indexed` |
| Indexing fails | Scraper does not retry indexing — gateway handles retry policy |
| Indexing succeeds | Scraper records `indexed_at` timestamp on its job record |

## Outbound Integrations

### Indexing Worker → PostgreSQL

| Property | Value |
|----------|-------|
| Direction | Outbound |
| Protocol | TCP (psycopg2 / asyncpg) |
| Auth | `DATABASE_URL` connection string |
| Purpose | Read documents, write vectors and hashes |

**Read operations:**

| Table | Query Pattern | Purpose |
|-------|---------------|---------|
| `data_mgmt.documents` | `SELECT id, content, content_hash, metadata FROM documents WHERE id = $1` | Load document for indexing |
| `data_mgmt.documents` | `SELECT id, content, content_hash FROM documents WHERE source_id = $1` | Load all documents for a source (re-index) |
| `agent.content_hashes` | `SELECT document_id, content_hash FROM content_hashes WHERE document_id = ANY($1)` | Compare stored hashes for change detection |

**Write operations:**

| Table | Operation | Purpose |
|-------|-----------|---------|
| `agent.vectors` | `INSERT ... ON CONFLICT (document_id, chunk_index) DO UPDATE` | Upsert vector records |
| `agent.vectors` | `DELETE FROM vectors WHERE document_id = $1` | Remove old vectors before re-indexing a document |
| `agent.vectors` | `DELETE FROM vectors` | Clear all vectors for full rebuild |
| `agent.content_hashes` | `INSERT ... ON CONFLICT (document_id) DO UPDATE` | Update content hash after successful indexing |
| `agent.indexing_jobs` | `INSERT`, `UPDATE` | Track job lifecycle |

**Connection management (planned):**

| Property | Value |
|----------|-------|
| Driver | psycopg2-binary (initial), asyncpg (future) |
| Pool size | 5 connections per Modal container |
| Statement timeout | 30s for reads, 120s for bulk writes |
| SSL | Required (`sslmode=require`) |

**Error handling:**

| Scenario | Behavior |
|----------|----------|
| Connection failure | Retry 3 times with exponential backoff (1s, 2s, 4s) |
| Statement timeout | Abort current operation, mark job as failed |
| Unique constraint violation | Expected during upserts — handled via `ON CONFLICT` |
| Disk space / pgvector limit | Surface error in `IndexingResult`, alert operators |

### Shared Resources

#### Embedding Model Volume

| Property | Value |
|----------|-------|
| Volume name | `vecinita-embedding-models` |
| Shared with | embedding-worker (`vecinita-embedding`) |
| Purpose | Cache downloaded model weights to avoid re-downloading on cold starts |
| Mount path | `/models` |
| Contents | BAAI/bge-small-en-v1.5 model files (managed by fastembed/HuggingFace cache) |

## Integration Matrix

| From | To | Protocol | Direction | Data Exchanged |
|------|-----|----------|-----------|----------------|
| Gateway | Indexing Worker | Modal SDK `.remote()` / `.spawn()` | → | Document IDs, force flag, reason |
| Scraper Worker | Indexing Worker | Modal SDK `.remote()` | → | Document ID |
| Indexing Worker | PostgreSQL | TCP (psycopg2) | → | SQL queries, vector data |
| Indexing Worker | Model Volume | Modal Volume mount | ↔ | Model weight files (read) |

## Cross-References

- Gateway Modal integration: [Gateway 13-modal-integration-plan](../gateway/13-modal-integration-plan.md)
- Data management schema: [Data Management API 02-data-models](../data-management-api/02-data-models.md)
- Embedding worker (shared model): [Embedding Worker README](../embedding-worker/README.md)

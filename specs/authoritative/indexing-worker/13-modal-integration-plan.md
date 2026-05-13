# Modal Integration Plan: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker will be deployed as a Modal app named `vecinita-indexing`. This document details the planned Modal configuration, function decorators, GPU resources, volumes, secrets, and invocation patterns.

Planned source: `apps/indexing-worker/src/vecinita_indexing/app.py`

## Modal App Definition

```python
import modal

app = modal.App("vecinita-indexing")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "llama-index-core>=0.11",
        "llama-index-embeddings-fastembed>=0.3",
        "fastembed>=0.7.4",
        "psycopg2-binary>=2.9.9",
        "pgvector>=0.3",
        "pydantic>=2.6",
        "structlog>=24.1",
    )
)

volume = modal.Volume.from_name("vecinita-embedding-models", create_if_missing=True)
db_secret = modal.Secret.from_name("vecinita-db-credentials")
```

## Function Definitions

### index_document

The core GPU-accelerated indexing function.

```python
@app.function(
    image=image,
    gpu="T4",
    timeout=300,
    retries=2,
    secrets=[db_secret],
    volumes={"/models": volume},
    keep_warm=1,
)
def index_document(
    document_id: str,
    force: bool = False,
    correlation_id: str | None = None,
) -> dict:
    """Index a single document: read → chunk → embed → store vectors."""
    ...
```

| Property | Value |
|----------|-------|
| GPU | T4 (16 GB VRAM) |
| CPU | 2 cores (Modal default for GPU functions) |
| Memory | 4 GB |
| Timeout | 300 seconds |
| Retries | 2 (automatic retry on container crash) |
| Volumes | `/models` → `vecinita-embedding-models` |
| Secrets | `vecinita-db-credentials` (`DATABASE_URL`) |
| Keep warm | 1 container |

### index_batch

CPU-only orchestrator that fans out to `index_document` via `.map()`.

```python
@app.function(
    image=image,
    timeout=600,
    secrets=[db_secret],
)
def index_batch(
    document_ids: list[str],
    force: bool = False,
    correlation_id: str | None = None,
) -> dict:
    """Index multiple documents in parallel via spawn_map."""
    results = list(index_document.map(
        [(doc_id,) for doc_id in document_ids],
        kwargs={"force": force, "correlation_id": correlation_id},
    ))
    return aggregate_results(results)
```

| Property | Value |
|----------|-------|
| GPU | None (CPU only) |
| Timeout | 600 seconds |
| Secrets | `vecinita-db-credentials` (for job tracking) |
| Parallelism | Delegates to `index_document.map()` |

### reindex_changed

CPU-only orchestrator that detects changes and re-indexes only modified documents.

```python
@app.function(
    image=image,
    timeout=600,
    secrets=[db_secret],
)
def reindex_changed(
    source_id: str,
    correlation_id: str | None = None,
) -> dict:
    """Compare content hashes, re-index only changed documents."""
    ...
```

| Property | Value |
|----------|-------|
| GPU | None (CPU only) |
| Timeout | 600 seconds |
| Secrets | `vecinita-db-credentials` |
| Hash computation | CPU-bound (SHA-256) |
| Delegation | Changed docs sent to `index_document.map()` |

### rebuild_all

Long-running CPU orchestrator for full vector rebuilds.

```python
@app.function(
    image=image,
    timeout=3600,
    secrets=[db_secret],
)
def rebuild_all(
    reason: str,
    confirm: bool = False,
    correlation_id: str | None = None,
) -> dict:
    """Delete all vectors and rebuild from scratch."""
    ...
```

| Property | Value |
|----------|-------|
| GPU | None (CPU only) |
| Timeout | 3600 seconds (1 hour) |
| Secrets | `vecinita-db-credentials` |
| Safety | Requires `confirm=True` to execute |
| Concurrency | Singleton (checks `indexing_jobs` table for running rebuild) |
| Delegation | Processes in batches of `INDEX_BATCH_SIZE` via `index_document.map()` |

### health_check

Lightweight CPU-only health probe.

```python
@app.function(
    image=image,
    timeout=30,
    retries=1,
    secrets=[db_secret],
)
def health_check() -> dict:
    """Verify database connectivity and model cache."""
    ...
```

| Property | Value |
|----------|-------|
| GPU | None |
| Timeout | 30 seconds |
| Retries | 1 |

## Invocation Patterns

### From Gateway (Python)

The gateway will invoke indexing-worker functions using the same `Function.from_name` pattern used for embedding and scraper workers.

```python
from functools import lru_cache
import modal

@lru_cache(maxsize=8)
def _lookup_indexing_function(function_name: str) -> modal.Function:
    return modal.Function.from_name("vecinita-indexing", function_name)

async def invoke_index_document(document_id: str, force: bool = False) -> dict:
    fn = _lookup_indexing_function("index_document")
    return await asyncio.to_thread(fn.remote, document_id=document_id, force=force)

async def invoke_index_batch(document_ids: list[str]) -> dict:
    fn = _lookup_indexing_function("index_batch")
    return await asyncio.to_thread(fn.remote, document_ids=document_ids)

async def spawn_rebuild_all(reason: str) -> str:
    fn = _lookup_indexing_function("rebuild_all")
    call = await asyncio.to_thread(fn.spawn, reason=reason, confirm=True)
    return call.object_id  # return function_call_id for tracking
```

### From Scraper Worker (Cross-App Call)

```python
index_fn = modal.Function.from_name("vecinita-indexing", "index_document")
result = index_fn.remote(document_id=newly_scraped_doc_id)
```

### From Modal CLI (Development/Operations)

```bash
# Single document
modal run apps/indexing-worker/src/vecinita_indexing/app.py::index_document \
  --document-id "uuid-here"

# Health check
modal run apps/indexing-worker/src/vecinita_indexing/app.py::health_check

# Full rebuild
modal run apps/indexing-worker/src/vecinita_indexing/app.py::rebuild_all \
  --reason "model_change" --confirm
```

## Volumes

### vecinita-embedding-models

| Property | Value |
|----------|-------|
| Name | `vecinita-embedding-models` |
| Type | Modal Volume (persistent) |
| Mount path | `/models` |
| Shared with | `vecinita-embedding` (embedding-worker) |
| Contents | BAAI/bge-small-en-v1.5 model files |
| Create policy | `create_if_missing=True` |
| Estimated size | ~100 MB (bge-small-en-v1.5 ONNX weights) |

Model loading in container:

```python
import os
os.environ["FASTEMBED_CACHE_PATH"] = "/models"
```

This directs fastembed to use the Modal volume as its model cache, avoiding downloads after the first invocation.

## Secrets

### vecinita-db-credentials

| Secret Key | Purpose |
|------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (Render internal URL) |

Created via Modal CLI:
```bash
modal secret create vecinita-db-credentials \
  DATABASE_URL="postgresql://user:pass@host:5432/vecinita?sslmode=require"
```

### Modal Authentication

Modal tokens (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`) are set in the CI/CD environment and on the gateway's Render env vars. They are not explicitly passed to Modal functions — the Modal platform handles authentication internally.

## Deployment

### Deploy Command

```bash
modal deploy apps/indexing-worker/src/vecinita_indexing/app.py
```

### CI/CD Workflow (Planned)

```yaml
name: deploy-indexing-worker
on:
  push:
    branches: [main]
    paths:
      - "apps/indexing-worker/**"

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install modal
      - run: modal deploy apps/indexing-worker/src/vecinita_indexing/app.py
        env:
          MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
          MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
```

## Comparison with Existing Modal Apps

| Property | vecinita-embedding | vecinita-scraper | vecinita-indexing (planned) |
|----------|-------------------|------------------|---------------------------|
| GPU | T4 | None | T4 (index_document only) |
| Functions | embed_query, embed_batch | 5-stage pipeline | 5 functions |
| Batch pattern | Simple batch | Queue-based stages | spawn_map |
| Persistence | None (stateless) | Callbacks to gateway | Direct PostgreSQL writes |
| Timeout (max) | 120s | 1800s | 3600s (rebuild_all) |
| Keep warm | 1 | 0 | 1 (index_document) |
| Volume | vecinita-embedding-models | vecinita-scraper-cache | vecinita-embedding-models (shared) |

## Gateway Configuration (Planned)

New environment variables needed on the gateway:

| Variable | Value | Purpose |
|----------|-------|---------|
| `MODAL_INDEXING_APP_NAME` | `vecinita-indexing` | App name for `Function.from_name` |
| `MODAL_INDEXING_SINGLE_FUNCTION` | `index_document` | Function name override |
| `MODAL_INDEXING_BATCH_FUNCTION` | `index_batch` | Function name override |
| `MODAL_INDEXING_REINDEX_FUNCTION` | `reindex_changed` | Function name override |
| `MODAL_INDEXING_REBUILD_FUNCTION` | `rebuild_all` | Function name override |

## Cross-References

- Architecture: [07-architecture.md](07-architecture.md)
- API contract: [08-api-contract.md](08-api-contract.md)
- Infrastructure plan: [12-infrastructure-plan.md](12-infrastructure-plan.md)
- Gateway Modal integration: [Gateway 13-modal-integration-plan](../gateway/13-modal-integration-plan.md)
- Modal landscape: [Modal current-landscape](../modal/current-landscape.md)

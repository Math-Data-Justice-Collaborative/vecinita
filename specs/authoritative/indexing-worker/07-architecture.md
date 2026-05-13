# Architecture: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker will be a **serverless GPU-accelerated service** deployed on Modal. It uses a function-based architecture where each indexing mode is a separate Modal function, sharing a common GPU-enabled container image. The service has no HTTP server — all invocations are via Modal SDK function calls.

See: [Architecture Diagram](diagrams/architecture.md)

## Architectural Style

| Property | Value |
|----------|-------|
| Style | Serverless functions (FaaS) |
| Platform | Modal |
| Language | Python >=3.11 |
| Framework | LlamaIndex (chunking + embedding abstraction) |
| GPU requirement | Yes (embedding generation) |
| HTTP server | None — Modal function invocation only |
| State | Stateless functions; all state in PostgreSQL |

## Internal Components

### Module Structure (Planned)

```
apps/indexing-worker/
├── src/
│   └── vecinita_indexing/
│       ├── __init__.py
│       ├── app.py              # Modal App definition, function decorators
│       ├── indexer.py           # Core indexing logic (orchestrator)
│       ├── chunker.py           # Document chunking (LlamaIndex SentenceSplitter)
│       ├── embedder.py          # Embedding generation (fastembed adapter)
│       ├── db.py                # PostgreSQL operations (read/write)
│       ├── hasher.py            # Content hash computation and comparison
│       ├── schemas.py           # Pydantic request/response models
│       └── constants.py         # Configuration defaults and constants
├── tests/
│   ├── test_indexer.py
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_db.py
│   └── test_hasher.py
└── pyproject.toml
```

### Component Responsibilities

| Component | Responsibility | Dependencies |
|-----------|---------------|-------------|
| `app.py` | Modal App definition, function decorators, image config, volume mounts, GPU allocation | modal, all internal modules |
| `indexer.py` | Orchestrates the index pipeline: read → chunk → embed → store | chunker, embedder, db, hasher |
| `chunker.py` | Splits document text into overlapping token-based chunks | llama-index-core (`SentenceSplitter`) |
| `embedder.py` | Generates dense vector embeddings from chunk texts | fastembed (or llama-index-embeddings-fastembed) |
| `db.py` | PostgreSQL CRUD: read documents, write vectors, manage hashes and jobs | psycopg2-binary, pgvector |
| `hasher.py` | SHA-256 content hashing and comparison logic | hashlib (stdlib) |
| `schemas.py` | Pydantic models for all request/response types | pydantic |
| `constants.py` | Default configuration values, model identifiers | — |

## Container Image

The Modal container image will be built from `debian_slim` with Python dependencies installed:

```python
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
```

## GPU Allocation Strategy

| Function | GPU | Rationale |
|----------|-----|-----------|
| `index_document` | T4 (or A10G) | Single-document embedding is lightweight; T4 is cost-effective |
| `index_batch` | CPU only | Orchestrator that spawns GPU workers; no direct GPU work |
| `reindex_changed` | CPU only | Hash comparison is CPU-bound; spawns GPU workers for actual indexing |
| `rebuild_all` | CPU only | Orchestrator; spawns GPU workers via `spawn_map` |
| `health_check` | CPU only | No embedding work |

The GPU is allocated at the `index_document` function level because it performs the actual embedding generation. Orchestrator functions (`index_batch`, `reindex_changed`, `rebuild_all`) run on CPU and delegate GPU work via `spawn_map`.

## Concurrency Model

| Concern | Approach |
|---------|----------|
| Single-document | Sequential pipeline within one GPU container |
| Batch parallelism | Modal `spawn_map` — each document gets its own GPU container |
| Rebuild parallelism | `spawn_map` in batches of `INDEX_BATCH_SIZE` to limit concurrent containers |
| Database access | Synchronous psycopg2 (one connection per function invocation) |
| Model loading | Loaded once per container lifecycle (warm containers reuse model) |

### spawn_map Pattern

```python
@app.function(gpu="T4", timeout=300)
def index_document(document_id: str, force: bool = False) -> dict:
    ...

@app.function(timeout=600)
def index_batch(document_ids: list[str], force: bool = False) -> dict:
    results = list(index_document.map(
        [(doc_id, force) for doc_id in document_ids]
    ))
    return aggregate_results(results)
```

## Warm Container Strategy

Modal containers are ephemeral but can be kept warm with `keep_warm`:

| Function | Keep Warm | Rationale |
|----------|-----------|-----------|
| `index_document` | 1 container | Reduce cold start for on-demand indexing |
| Others | 0 | Infrequent; cold start acceptable |

Cold start cost for `index_document`:
1. Container boot: ~5s
2. Python imports: ~3s
3. Model load from volume: ~10-20s (first invocation per container)
4. Total cold start: ~20-30s

Warm invocation: ~200-500ms per document (GPU embedding only).

## Error Handling Strategy

| Layer | Strategy |
|-------|----------|
| Modal function timeout | Function-level timeouts (see [08-api-contract.md](08-api-contract.md)) |
| Modal container crash | Modal auto-retries (configurable `retries` parameter) |
| Database connection | Retry 3x with exponential backoff |
| Embedding model error | Fail fast, surface in `IndexingResult.errors` |
| Partial batch failure | Continue processing remaining documents, aggregate errors |

## Observability (Planned)

| Concern | Tool | Details |
|---------|------|---------|
| Structured logging | `structlog` | JSON-formatted logs with correlation_id, job_id, document_id |
| Function metrics | Modal dashboard | Execution time, GPU utilization, cold starts |
| Job tracking | `agent.indexing_jobs` table | Per-job status, duration, document counts |
| Alerting | Modal webhooks (future) | Notify on job failures exceeding threshold |

## Cross-References

- Modal deployment details: [13-modal-integration-plan.md](13-modal-integration-plan.md)
- Function signatures: [08-api-contract.md](08-api-contract.md)
- Data pipeline details: [06-data-flow.md](06-data-flow.md)

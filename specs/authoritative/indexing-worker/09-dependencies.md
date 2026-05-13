# Dependencies: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker is a **planned** service. All dependencies below are based on design specifications, not existing `pyproject.toml`. Dependencies are chosen to align with the existing embedding-worker patterns.

## Runtime Dependencies

### Core Libraries

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `llama-index-core` | >=0.11 | Text splitting, document abstractions | Yes |
| `llama-index-embeddings-fastembed` | >=0.3 | LlamaIndex adapter for fastembed | Yes |
| `fastembed` | >=0.7.4 | ONNX-optimized embedding model runtime | Yes |
| `modal` | >=1.3.5 | Serverless deployment and GPU provisioning | Yes |
| `psycopg2-binary` | >=2.9.9 | PostgreSQL client driver | Yes |
| `pgvector` | >=0.3 | pgvector Python extension for vector type support | Yes |
| `pydantic` | >=2.6 | Schema validation for request/response models | Yes |
| `structlog` | >=24.1 | Structured JSON logging | No (graceful fallback to stdlib logging) |

### Transitive Dependencies (Notable)

| Package | Brought By | Purpose |
|---------|-----------|---------|
| `onnxruntime` | fastembed | ONNX model execution on CPU/GPU |
| `tokenizers` | fastembed | Fast text tokenization |
| `numpy` | fastembed, pgvector | Array operations for embeddings |
| `huggingface-hub` | fastembed | Model download from HuggingFace Hub |

## Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.0 | Test framework |
| `pytest-asyncio` | >=0.23 | Async test support |
| `pytest-mock` | >=3.12 | Mocking utilities |
| `modal` | >=1.3.5 | Local testing with `modal run` |
| `ruff` | >=0.5 | Linting and formatting |
| `mypy` | >=1.10 | Static type checking |

## Infrastructure Dependencies

| Dependency | Type | Required | Purpose |
|------------|------|----------|---------|
| Modal Platform | Compute | Yes | GPU containers, function orchestration, volumes |
| PostgreSQL (Render Managed) | Database | Yes | Document storage (read), vector storage (write) |
| pgvector extension | DB Extension | Yes | Vector similarity search |
| Modal Volume (`vecinita-embedding-models`) | Storage | Yes | Shared model weight cache |
| GPU (NVIDIA T4 or A10G) | Compute | Yes | Embedding generation |

## Internal Dependencies (Monorepo)

| Dependency | Type | Purpose |
|------------|------|---------|
| `data_mgmt.documents` schema | Database schema | Source of document content (read-only) |
| `agent.vectors` schema | Database schema | Vector storage (owned by this service) |
| Gateway Modal invoker pattern | Integration pattern | Caller uses `Function.from_name` pattern |
| Embedding worker model config | Configuration | Shared `BAAI/bge-small-en-v1.5` model and volume |

## Service Dependencies (Runtime)

| Service | Dependency Type | Required | Fallback |
|---------|----------------|----------|----------|
| PostgreSQL | Hard | Yes | Service cannot function without database |
| Modal Platform | Hard | Yes | Service cannot deploy or execute without Modal |
| Modal Volume (model cache) | Soft | No | Model downloaded on cold start (slower, not cached) |
| Gateway | Soft (caller) | No | Service functions can be invoked directly via Modal CLI |
| Scraper Worker | Soft (caller) | No | Service functions can be invoked independently |

## Dependency Decisions

| Decision | Chosen | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Embedding runtime | fastembed | sentence-transformers | ONNX-optimized, smaller memory footprint, aligns with embedding-worker |
| LlamaIndex abstraction | Yes | Direct fastembed | Provides `SentenceSplitter` and future flexibility for chunking strategies |
| Database driver | psycopg2-binary | asyncpg | Simpler sync driver sufficient for per-invocation connections |
| Schema validation | Pydantic v2 | dataclasses | Richer validation, serialization, aligns with rest of monorepo |

## Planned pyproject.toml

```toml
[project]
name = "vecinita-indexing-worker"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "llama-index-core>=0.11",
    "llama-index-embeddings-fastembed>=0.3",
    "fastembed>=0.7.4",
    "modal>=1.3.5",
    "psycopg2-binary>=2.9.9",
    "pgvector>=0.3",
    "pydantic>=2.6",
    "structlog>=24.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
    "ruff>=0.5",
    "mypy>=1.10",
]
```

## Cross-References

- Embedding worker dependencies: [Embedding Worker README](../embedding-worker/README.md)
- Technical decisions on dependency choices: [10-technical-decisions.md](10-technical-decisions.md)
- Full monorepo dependency inventory: [Dependencies](../dependencies/DEPENDENCIES.md)

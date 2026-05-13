# Data Models: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/schemas.py`, `modal-apps/embedding-modal/src/vecinita/service.py`

## Overview

The embedding worker uses Pydantic models for HTTP API request/response validation and plain dicts for Modal function return values. The service layer bridges both interfaces through `EmbeddingService`.

## Request Models

### QueryRequest

Single-text embedding request. Supports two field names for backward compatibility.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | `str \| None` | One of `query`/`text` | `None` | Primary text field (gateway and legacy clients) |
| `text` | `str \| None` | One of `query`/`text` | `None` | Alias for backend service parity |
| `model` | `str \| None` | No | `None` | Override default embedding model |

Validation: at least one of `query` or `text` must be non-null (`model_validator`).

### BatchQueryRequest

Batch embedding request. Supports two field names for backward compatibility.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `queries` | `list[str] \| None` | One of `queries`/`texts` | `None` | List of queries (preferred) |
| `texts` | `list[str] \| None` | One of `queries`/`texts` | `None` | Alias for gateway fallback |
| `model` | `str \| None` | No | `None` | Override default embedding model |

Validation: at least one non-empty list required; each entry must be non-whitespace (`model_validator`).

## Response Models

### EmbeddingResponse

| Field | Type | Description |
|-------|------|-------------|
| `embedding` | `list[float]` | The embedding vector (384 dimensions for default model) |
| `model` | `str` | Model name used for generation |
| `dimensions` | `int` | Number of dimensions in the vector |

### BatchEmbeddingResponse

| Field | Type | Description |
|-------|------|-------------|
| `embeddings` | `list[list[float]]` | List of embedding vectors |
| `model` | `str` | Model name used for generation |
| `dimensions` | `int` | Number of dimensions in each vector |

### EmbeddingServiceRootResponse

| Field | Type | Description |
|-------|------|-------------|
| `status` | `str` | Liveness flag (`"ok"`) |
| `model` | `str` | Default embedding model for this deployment |

### EmbeddingLivenessResponse

| Field | Type | Description |
|-------|------|-------------|
| `status` | `str` | Liveness flag (`"ok"`) |

## Modal Function Return Shapes

Modal functions return plain dicts (not Pydantic models) for serialization compatibility.

### `embed_query` Return

```json
{
  "embedding": [0.01, -0.02, 0.03, ...],
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384
}
```

| Field | Type | Description |
|-------|------|-------------|
| `embedding` | `list[float]` | 384-dimensional float vector |
| `model` | `str` | Model name (from `DEFAULT_MODEL` constant) |
| `dimension` | `int` | Vector dimensionality |

### `embed_batch` Return

```json
{
  "embeddings": [[0.01, -0.02, ...], [0.03, 0.04, ...]],
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384
}
```

| Field | Type | Description |
|-------|------|-------------|
| `embeddings` | `list[list[float]]` | List of 384-dimensional float vectors |
| `model` | `str` | Model name (from `DEFAULT_MODEL` constant) |
| `dimension` | `int` | Vector dimensionality |

## Service Layer Types

### Embedder Protocol

```python
class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> Any: ...
```

Any object with an `embed(texts) → iterable[vector]` method satisfies this protocol. In production, `fastembed.TextEmbedding` is used.

### Error Types

| Error | Base | Raised When |
|-------|------|-------------|
| `EmptyQueryError` | `ValueError` | Query is empty or whitespace-only |
| `EmbeddingExecutionError` | `RuntimeError` | fastembed backend fails to produce vectors |

## Constants

Source: `modal-apps/embedding-modal/src/vecinita/constants.py`

| Constant | Value | Description |
|----------|-------|-------------|
| `APP_NAME` | `"vecinita-embedding"` | Modal app identifier |
| `MODEL_DIR` | `"/models"` | Mount path for model cache Volume |
| `DEFAULT_MODEL` | `"BAAI/bge-small-en-v1.5"` | Default embedding model |
| `VOLUME_NAME` | `"embedding-models"` | Modal Volume name for cached models |

## Downstream Data Target

Embedding vectors produced by this service are written to PostgreSQL by the gateway as `agent.vectors` rows. The embedding worker itself does **not** write to the database — it returns vectors to the gateway, which handles persistence.

See: [Integration Points](03-integration-points.md)

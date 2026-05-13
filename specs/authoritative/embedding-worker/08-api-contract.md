# API Contract: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/app.py`, `modal-apps/embedding-modal/src/vecinita/api.py`, `modal-apps/embedding-modal/src/vecinita/schemas.py`

## Overview

The embedding worker exposes two interfaces:
1. **Modal function signatures** — Production interface, invoked via `modal.Function.from_name().remote()`
2. **HTTP endpoints** — Development/local interface via FastAPI

## Modal Function Signatures (Production)

### `embed_query`

| Property | Value |
|----------|-------|
| App | `vecinita-embedding` |
| Function | `embed_query` |
| Timeout | 600s |
| Compute | Default CPU |
| Volume | `embedding-models` at `/models` |

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `str` | Yes | Text to embed |

**Output:**

```json
{
  "embedding": [0.0312, -0.0451, 0.0178, ...],
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384
}
```

| Field | Type | Description |
|-------|------|-------------|
| `embedding` | `list[float]` | 384-dimensional vector |
| `model` | `str` | Model identifier |
| `dimension` | `int` | Vector length (always 384) |

**Invocation:**

```python
import modal

fn = modal.Function.from_name("vecinita-embedding", "embed_query")
result = fn.remote("What housing assistance programs exist?")
# result == {"embedding": [...], "model": "BAAI/bge-small-en-v1.5", "dimension": 384}
```

---

### `embed_batch`

| Property | Value |
|----------|-------|
| App | `vecinita-embedding` |
| Function | `embed_batch` |
| Timeout | 600s |
| Compute | Default CPU |
| Volume | `embedding-models` at `/models` |

**Input:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `queries` | `list[str]` | Yes | List of texts to embed |

**Output:**

```json
{
  "embeddings": [[0.0312, ...], [0.0451, ...], ...],
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384
}
```

| Field | Type | Description |
|-------|------|-------------|
| `embeddings` | `list[list[float]]` | List of 384-dimensional vectors |
| `model` | `str` | Model identifier |
| `dimension` | `int` | Vector length (always 384) |

**Invocation:**

```python
import modal

fn = modal.Function.from_name("vecinita-embedding", "embed_batch")
result = fn.remote(["query one", "query two", "query three"])
# result == {"embeddings": [[...], [...], [...]],
#            "model": "BAAI/bge-small-en-v1.5", "dimension": 384}
```

---

## HTTP Endpoints (Development/Local)

### `GET /`

| Property | Value |
|----------|-------|
| Tags | `health` |
| Auth | None |
| Response | `EmbeddingServiceRootResponse` |

**Response (200):**

```json
{"status": "ok", "model": "BAAI/bge-small-en-v1.5"}
```

---

### `GET /health`

| Property | Value |
|----------|-------|
| Tags | `health` |
| Auth | None |
| Response | `EmbeddingLivenessResponse` |

**Response (200):**

```json
{"status": "ok"}
```

---

### `POST /embed`

| Property | Value |
|----------|-------|
| Tags | `embedding` |
| Auth | None |
| Request body | `QueryRequest` |
| Response | `EmbeddingResponse` |

**Request:**

```json
{"query": "What housing assistance programs exist?"}
```

or (alias):

```json
{"text": "What housing assistance programs exist?"}
```

**Response (200):**

```json
{
  "embedding": [0.0312, -0.0451, 0.0178, ...],
  "model": "BAAI/bge-small-en-v1.5",
  "dimensions": 384
}
```

**Errors:**

| Status | Cause |
|--------|-------|
| 422 | Empty or whitespace-only query |
| 500 | Backend embedding failure |

---

### `POST /embed/batch`

| Property | Value |
|----------|-------|
| Tags | `embedding` |
| Auth | None |
| Request body | `BatchQueryRequest` |
| Response | `BatchEmbeddingResponse` |

**Request:**

```json
{"queries": ["query one", "query two"]}
```

or (alias):

```json
{"texts": ["text one", "text two"]}
```

**Response (200):**

```json
{
  "embeddings": [[0.0312, ...], [0.0451, ...]],
  "model": "BAAI/bge-small-en-v1.5",
  "dimensions": 384
}
```

**Errors:**

| Status | Cause |
|--------|-------|
| 422 | Empty list, or any entry is empty/whitespace |
| 500 | Backend embedding failure |

---

### `POST /embed-batch`

Alias for `POST /embed/batch` — exists for backward compatibility with gateway clients that use the hyphenated path.

Same request/response contract as `POST /embed/batch`.

---

## Key Differences: Modal vs HTTP Response Fields

| Field | Modal Function | HTTP Endpoint |
|-------|---------------|---------------|
| Vector(s) | `embedding` / `embeddings` | `embedding` / `embeddings` |
| Model | `model` | `model` |
| Dimensions | `dimension` (singular) | `dimensions` (plural) |

The singular/plural difference in the dimension field is a known divergence between the Modal function return dict and the Pydantic response model.

See: [Data Models](02-data-models.md) | [Integration Points](03-integration-points.md)

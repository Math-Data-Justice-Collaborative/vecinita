# Data Flow: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/app.py`, `apis/gateway/src/services/modal/invoker.py`

## Overview

Data flows through the embedding worker in a simple linear pipeline: text enters via Modal function invocation, is converted to a dense vector by fastembed, and the vector is returned to the caller.

## Single Embedding Flow

| Stage | Component | Input | Output | Notes |
|-------|-----------|-------|--------|-------|
| 1. Invoke | Gateway (`invoker.py`) | User question `str` | Modal RPC call | `fn.remote(text)` |
| 2. Receive | Modal runtime | Deserialized `str` | Function args | Modal handles serialization |
| 3. Load model | `load_runtime_model()` | — | `TextEmbedding` instance | Cached after first call |
| 4. Warmup | `warmup_embedding_model()` | `["warmup"]` | Warmed model | Ensures weights are loaded |
| 5. Embed | `model.embed([text])` | `list[str]` | `ndarray` (384-dim) | fastembed inference |
| 6. Serialize | `.tolist()` | `ndarray` | `list[float]` | NumPy → Python conversion |
| 7. Shape | `_embed_query_impl()` | Vector + metadata | `dict` | `{embedding, model, dimension}` |
| 8. Return | Modal runtime | `dict` | Serialized response | Modal handles return transport |
| 9. Consume | Gateway | `dict` | Vector for PostgreSQL | Gateway writes to `agent.vectors` |

## Batch Embedding Flow

| Stage | Component | Input | Output | Notes |
|-------|-----------|-------|--------|-------|
| 1. Invoke | Gateway (`invoker.py`) | `list[str]` | Modal RPC call | `fn.remote(texts)` |
| 2. Receive | Modal runtime | Deserialized `list[str]` | Function args | — |
| 3. Load model | `load_runtime_model()` | — | `TextEmbedding` instance | Cached |
| 4. Embed | `model.embed(queries)` | `list[str]` | `list[ndarray]` | Batch inference |
| 5. Serialize | `.tolist()` per vector | `list[ndarray]` | `list[list[float]]` | — |
| 6. Shape | `_embed_batch_impl()` | Vectors + metadata | `dict` | `{embeddings, model, dimension}` |
| 7. Return | Modal runtime | `dict` | Serialized response | — |
| 8. Consume | Gateway | `dict` | Vectors for PostgreSQL | Batch write to `agent.vectors` |

## Data Transformation Summary

```
Input:   "What housing assistance programs exist?"     (str, variable length)
   ↓
Tokenize: fastembed tokenizer (BAAI/bge-small-en-v1.5)
   ↓
Encode:  Transformer forward pass (CPU)
   ↓
Output:  [0.0312, -0.0451, 0.0178, ..., 0.0089]       (list[float], exactly 384 elements)
```

## Data Characteristics

| Property | Value |
|----------|-------|
| Input type | UTF-8 text (any length) |
| Output type | `list[float]` (384 dimensions) |
| Model | BAAI/bge-small-en-v1.5 |
| Encoding | Dense float32 vectors |
| Normalization | Model-dependent (bge-small normalizes by default) |
| Determinism | Same input → same output (deterministic model) |

## Logging and Observability

The embedding worker logs input/output summaries for tracing:

| Log Point | Data Logged | Truncation |
|-----------|-------------|-----------|
| `embed_query` input | `char_len`, `preview` (first 240 chars) | Newlines escaped, long text truncated |
| `embed_query` output | `model`, `dimension`, `embedding_head` (first 4 floats) | — |
| `embed_batch` input | `batch_size`, `total_char_len`, `first_query_preview` | First query only |
| `embed_batch` output | `model`, `dimension`, `num_vectors`, `first_vector_head` | First vector head only |

Source: `_preview_text()` and `_preview_floats()` in `modal-apps/embedding-modal/src/vecinita/app.py`

## Data at Rest

| Storage | What | Lifetime |
|---------|------|----------|
| Modal Volume (`embedding-models`) | Cached model weights (~100MB) | Persistent until manually deleted |
| PostgreSQL (`agent.vectors`) | Generated embedding vectors | Application lifetime (gateway-managed) |

The embedding worker itself stores no application data — only model cache files on the Modal Volume.

See: [Data Models](02-data-models.md) | [Architecture](07-architecture.md) | [Data Flow Diagram](diagrams/data-flow.md)

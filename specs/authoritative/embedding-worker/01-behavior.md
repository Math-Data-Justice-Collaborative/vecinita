# Behavior: Embedding Worker
> Auto-generated: 2026-05-12

## Purpose

The embedding worker is a **serverless text embedding utility** deployed on Modal that converts natural-language text into dense vector representations using the fastembed library. It exposes two Modal functions (`embed_query`, `embed_batch`) invoked by the gateway via `modal.Function.from_name().remote()`.

Source: `modal-apps/embedding-modal/src/vecinita/app.py`

## Core Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| 1 | Single-text embedding | Convert one text string into a 384-dimensional float vector |
| 2 | Batch embedding | Convert a list of text strings into a list of 384-dimensional float vectors |
| 3 | Model management | Load and cache BAAI/bge-small-en-v1.5 via fastembed on a Modal Volume |
| 4 | Input validation | Reject empty or whitespace-only queries via `EmbeddingService` |
| 5 | Response shaping | Return structured dicts with `embedding(s)`, `model`, and `dimension(s)` |

## Key Behaviors

### Single Embedding (`embed_query`)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `fn.remote(text)` | Load model → embed single text → serialize | `{"embedding": [...], "model": "...", "dimension": 384}` |
| Empty/whitespace text | `EmptyQueryError` raised by service layer | Error propagated to caller |
| Model not cached | fastembed downloads BAAI/bge-small-en-v1.5 to Volume | ~5-10s cold start, then cached |

### Batch Embedding (`embed_batch`)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| Gateway calls `fn.remote(texts)` | Load model → embed all texts → serialize | `{"embeddings": [[...], ...], "model": "...", "dimension": 384}` |
| Any empty query in batch | `EmptyQueryError` with failing indices | Error propagated to caller |
| Backend failure | `EmbeddingExecutionError` wraps underlying exception | Error propagated to caller |

### HTTP API (Development/Local)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| `GET /` | Return service status and default model | `{"status": "ok", "model": "BAAI/bge-small-en-v1.5"}` |
| `GET /health` | Liveness probe | `{"status": "ok"}` |
| `POST /embed` | Embed single query via `query` or `text` field | `EmbeddingResponse` |
| `POST /embed/batch` | Embed batch via `queries` or `texts` field | `BatchEmbeddingResponse` |
| `POST /embed-batch` | Alias for `/embed/batch` (gateway compat) | `BatchEmbeddingResponse` |

## Service Boundaries

| Boundary | In Scope | Out of Scope |
|----------|----------|-------------|
| Embedding generation | Text → vector conversion | Storing vectors in database |
| Model lifecycle | Loading, caching, warmup | Training, fine-tuning |
| Input validation | Empty/whitespace rejection | Semantic content validation |
| Transport | Modal function invocation, FastAPI HTTP (dev) | WebSocket, gRPC |
| Storage | Model cache on Modal Volume | Application data persistence |

## Operational Characteristics

| Metric | Value |
|--------|-------|
| Cold start | ~5-10s (model load from Volume) |
| Warm latency | <2s per query |
| Timeout | 600s per function invocation |
| Invocations/day | 50-500 (typical) |
| Output dimension | 384 (BAAI/bge-small-en-v1.5) |
| Compute | Default CPU (no GPU required for fastembed) |

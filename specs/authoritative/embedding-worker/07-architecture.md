# Architecture: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/`

## Overview

The embedding worker is a serverless function application deployed on Modal. It consists of two Modal functions (`embed_query`, `embed_batch`) backed by a shared service layer and the fastembed library. A FastAPI HTTP interface exists for local development but is not used in production.

## Component Architecture

| Component | File | Responsibility |
|-----------|------|---------------|
| Modal entrypoint | `src/vecinita/app.py` | Defines Modal `App`, functions, image, Volume |
| Service layer | `src/vecinita/service.py` | Input validation, response shaping, `Embedder` protocol |
| Schemas | `src/vecinita/schemas.py` | Pydantic request/response models (HTTP API) |
| FastAPI factory | `src/vecinita/api.py` | HTTP application factory (local dev) |
| Constants | `src/vecinita/constants.py` | Shared config: app name, model, paths |

## Layers

```
┌──────────────────────────────────────────────┐
│  Gateway (caller)                            │
│  modal.Function.from_name().remote()         │
└──────────────┬───────────────────────────────┘
               │ Modal SDK RPC
┌──────────────▼───────────────────────────────┐
│  Modal Runtime                               │
│  ┌─────────────────────────────────────────┐ │
│  │  embed_query / embed_batch  (app.py)    │ │
│  │  ┌───────────────────────────────────┐  │ │
│  │  │  load_runtime_model()             │  │ │
│  │  │  → create_text_embedding()        │  │ │
│  │  │  → warmup_embedding_model()       │  │ │
│  │  └───────────────────────────────────┘  │ │
│  │  ┌───────────────────────────────────┐  │ │
│  │  │  fastembed.TextEmbedding          │  │ │
│  │  │  (BAAI/bge-small-en-v1.5)        │  │ │
│  │  └───────────────────────────────────┘  │ │
│  └─────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │  Modal Volume: /models                  │ │
│  │  (cached model weights)                 │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

## Modal App Configuration

| Setting | Value | Source |
|---------|-------|--------|
| App name | `vecinita-embedding` | `constants.APP_NAME` |
| Python version | 3.11 | `Image.debian_slim(python_version="3.11")` |
| Base image | `debian_slim` | Modal built-in |
| Pip packages | `fastembed>=0.7.4` | Image builder |
| Volume name | `embedding-models` | `constants.VOLUME_NAME` |
| Volume mount | `/models` | `constants.MODEL_DIR` |
| Function timeout | 600s | `@app.function(timeout=600)` |
| Compute | Default CPU | No GPU/memory override |

## Function Architecture

Both functions follow the same pattern:

1. **Load model** — `load_runtime_model()` creates a `TextEmbedding` instance and runs a warmup query
2. **Embed** — Call `model.embed(texts)` which returns numpy arrays
3. **Serialize** — Convert arrays to Python lists via `.tolist()`
4. **Log** — Log input preview and output summary
5. **Return** — Return structured dict

Model loading happens on every invocation (no persistent state between invocations within the current implementation). The Modal Volume ensures model weights don't need re-downloading.

## Service Layer Architecture

The `EmbeddingService` class (used by the HTTP API) adds:

| Feature | Implementation |
|---------|---------------|
| Input validation | Strip + empty check, per-index batch validation |
| Error types | `EmptyQueryError`, `EmbeddingExecutionError` |
| Embedder protocol | `Protocol` class — any `embed(texts)` method works |
| Response models | Returns Pydantic `EmbeddingResponse` / `BatchEmbeddingResponse` |

## HTTP API Architecture (Development Only)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Service heartbeat + default model |
| `/health` | GET | Liveness probe |
| `/embed` | POST | Single embedding |
| `/embed/batch` | POST | Batch embedding |
| `/embed-batch` | POST | Alias for `/embed/batch` (gateway compat) |

The HTTP API is created via `create_app(service)` factory pattern with dependency injection of the `EmbeddingService`.

## Concurrency Model

| Aspect | Behavior |
|--------|----------|
| Modal scaling | Auto-scaled containers per demand |
| Per-container | Single-threaded (one request per container instance) |
| Cold start | ~5-10s (model load + warmup) |
| Warm invocation | <2s |
| Timeout | 600s hard limit per invocation |

## Logging Architecture

Source: `_ensure_vecinita_loggers_visible()` in `app.py`

- Package logger `vecinita` set to `INFO` level
- `StreamHandler` to stderr (captured by Modal)
- Formatter: `%(levelname)s %(name)s %(message)s`
- `propagate = False` to avoid duplicate logs

See: [Data Flow](06-data-flow.md) | [Infrastructure Plan](12-infrastructure-plan.md) | [Architecture Diagram](diagrams/architecture.md)

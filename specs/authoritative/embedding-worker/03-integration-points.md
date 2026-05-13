# Integration Points: Embedding Worker
> Auto-generated: 2026-05-12

Source: `modal-apps/embedding-modal/src/vecinita/app.py`, `apis/gateway/src/services/modal/invoker.py`

## Overview

The embedding worker has a minimal integration surface: it receives invocations from the gateway and returns vectors. It does **not** directly connect to databases, external APIs, or other Modal apps.

## Integration Map

| Direction | Partner | Protocol | Description |
|-----------|---------|----------|-------------|
| ← Inbound | Gateway | Modal SDK (`fn.remote()`) | Receives text for embedding |
| → Outbound | None | — | Returns vectors to caller; no direct DB writes |

## Inbound: Gateway → Embedding Worker

### Invocation Pattern

The gateway resolves deployed Modal functions using `modal.Function.from_name()` with LRU caching, then calls `.remote()` for synchronous results.

Source: `apis/gateway/src/services/modal/invoker.py`

```python
fn = modal.Function.from_name(app_name, function_name)
result = fn.remote(text)  # blocking call
```

### Function Resolution

| Gateway Function | Modal App | Modal Function | Input | Output |
|-----------------|-----------|---------------|-------|--------|
| `invoke_modal_embedding_single` | `vecinita-embedding` | `embed_query` | `str` | `dict` |
| `invoke_modal_embedding_batch` | `vecinita-embedding` | `embed_batch` | `list[str]` | `dict` |

### Gateway Environment Variables (caller-side)

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODAL_EMBEDDING_APP_NAME` | `vecinita-embedding` | Modal app name for function lookup |
| `MODAL_EMBEDDING_SINGLE_FUNCTION` | `embed_query` | Function name for single embedding |
| `MODAL_EMBEDDING_BATCH_FUNCTION` | `embed_batch` | Function name for batch embedding |
| `MODAL_FUNCTION_INVOCATION` | (empty = off) | Enable/disable Modal SDK invocation |
| `MODAL_TOKEN_ID` | — | SDK authentication |
| `MODAL_TOKEN_SECRET` | — | SDK authentication |

### Invocation Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| Off | `MODAL_FUNCTION_INVOCATION` unset or `false` | Gateway uses HTTP fallback |
| Auto | `MODAL_FUNCTION_INVOCATION=auto` | Uses Modal SDK if tokens present, else HTTP |
| On | `MODAL_FUNCTION_INVOCATION=true` | Always uses Modal SDK (requires tokens) |

### Error Handling

| Error Scenario | Gateway Behavior |
|---------------|-----------------|
| Modal function timeout (>600s) | `TimeoutError` propagated to caller |
| Modal SDK not installed | `RuntimeError("modal SDK is unavailable")` |
| Missing Modal tokens with `MODAL_FUNCTION_INVOCATION=on` | `RuntimeError` at startup (fail-fast policy) |
| `EmptyQueryError` from worker | Error dict returned to gateway |
| `EmbeddingExecutionError` from worker | Error dict returned to gateway |

## Outbound: Embedding Worker → PostgreSQL (Indirect)

The embedding worker does **not** write directly to PostgreSQL. The data flow is:

1. Gateway calls `embed_query` / `embed_batch` via Modal SDK
2. Embedding worker returns vector(s)
3. Gateway writes vectors to `agent.vectors` table in PostgreSQL

This separation keeps the embedding worker stateless and focused solely on vector generation.

## Modal Volume Integration

| Resource | Name | Mount Path | Purpose |
|----------|------|-----------|---------|
| Modal Volume | `embedding-models` | `/models` | Cache downloaded fastembed model files |

The Volume is created automatically (`create_if_missing=True`) on first deployment. Model files persist across function invocations, eliminating repeated downloads.

## No External Service Calls

The embedding worker makes no outbound network calls beyond:
- fastembed model download (first run only, cached to Volume)
- Modal platform communication (implicit, handled by Modal runtime)

See: [Architecture](07-architecture.md) | [Modal Integration Plan](13-modal-integration-plan.md)

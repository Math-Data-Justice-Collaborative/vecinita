# Data Management API — Modal Integration Plan

> Auto-generated: 2026-05-12

## Overview

The data-management API is **not** deployed on Modal itself. Instead, it
**invokes** Modal-deployed functions on the scraper, embedding, and model apps
via the Modal Python SDK when `MODAL_FUNCTION_INVOCATION` is enabled. This
plan documents the invocation patterns and configuration.

## Modal Apps Invoked

| App | Default Name | Functions Called | Purpose |
|-----|-------------|-----------------|---------|
| Scraper | `vecinita-scraper` | `health_check` | Health aggregation |
| Embedding | `vecinita-embedding` | `embed_query`, `embed_batch` | Text embedding |
| Model | `vecinita-model` | `predict`, `chat_completion` | Text classification/prediction |

## Invocation Pattern

The `modal_invoker.py` module provides the SDK bridge:

1. **Function lookup:** `modal.Function.from_name(app_name, function_name)` — LRU-cached (maxsize=32)
2. **Remote call:** `.remote(args)` — synchronous Modal SDK call
3. **Async bridge:** Wrapped in `asyncio.to_thread()` to avoid blocking the FastAPI event loop
4. **Routing decision:** `modal_function_invocation_enabled()` checks `MODAL_FUNCTION_INVOCATION` env var

**Source:** `apis/data-management-api/packages/service-clients/service_clients/modal_invoker.py`

### Routing Logic

```
MODAL_FUNCTION_INVOCATION=""       → HTTP (disabled)
MODAL_FUNCTION_INVOCATION="auto"   → Modal if MODAL_TOKEN_ID + MODAL_TOKEN_SECRET set, else HTTP
MODAL_FUNCTION_INVOCATION="1"      → Modal (forced)
MODAL_FUNCTION_INVOCATION="http"   → HTTP (forced)
```

## Environment Variables

| Variable | Source | Required | Default |
|----------|--------|----------|---------|
| `MODAL_FUNCTION_INVOCATION` | Render env / `.env` | no | `""` (disabled) |
| `MODAL_TOKEN_ID` | Render env (sync: false) | when Modal enabled | — |
| `MODAL_TOKEN_SECRET` | Render env (sync: false) | when Modal enabled | — |
| `MODAL_ENVIRONMENT_NAME` | Render env | no | `""` |
| `MODAL_SCRAPER_APP_NAME` | Render env | no | `vecinita-scraper` |
| `MODAL_SCRAPER_HEALTH_FUNCTION` | Render env | no | `health_check` |
| `MODAL_EMBEDDING_APP_NAME` | Render env | no | `vecinita-embedding` |
| `MODAL_EMBEDDING_SINGLE_FUNCTION` | Render env | no | `embed_query` |
| `MODAL_EMBEDDING_BATCH_FUNCTION` | Render env | no | `embed_batch` |
| `MODAL_MODEL_APP_NAME` | Render env | no | `vecinita-model` |
| `MODAL_MODEL_PREDICT_FUNCTION` | Render env | no | `predict` |
| `MODAL_MODEL_CHAT_FUNCTION` | Render env | no | `chat_completion` |

**Source:** `apis/data-management-api/packages/shared-config/shared_config/__init__.py` (`BaseServiceSettings`)

## Correlation / Tracing

Modal invocations log a correlation ID from (in priority order):
`X_REQUEST_ID` → `CORRELATION_ID` → `VECINITA_TRACE_ID` → random UUID.

**Source:** `modal_invoker.py` (`_correlation_id()`)

## Cross-reference

- [Modal Landscape](../modal/current-landscape.md)

## Related Documents

- [Integration Points](03-integration-points.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

# Data Management API — Integration Points

> Auto-generated: 2026-05-12

## Overview

The data-management API is an integration hub — it receives browser traffic from
the SPA and fans out to three upstream backend services (scraper, embedding,
model) via HTTP or Modal SDK. It also validates its Postgres connection at
startup and on health checks.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| data-management SPA | HTTP/HTTPS | inbound | Browser CRUD for jobs, embed, predict | `ALLOWED_ORIGINS` |
| Scraper service | HTTP | outbound | Job proxy (`/jobs`), health checks | `SCRAPER_SERVICE_BASE_URL` |
| Scraper service | Modal SDK | outbound | Health check when `MODAL_FUNCTION_INVOCATION` enabled | `MODAL_SCRAPER_APP_NAME`, `MODAL_SCRAPER_HEALTH_FUNCTION` |
| Embedding service | HTTP | outbound | `/embed` delegation | `EMBEDDING_SERVICE_BASE_URL` |
| Embedding service | Modal SDK | outbound | `/embed` when `MODAL_FUNCTION_INVOCATION` enabled | `MODAL_EMBEDDING_APP_NAME`, `MODAL_EMBEDDING_SINGLE_FUNCTION` |
| Model service | HTTP | outbound | `/predict` delegation | `MODEL_SERVICE_BASE_URL` |
| Model service | Modal SDK | outbound | `/predict` when `MODAL_FUNCTION_INVOCATION` enabled | `MODAL_MODEL_APP_NAME`, `MODAL_MODEL_PREDICT_FUNCTION` |
| Gateway | HTTP proxy | inbound | Gateway may proxy to this service | Gateway `render.yaml` routing |

## External Integrations

| Provider | Protocol | Purpose | Auth | Config |
|----------|----------|---------|------|--------|
| Render PostgreSQL | TCP (psycopg2) | `DATABASE_URL` validation at startup | Connection string | `DATABASE_URL` (fromDatabase) |
| Modal | Python SDK | Remote function invocation for scraper/embed/model | Token pair | `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` |

## Integration Details

### Scraper Job Proxy

- **Endpoint:** `SCRAPER_SERVICE_BASE_URL/jobs[/{subpath}]`
- **Request format:** Passthrough — method, path, query, body, and Authorization header forwarded verbatim
- **Response format:** Upstream response mirrored (status + JSON body); POST enriched with `source_of_truth`
- **Error handling:** `ScraperUpstreamError` raised on 5xx (maps to 502) or connectivity failure (maps to 503)
- **Retry/timeout policy:** 60s timeout per request (`ScraperClient.timeout`); no automatic retry
- **Source:** `apis/data-management-api/packages/service-clients/service_clients/scraper_client.py`

### Embedding Delegation

- **Endpoint/Function:** `EMBEDDING_SERVICE_BASE_URL/embed` or Modal `embed_query` function
- **Request format:** `EmbedRequest { text, model_version }`
- **Response format:** `EmbedResponse { embedding, model_version }`
- **Error handling:** `EmbeddingUpstreamError` — 5xx→502, connectivity→503, Modal failures→503
- **Retry/timeout policy:** 30s timeout; no automatic retry
- **Source:** `apis/data-management-api/packages/service-clients/service_clients/embedding_client.py`

### Model Prediction Delegation

- **Endpoint/Function:** `MODEL_SERVICE_BASE_URL/predict` or Modal `predict` function
- **Request format:** `PredictRequest { text, model_version }`
- **Response format:** `PredictResponse { label, score, model_version }`
- **Error handling:** `ModelUpstreamError` — 5xx→502, connectivity→503, Modal failures→503
- **Retry/timeout policy:** 30s timeout; no automatic retry
- **Source:** `apis/data-management-api/packages/service-clients/service_clients/model_client.py`

### Modal Function Invocation

- **Mechanism:** `modal.Function.from_name(app, function).remote()` via `asyncio.to_thread`
- **Routing decision:** `MODAL_FUNCTION_INVOCATION` env var — `auto` checks for token pair, `1`/`true` forces SDK, `0`/`http` forces HTTP
- **Function lookup caching:** LRU cache (maxsize=32) on `(app_name, function_name, environment_name)`
- **Source:** `apis/data-management-api/packages/service-clients/service_clients/modal_invoker.py`

### DATABASE_URL Guard

- **Mechanism:** `validate_canonical_database_url()` checks scheme is `postgres`/`postgresql` and value does not contain mock/placeholder tokens
- **Strict mode:** Enabled automatically on Render (`RENDER` or `RENDER_SERVICE_ID` env var set)
- **Source:** `apis/data-management-api/apps/backend/vecinita_dm_api/corpus_db_guard.py`

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)

# Integration Points: Gateway
> Auto-generated: 2026-05-12

## Overview

The gateway sits at the center of the Vecinita service mesh, proxying and orchestrating between frontends, internal services, and Modal serverless functions.

See [diagrams/integration-points.md](diagrams/integration-points.md) for the connectivity graph.

## Outbound Integrations (gateway → service)

### Agent Service

| Property | Value |
|----------|-------|
| Protocol | HTTP REST (httpx AsyncClient) |
| Base URL | `AGENT_SERVICE_URL` (default `http://localhost:8000`) |
| Purpose | Q&A proxy, SSE streaming, config fetch |
| Auth | None (internal mesh) |
| Timeout | `AGENT_TIMEOUT` (default 180s), `AGENT_STREAM_TIMEOUT` (180s) |
| Connection pool | max_connections=100, max_keepalive=20 |
| Error handling | 504 on timeout, 503 on connection error, upstream status codes forwarded |
| Health probe | `GET {base}/health` with 2s timeout |
| Source | `apis/gateway/src/api/router_ask.py` |

### Modal — Embedding Functions

| Property | Value |
|----------|-------|
| Protocol | Modal SDK (`Function.from_name().remote()`) |
| App | `MODAL_EMBEDDING_APP_NAME` (default `vecinita-embedding`) |
| Functions | `embed_query` (single), `embed_batch` (batch) |
| Fallback | HTTP proxy to `EMBEDDING_SERVICE_URL` when `MODAL_FUNCTION_INVOCATION` is off |
| Auth | `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` |
| Source | `apis/gateway/src/services/modal/invoker.py` |

### Modal — Scraper Functions

| Property | Value |
|----------|-------|
| Protocol | Modal SDK |
| App | `MODAL_SCRAPER_APP_NAME` (default `vecinita-scraper`) |
| Functions | `modal_scrape_job_submit`, `modal_scrape_job_get`, `modal_scrape_job_list`, `modal_scrape_job_cancel`, `trigger_reindex` |
| Spawn pattern | `trigger_reindex` uses `.spawn()` (non-blocking), others use `.remote()` |
| Auth | `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` |
| Source | `apis/gateway/src/services/modal/invoker.py`, `apis/gateway/src/api/router_modal_jobs.py` |

### Modal — Model Functions

| Property | Value |
|----------|-------|
| Protocol | Modal SDK |
| App | `MODAL_MODEL_APP_NAME` (default `vecinita-model`) |
| Functions | `chat_completion` |
| Source | `apis/gateway/src/services/modal/invoker.py` |

### PostgreSQL

| Property | Value |
|----------|-------|
| Protocol | TCP (psycopg2 synchronous connections) |
| URL | `DATABASE_URL` |
| Purpose | Documents read (overview, preview, tags), scraper job persistence |
| Connection | Per-request via `psycopg2.connect()` with `connect_timeout=5` |
| Statement timeout | 30s default |
| Health probe | TCP socket probe to host:port with 2s timeout |
| Source | `apis/gateway/src/api/router_documents.py`, `apis/gateway/src/services/ingestion/` |

## Inbound Integrations (service → gateway)

### Chat Frontend

| Property | Value |
|----------|-------|
| Protocol | HTTP + SSE |
| Endpoints consumed | `/api/v1/ask`, `/api/v1/ask/stream`, `/api/v1/ask/config`, `/api/v1/documents/*` |
| Auth | Bearer token (when `ENABLE_AUTH=true`) |
| CORS | `ALLOWED_ORIGINS` (default `localhost:5173,5174,4173`) |

### Data Management Frontend

| Property | Value |
|----------|-------|
| Protocol | HTTP |
| Endpoints consumed | `/api/v1/documents/*`, `/api/v1/scrape/*`, `/api/v1/modal-jobs/*` |
| Auth | Bearer token |

### Modal Scraper Workers (internal pipeline)

| Property | Value |
|----------|-------|
| Protocol | HTTP (internal, not in OpenAPI schema) |
| Endpoints consumed | `/api/v1/internal/scraper-pipeline/*` |
| Auth | `X-Scraper-Pipeline-Ingest-Token` header (from `SCRAPER_API_KEYS`) |
| Purpose | Persist pipeline state (job status, crawled URLs, chunks, embeddings) back to gateway Postgres |
| Source | `apis/gateway/src/api/router_scraper_pipeline_ingest.py` |

## Error Handling Summary

| Integration | Timeout | Retry | Circuit Breaker |
|-------------|---------|-------|-----------------|
| Agent HTTP | 180s (configurable) | None (client retries) | None |
| Modal SDK | Function-specific | Modal SDK internal | None |
| PostgreSQL | 5s connect, 30s statement | None | Fail-closed for corpus projection errors |
| Embedding HTTP | 30s (single), 60s (batch) | None | Blocks Modal-hosted URLs without SDK config |

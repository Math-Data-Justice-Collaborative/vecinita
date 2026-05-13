# Data Management API — Architecture

> Auto-generated: 2026-05-12

## Overview

The data-management API follows a **thin proxy / BFF (Backend For Frontend)**
architecture. It is a lightweight FastAPI application that accepts browser
requests from the data-management SPA and dispatches them to upstream services
via typed async clients. The service itself is stateless and contains no
business logic beyond routing, metadata enrichment, and configuration validation.

## Architecture Style

**Thin API proxy / BFF** — the service owns no domain logic or data; it exists
to provide a single CORS-safe HTTP origin for the SPA and to abstract Modal vs
HTTP routing decisions from the browser.

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| Application factory | Create FastAPI app, wire middleware and routers | `apis/data-management-api/apps/backend/vecinita_dm_api/app.py` |
| Health router | Aggregate health check (DB guard + scraper) | `apis/data-management-api/apps/backend/vecinita_dm_api/routers/health.py` |
| Jobs proxy router | Forward `/jobs` CRUD to scraper | `apis/data-management-api/apps/backend/vecinita_dm_api/routers/jobs_proxy.py` |
| Ingest router | `/embed` and `/predict` delegation | `apis/data-management-api/apps/backend/vecinita_dm_api/routers/ingest.py` |
| Response mapper | Convert httpx responses to Starlette responses | `apis/data-management-api/apps/backend/vecinita_dm_api/routers/responses.py` |
| Corpus conflict resolver | Deterministic last-writer-wins for corpus writes | `apis/data-management-api/apps/backend/vecinita_dm_api/corpus_conflict.py` |
| Corpus DB guard | Validate DATABASE_URL at startup | `apis/data-management-api/apps/backend/vecinita_dm_api/corpus_db_guard.py` |
| ScraperClient | Async HTTP client for scraper service | `apis/data-management-api/packages/service-clients/service_clients/scraper_client.py` |
| EmbeddingClient | Async HTTP/Modal client for embedding service | `apis/data-management-api/packages/service-clients/service_clients/embedding_client.py` |
| ModelClient | Async HTTP/Modal client for model service | `apis/data-management-api/packages/service-clients/service_clients/model_client.py` |
| Modal invoker | Modal SDK function lookup and invocation helpers | `apis/data-management-api/packages/service-clients/service_clients/modal_invoker.py` |
| Shared config | `BaseServiceSettings` (pydantic-settings) | `apis/data-management-api/packages/shared-config/shared_config/__init__.py` |
| Shared schemas | `EmbedRequest/Response`, `PredictRequest/Response`, `ScrapeRequest/Result` | `apis/data-management-api/packages/shared-schemas/shared_schemas/` |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | Python 3.11 |
| Framework | FastAPI 0.110+ |
| Entry point | `vecinita_dm_api.app:create_app` (app factory) |
| ASGI server | Uvicorn (standard extras) |
| Default port | 8000 (local) / 10000 (Render) |
| Health check | `GET /health` |

**Note:** In the current Render deployment, the production image runs the
**scraper server** (`vecinita_scraper.api.server:create_app`) rather than the
DM API app factory directly. The scraper image is built from
`modal-apps/scraper/Dockerfile`. See [Render Integration](14-render-integration-plan.md).

## Concurrency Model

- **Async/await:** All route handlers and service clients are `async`. The
  event loop handles concurrent HTTP requests natively via Uvicorn's ASGI server.
- **Modal SDK bridge:** Modal's synchronous `.remote()` calls are wrapped in
  `asyncio.to_thread()` to avoid blocking the event loop.
- **No worker processes:** Single-process Uvicorn; Render starter plan provides
  one instance.
- **No background tasks:** All work is synchronous request-response; long-running
  scrape work is offloaded to the scraper service / Modal.

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

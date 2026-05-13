# Architecture: Gateway
> Auto-generated: 2026-05-12

See [diagrams/architecture.md](diagrams/architecture.md) for the component diagram.

## Architectural Style

**Microservice** — async Python web service acting as an API gateway and BFF (backend-for-frontend). Single FastAPI application with modular routers, deployed as a Render web service.

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | ≥3.10 (Dockerfile uses 3.11) |
| Framework | FastAPI | Latest |
| ASGI server | Uvicorn | Latest |
| HTTP client | httpx | 0.28.1 |
| Database driver | psycopg2-binary | Latest |
| Serverless SDK | Modal | ≥1.3.5 |
| Validation | Pydantic | v2 |
| Config loading | python-dotenv, PyYAML | Latest |

## Internal Components

### Middleware Stack (outermost → innermost)

Middleware is applied in reverse declaration order per Starlette convention.

| Order | Middleware | Source | Purpose |
|-------|-----------|--------|---------|
| 1 (outermost) | `CorrelationIdMiddleware` | `middleware.py` | Assign/propagate `X-Correlation-ID` |
| 2 | `AuthenticationMiddleware` | `middleware.py` | Bearer token validation, usage tracking |
| 3 | `RateLimitingMiddleware` | `middleware.py` | Per-endpoint request/hour + token/day limits |
| 4 | `CORSMiddleware` | FastAPI/Starlette | Origin allowlisting, preflight handling |

### Routers

| Router | Prefix | Tags | Source |
|--------|--------|------|--------|
| `ask_router` | `/ask` | Q&A | `router_ask.py` |
| `scrape_router` | `/scrape` | Scraping | `router_scrape.py` (optional, fails gracefully) |
| `embed_router` | `/embed` | Embeddings | `router_embed.py` |
| `modal_jobs_router` | `/modal-jobs` | Modal jobs | `router_modal_jobs.py` |
| `scraper_pipeline_ingest_router` | `/internal/scraper-pipeline` | Internal | `router_scraper_pipeline_ingest.py` |
| `documents_router` | `/documents` | Documents (Public) | `router_documents.py` |

All routers mounted under `v1_router` with prefix `/api/v1`.

### Service Layer

| Module | Path | Purpose |
|--------|------|---------|
| `modal/invoker.py` | `src/services/modal/invoker.py` | Modal function lookup, invocation, policy enforcement |
| `modal/job_registry.py` | `src/services/modal/job_registry.py` | Track spawned Modal `FunctionCall` handles (Modal Dict or in-memory) |
| `ingestion/modal_scraper_persist.py` | `src/services/ingestion/` | Gateway-owned scrape job CRUD in Postgres |
| `ingestion/modal_scraper_pipeline_persist.py` | `src/services/ingestion/` | Pipeline stage persistence (crawled URLs, chunks, embeddings) |
| `corpus/corpus_projection_service.py` | `src/services/corpus/` | Fail-closed corpus projection logic |
| `llm/client_manager.py` | `src/services/llm/` | LLM client management |
| `embedding/client.py` | `src/embedding_service/client.py` | Embedding HTTP client |

### Configuration

| Module | Path | Purpose |
|--------|------|---------|
| `config.py` | `src/config.py` | Central config: model names, URLs, feature flags, guardrails |
| `service_endpoints.py` | `src/service_endpoints.py` | Normalized service URLs (Render vs local) |
| `utils/database_url.py` | `src/utils/database_url.py` | DATABASE_URL resolution |

## Concurrency Model

| Concern | Pattern |
|---------|---------|
| Request handling | Async (`async def` handlers on uvicorn event loop) |
| Agent HTTP proxy | `httpx.AsyncClient` with shared connection pool |
| Modal SDK calls | `asyncio.to_thread()` (Modal SDK is synchronous) |
| Database queries | `psycopg2.connect()` (synchronous, blocks event loop briefly) |
| SSE streaming | `StreamingResponse` with async generator forwarding bytes |
| Background scraping | `BackgroundTasks` for local scraper (non-Modal path) |
| Rate limiting | In-memory `dict` (single-process, not shared across instances) |

## Static File Serving

The gateway optionally mounts the chat frontend's `dist/` directory at `/` via `StaticFiles`. When a browser requests `/` with `Accept: text/html`, the gateway serves `index.html`; API clients get JSON.

Source: `apis/gateway/src/api/main.py` lines 633–643

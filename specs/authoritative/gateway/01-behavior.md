# Behavior: Gateway
> Auto-generated: 2026-05-12

## Purpose

The gateway is the **unified HTTP entry point** for the Vecinita civic/community information RAG system. It consolidates Q&A, scraping, embedding, document browsing, and Modal job orchestration endpoints into a single FastAPI application deployed on Render.

Source: `apis/gateway/src/api/main.py`

## Core Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| 1 | Request routing | Proxy chat/Q&A requests to the agent service, document requests to data-management-api |
| 2 | Authentication | Bearer token validation via `AuthenticationMiddleware` (toggled by `ENABLE_AUTH`) |
| 3 | Rate limiting | Per-endpoint request/hour and token/day limits via `RateLimitingMiddleware` |
| 4 | CORS | Origin allowlisting with regex support for frontend origins |
| 5 | Correlation tracking | `X-Correlation-ID` propagation across gateway → Modal → agent for distributed tracing |
| 6 | Modal job orchestration | Submit, track, cancel scrape/embed/reindex jobs via Modal SDK `Function.from_name().remote()` |
| 7 | Scraper pipeline persistence | Gateway-owned Postgres persistence for Modal scraper job state when `MODAL_SCRAPER_PERSIST_VIA_GATEWAY=true` |
| 8 | SSE streaming passthrough | Forward Server-Sent Events from agent `/ask-stream` to chat frontend |
| 9 | Embedding proxy | Forward embedding requests to Modal functions or HTTP embedding service |
| 10 | Public documents API | Read-only corpus metadata endpoints (overview, preview, tags, chunk statistics) |
| 11 | Health/integrations | Structured health probes for agent, database, and Modal-backed services |
| 12 | OpenAPI aggregation | Bearer security scheme injection and schema generation at `/api/v1/docs/openapi.json` |

## Key Behaviors

### Q&A Proxy (router_ask.py)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| `GET /api/v1/ask?question=...` | Forward to agent `/ask` with all query params | `AskResponse` with answer, sources, latency |
| `GET /api/v1/ask/stream?question=...` | Open SSE stream to agent `/ask-stream`, forward raw bytes | `text/event-stream` with thinking/complete/error events |
| `GET /api/v1/ask/config` | Forward to agent `/config`, normalize provider shape | `GatewayAskConfigPayload` |
| Agent unavailable | Return demo response (`DEMO_MODE=true`) or fallback config | Graceful degradation |

### Modal Job Orchestration (router_modal_jobs.py)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| `POST /api/v1/modal-jobs/scraper` | Invoke `modal_scrape_job_submit` via Modal SDK; optionally persist to gateway Postgres | `GatewayModalScrapeJobBody` with job_id |
| `GET /api/v1/modal-jobs/scraper/{job_id}` | Read from gateway Postgres or invoke `modal_scrape_job_get` | Job status with pipeline_stage |
| `POST /api/v1/modal-jobs/scraper/{job_id}/cancel` | Cancel via Postgres or Modal RPC | Updated job status |
| `POST /api/v1/modal-jobs/reindex/spawn` | `spawn_modal_scraper_reindex` (non-blocking) | `gateway_job_id` + `modal_function_call_id` |

### Embedding Proxy (router_embed.py)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| `POST /api/v1/embed` | Modal function invocation (`embed_query`) or HTTP proxy | `EmbedResponse` with vector |
| `POST /api/v1/embed/batch` | Modal `embed_batch` or HTTP proxy | `EmbedBatchResponse` |
| `POST /api/v1/embed/similarity` | Batch-embed two texts, compute cosine similarity | `SimilarityResponse` |

### Scraper Pipeline Ingest (router_scraper_pipeline_ingest.py)

| Trigger | Behavior | Outcome |
|---------|----------|---------|
| `POST /api/v1/internal/scraper-pipeline/jobs/{job_id}/status` | Modal workers persist pipeline stage transitions | 204 No Content |
| `POST /api/v1/internal/scraper-pipeline/crawled-urls` | Store crawled URL artifacts | `crawled_url_id` |
| `POST /api/v1/internal/scraper-pipeline/chunks` | Store document chunks | `chunk_ids` |
| `POST /api/v1/internal/scraper-pipeline/embeddings` | Store chunk embeddings | 204 No Content |

## Service Boundaries (Does NOT Own)

| Concern | Owned By |
|---------|----------|
| RAG retrieval logic, LLM inference, graph orchestration | agent service |
| Embedding model execution | Modal `vecinita-embedding` app |
| Web scraping execution | Modal `vecinita-scraper` app |
| Document content storage (chunks, sources) | `public` schema, managed by scraper/agent |
| Frontend rendering | chat-frontend, data-management-frontend |

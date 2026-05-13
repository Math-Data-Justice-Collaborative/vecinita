# Data Management API — High-Level Behavior

> Auto-generated: 2026-05-12

## Purpose

The **data-management API** is an operator-facing FastAPI service that brokers
communication between the **data-management SPA** (React/Vite dashboard) and the
backend scraper, embedding, and model workloads. It provides a single HTTP
origin for browser clients — proxying scrape-job CRUD to the scraper service
and delegating embedding/prediction requests through typed service-clients that
can route via HTTP or Modal SDK depending on configuration. The service exists
so browsers never need direct access to Modal endpoints or multiple backend
hostnames.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Scrape-job proxy | Forward `/jobs` CRUD from the SPA to the scraper service, preserving auth headers and upstream status codes |
| Embedding delegation | Accept `/embed` requests and delegate to the embedding service via `EmbeddingClient` (HTTP or Modal) |
| Model prediction delegation | Accept `/predict` requests and delegate to the model service via `ModelClient` (HTTP or Modal) |
| Aggregate health | Expose `/health` that checks its own DB guard and the upstream scraper health |
| CORS management | Maintain an allowed-origin list so the SPA can make browser requests safely |
| Canonical DB URL guard | Validate that `DATABASE_URL` is a real Postgres connection (not a placeholder) at startup and on health checks |
| Corpus conflict resolution | Provide deterministic last-writer-wins conflict resolution for corpus writes (`corpus_conflict.py`) |
| Metadata enrichment | Inject `source_of_truth` and `canonical_visibility_updated_at` on outbound POST responses and embed results |

## Key Behaviors

### Scrape Job Proxy (`/jobs/*`)
- **Trigger:** SPA sends any HTTP method to `/jobs` or `/jobs/{rest}`
- **Process:** `ScraperClient.forward_jobs()` relays the method, path, query, body, and auth header to the scraper service at `SCRAPER_SERVICE_BASE_URL`; POST responses are enriched with `source_of_truth` metadata
- **Outcome:** Upstream response (status + body) is mirrored to the browser

### Embed Request (`/embed`)
- **Trigger:** SPA or internal caller posts `{ text, model_version }` to `/embed`
- **Process:** `EmbeddingClient.embed()` routes to Modal SDK or HTTP based on `MODAL_FUNCTION_INVOCATION`; result metadata is enriched with canonical visibility fields
- **Outcome:** `EmbedResponse` with embedding vector returned

### Predict Request (`/predict`)
- **Trigger:** SPA or internal caller posts `{ text, model_version }` to `/predict`
- **Process:** `ModelClient.predict()` routes to Modal SDK or HTTP
- **Outcome:** `PredictResponse` with label, score, and model version returned

### Health Aggregation (`/health`)
- **Trigger:** Render health-check probe or manual GET
- **Process:** Validates `DATABASE_URL` via `corpus_db_guard`, then delegates to `ScraperClient.health()` (Modal or HTTP)
- **Outcome:** JSON health payload; 503 if scraper unreachable or DB URL invalid

## Boundaries

| Not responsible for | Handled by |
|---------------------|------------|
| Actual web scraping, crawling, chunking | `modal-apps/scraper` (vecinita-scraper) |
| Embedding vector computation | `modal-apps/embedding-modal` |
| Model inference / prediction | `modal-apps/model-modal` |
| Chat conversations and RAG retrieval | `apis/gateway` + `apis/agent` |
| Frontend UI rendering | `frontends/data-management` |
| Database schema migrations | Managed externally (Render Postgres) |
| User authentication (end-user login) | Scraper API key auth (bearer token) — no user sessions |

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)

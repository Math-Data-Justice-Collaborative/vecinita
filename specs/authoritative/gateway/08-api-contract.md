# API Contract: Gateway
> Auto-generated: 2026-05-12

Base path: `/api/v1`
OpenAPI docs: `GET /api/v1/docs` (Swagger UI), `GET /api/v1/docs/openapi.json`

## Authentication

| Property | Value |
|----------|-------|
| Scheme | Bearer token (`Authorization: Bearer <key>`) |
| Toggle | `ENABLE_AUTH` env var (default `false`) |
| Public endpoints | `/`, `/health`, `/integrations/status`, `/api/v1/ask/config`, `/api/v1/documents/*`, `/api/v1/docs*` |
| Source | `apis/gateway/src/api/middleware.py` |

## Versioning

No URL versioning beyond `/api/v1`. No breaking change policy documented yet.

## Endpoints

### Q&A (`/api/v1/ask`)

| Method | Path | Auth | Request | Response | Status Codes |
|--------|------|------|---------|----------|-------------|
| GET | `/ask` | Yes | Query: question (required), thread_id, lang, provider, model, tags, tag_match_mode, include_untagged_fallback, rerank, rerank_top_k | `AskResponse` | 200, 401, 422, 503, 504, 500 |
| GET | `/ask/stream` | Yes | Same query params | `text/event-stream` (SSE) | 200 (stream), 401, 422, 503, 504, 500 |
| GET | `/ask/config` | No | — | `GatewayAskConfigPayload` | 200 |

**SSE event types:** `thinking`, `tool_event`, `complete`, `clarification`, `error`

### Scraping (`/api/v1/scrape`)

| Method | Path | Auth | Request | Response | Status Codes |
|--------|------|------|---------|----------|-------------|
| POST | `/scrape` | Yes | Body: `{ urls, force_loader, stream }` | `ScrapeResponse` | 200, 400, 422, 500 |
| GET | `/scrape/{job_id}` | Yes | Path: job_id (UUID) | `ScrapeStatusResponse` | 200, 404, 422, 500 |
| GET | `/scrape/history` | Yes | Query: limit, offset | `ScrapeHistoryResponse` | 200, 422, 500 |
| GET | `/scrape/stats` | Yes | — | `ScrapeGatewayStatsResponse` | 200, 500 |
| POST | `/scrape/{job_id}/cancel` | Yes | Path: job_id (UUID) | `ScrapeStatusResponse` | 200, 404, 409, 422, 500 |
| POST | `/scrape/cleanup` | Yes | — | `ScrapeGatewayCleanupResponse` | 200, 500 |
| POST | `/scrape/reindex` | Yes | Query: clean, verbose | `GatewayReindexTriggerResponse` | 200, 422, 502, 503, 500 |

### Embeddings (`/api/v1/embed`)

| Method | Path | Auth | Request | Response | Status Codes |
|--------|------|------|---------|----------|-------------|
| POST | `/embed` | Yes | Body: `{ text, model? }` | `EmbedResponse` | 200, 422, 503, 500 |
| POST | `/embed/batch` | Yes | Body: `{ texts, model? }` | `EmbedBatchResponse` | 200, 422, 503, 500 |
| POST | `/embed/similarity` | Yes | Body: `{ text1, text2, model? }` | `SimilarityResponse` | 200, 422, 503, 500 |
| GET | `/embed/config` | Yes | — | `EmbeddingConfigResponse` | 200 |
| POST | `/embed/config` | Yes | Query: provider, model, lock? | `EmbeddingConfigResponse` | 200, 403, 503, 500 |

### Modal Jobs (`/api/v1/modal-jobs`)

| Method | Path | Auth | Request | Response | Status Codes |
|--------|------|------|---------|----------|-------------|
| POST | `/modal-jobs/scraper` | Yes | Body: `{ url, user_id, crawl_config?, chunking_config?, metadata? }` | `GatewayModalScrapeJobBody` | 200, 400, 422, 503, 500 |
| GET | `/modal-jobs/scraper/{job_id}` | Yes | Path: job_id (UUID) | `GatewayModalScrapeJobBody` | 200, 404, 422, 503, 500 |
| GET | `/modal-jobs/scraper` | Yes | Query: user_id?, limit | `GatewayModalScraperListResponse` | 200, 422, 503, 500 |
| POST | `/modal-jobs/scraper/{job_id}/cancel` | Yes | Path: job_id (UUID) | `GatewayModalScrapeJobBody` | 200, 404, 409, 422, 503, 500 |
| POST | `/modal-jobs/reindex/spawn` | Yes | Query: clean, stream, verbose | `GatewayModalReindexSpawnResponse` | 200, 422, 503, 500 |
| GET | `/modal-jobs/registry` | Yes | Query: limit | `GatewayModalRegistryListResponse` | 200, 503, 500 |
| GET | `/modal-jobs/registry/{gateway_job_id}` | Yes | Query: refresh? | `GatewayModalRegistryRecord` | 200, 404, 503, 500 |
| DELETE | `/modal-jobs/registry/{gateway_job_id}` | Yes | — | `{ gateway_job_id, deleted }` | 200, 404, 503 |

### Documents (`/api/v1/documents`) — Public, no auth

| Method | Path | Auth | Request | Response | Status Codes |
|--------|------|------|---------|----------|-------------|
| GET | `/documents/overview` | No | Query: tags?, tag_match_mode, include_test_data | `DocumentsOverviewResponse` | 200, 503, 500 |
| GET | `/documents/preview` | No | Query: source_url, limit | `DocumentsPreviewResponse` | 200, 404, 503, 500 |
| GET | `/documents/download-url` | No | Query: source_url | `DocumentsDownloadUrlResponse` | 200, 404, 503, 500 |
| GET | `/documents/chunk-statistics` | No | Query: limit | `DocumentsChunkStatisticsResponse` | 200, 503, 500 |
| GET | `/documents/tags` | No | Query: query?, locale, limit, include_test_data | `DocumentsTagsResponse` | 200, 503, 500 |

### Health & Operations (root-level)

| Method | Path | Auth | Response | Status Codes |
|--------|------|------|----------|-------------|
| GET | `/` | No | `GatewayPublicRootResponse` or `index.html` | 200 |
| GET | `/health` | No | `HealthCheck` | 200 |
| GET | `/api/v1/health` | No | `HealthCheck` (alias) | 200 |
| GET | `/integrations/status` | No | `IntegrationsStatus` | 200 |
| GET | `/config` | No | `GatewayConfig` | 200 |

### Internal Pipeline (`/api/v1/internal/scraper-pipeline`) — Not in OpenAPI schema

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/jobs/{job_id}/status` | `X-Scraper-Pipeline-Ingest-Token` | Update job pipeline stage |
| POST | `/crawled-urls` | Token | Store crawled URL |
| POST | `/extracted-content` | Token | Store extracted content |
| POST | `/processed-documents` | Token | Store processed document |
| POST | `/chunks` | Token | Store document chunks |
| POST | `/embeddings` | Token | Store chunk embeddings |

## Rate Limits

| Endpoint Prefix | Requests/Hour | Tokens/Day |
|----------------|---------------|------------|
| `/api/v1/ask` | 600 | 10,000 |
| `/api/v1/scrape` | 100 | 50,000 |
| `/api/v1/admin` | 50 | 1,000 |
| `/api/v1/embed` | 1,000 | 100,000 |
| Other | 100 (global default) | 1,000 (global default) |

All limits configurable via `RATE_LIMIT_*` env vars. Source: `apis/gateway/src/api/middleware.py`

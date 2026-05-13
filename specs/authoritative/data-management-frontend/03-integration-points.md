# data-management-frontend — Integration Points

> Auto-generated: 2026-05-12

## Overview

The data-management frontend integrates with the data-management API for document/corpus CRUD and the gateway for job triggering. All communication is HTTP REST.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| DM API (`/documents/*`) | HTTP REST | Outbound | Document CRUD, tag management, embedding operations | `VITE_DM_API_BASE_URL` |
| DM API (`/jobs/*`) | HTTP REST | Outbound | Scrape job submission, status, cancellation | `VITE_DM_API_BASE_URL` |
| DM API (`/tags/*`) | HTTP REST | Outbound | Tag inventory, auto-generation, application | `VITE_DM_API_BASE_URL` |
| DM API (`/upload`) | HTTP POST (multipart) | Outbound | Document file upload | `VITE_DM_API_BASE_URL` |
| DM API (`/embeddings/*`) | HTTP REST | Outbound | Embedding generation and semantic search | `VITE_DM_API_BASE_URL` |
| DM API (`/stats`) | HTTP GET | Outbound | Dashboard statistics | `VITE_DM_API_BASE_URL` |

## External Integrations

None. The DM frontend communicates exclusively with internal Vecinita services.

## Integration Details

### DM API — RAG API Client

- **Endpoint/Function:** All endpoints via `RAGApiClient` class in `rag-api.ts`
- **Request format:** JSON body (POST/PUT), query params (GET), multipart/form-data (upload)
- **Response format:** JSON
- **Error handling:** 3 retries with exponential backoff (500ms base, 4s max). Retries on 408, 429, and 5xx. AbortError (timeout) and TypeError (network) are retryable. Non-retryable errors surface to UI via toast.
- **Retry/timeout policy:** 15s per-request timeout via `AbortController`. Max 3 retries.
- **Authentication:** Bearer token via `getCurrentAuthToken()` from `apiKeyAuth.ts`
- **Mock mode:** When `VITE_DM_API_BASE_URL` is not configured, the client falls back to in-memory mock data

### Scraper Config Resolution

The frontend resolves API base URLs through `scraper-config.ts`:
- `browserDmHttpApiBase()` — resolves the DM API base URL for HTTP calls
- `scraperJobsApiRoot()` — resolves the jobs API root (may differ from document API base)
- `scraperRuntimeConfig.defaultUserId` — default user ID from `VITE_DEFAULT_SCRAPER_USER_ID`

**Source:** `frontends/data-management/src/app/api/scraper-config.ts`

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)

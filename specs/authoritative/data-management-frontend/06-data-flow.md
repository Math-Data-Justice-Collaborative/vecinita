# data-management-frontend — Data Flow

> Auto-generated: 2026-05-12

## Overview

Data flows from admin interactions through the DM API for corpus management. The frontend acts as a CRUD interface with intelligent fallback and mock modes.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| Admin input | Form data | UI interaction | `RAGApiClient` methods |
| DM API responses | JSON | HTTP response | React component state |
| localStorage | JSON | Page load | Known scrape jobs cache |
| OpenAPI spec | TypeScript types | Build time | `dm-openapi.generated.ts` |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| Scrape request building | `ScrapeRequest` | `buildModalScrapeJobRequest()` — maps frontend options to Modal job format | `ModalScrapeJobRequest` |
| Status mapping | `ModalJobStatus` | `mapModalStatusToFrontendStatus()` — maps backend statuses to frontend statuses | Frontend status string |
| Progress inference | Status + progress_pct | `inferProgress()` — maps status to percentage when explicit progress unavailable | 0-100 number |
| Stats aggregation | Documents + Jobs | `buildStatsFromDocuments()` / `buildStatsFromJobs()` — derive dashboard stats | `DashboardStats` |
| Tag normalization | Raw API response | `normalizeTagInventory()` — handles multiple response shapes | `TagInventoryResponse` |
| Error normalization | HTTP error body | `normalizeUpstreamErrorMessage()` — extract user-facing error message | Error string |
| Mock mode fallback | Missing `VITE_DM_API_BASE_URL` | In-memory mock data returned | Mock Document/Job arrays |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| DM API (`/documents`) | JSON | Document CRUD operations | Document create/update/delete payloads |
| DM API (`/jobs`) | JSON | Scrape job submission | `ModalScrapeJobRequest` |
| DM API (`/upload`) | multipart/form-data | File upload | Document file + metadata |
| DM API (`/tags`) | JSON | Tag operations | Tag generation/application payloads |
| localStorage | JSON | After job submission | Known scrape job cache (last 50 jobs) |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| Known scrape jobs | localStorage (`vecinita.scrape-jobs`) | Job IDs, URLs, depths, timestamps (max 50) | Until browser clear |
| Auth token | localStorage/memory | API key for authenticated requests | Until logout |
| Mock documents | In-memory | Fallback documents when API unconfigured | Session lifetime |

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)

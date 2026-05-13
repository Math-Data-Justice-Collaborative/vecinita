# data-management-frontend — API Contract

> Auto-generated: 2026-05-12

## Overview

The DM frontend does not expose an API — it consumes the data-management API. This document describes the DM API endpoints the frontend depends on.

## Base URL

| Environment | URL |
|-------------|-----|
| Local | `http://localhost:5174` (app) → `VITE_DM_API_BASE_URL` (default: `http://localhost:8005`) |
| Render | `https://vecinita-data-management-frontend-v1.onrender.com` → `VITE_DM_API_BASE_URL` |

## Consumed Endpoints

### Document CRUD

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/documents` | List documents (paginated, filterable) | Bearer token |
| GET | `/documents/:id` | Get single document | Bearer token |
| POST | `/documents` | Create document | Bearer token |
| PUT | `/documents/:id` | Update document | Bearer token |
| DELETE | `/documents/:id` | Delete document | Bearer token |
| DELETE | `/documents/bulk-delete` | Bulk delete documents | Bearer token |

### Scrape Jobs

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/jobs` (via `scraperJobsApiRoot()`) | Submit scrape job | Bearer token |
| GET | `/jobs` | List all jobs | Bearer token |
| GET | `/jobs/:job_id` | Get job status | Bearer token |
| POST | `/jobs/:job_id/cancel` | Cancel running job | Bearer token |

### Tags

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/tags` | Get tag inventory | Bearer token |
| POST | `/tags/auto-generate` | AI-generate tags for document | Bearer token |
| POST | `/tags/apply` | Apply tags to document | Bearer token |

### File Upload

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/upload` | Upload document file (multipart) | None (direct fetch) |

### Embeddings

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/embeddings/generate` | Generate embeddings for document | Bearer token |
| POST | `/embeddings/search` | Semantic search | Bearer token |

### Statistics

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/stats` | Dashboard statistics | Bearer token |

## Schemas

- Runtime types: `frontends/data-management/src/app/api/types/index.ts`
- OpenAPI generated: `frontends/data-management/src/app/api/types/dm-openapi.generated.ts`
- Codegen: `npm run codegen:api` from `specs/005-wire-services-dm-front/artifacts/dm-openapi.snapshot.json`

## Versioning

No formal API versioning. The frontend uses response normalization (e.g., `normalizeTagInventory()`) to handle response shape variations.

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)

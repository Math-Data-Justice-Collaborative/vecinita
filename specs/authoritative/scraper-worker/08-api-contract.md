# API Contract: Scraper Worker
> Auto-generated: 2026-05-12

## Overview

The scraper worker exposes two API surfaces:
1. **Modal functions** — invoked via Modal SDK by the gateway service
2. **FastAPI REST endpoints** — served on Render (DM API facade) and Modal ASGI

## Modal Function API

All functions belong to Modal app `vecinita-scraper`.

Source: `modal-apps/scraper/src/vecinita_scraper/app.py`

### modal_scrape_job_submit

| Property | Value |
|----------|-------|
| Invocation | `Function.from_name("vecinita-scraper", "modal_scrape_job_submit").remote(payload)` |
| Timeout | 300s |
| Auth | Modal SDK credentials (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`) |

**Request:**

```python
{
    "url": str,          # Target URL to scrape
    "user_id": str,      # Requesting user ID
    "max_depth": int,    # Crawl depth (default: 3)
    "timeout_seconds": int,  # Per-URL timeout (default: 60)
    "metadata": dict     # Optional metadata
}
```

**Response:**

```python
{
    "id": str,           # UUID job ID
    "user_id": str,
    "url": str,
    "status": "queued",
    "pipeline_stage": None,
    "created_at": str    # ISO 8601
}
```

**Errors:**

| Error | Cause |
|-------|-------|
| `ValueError` | Invalid URL format |
| `TimeoutError` | Function exceeded 300s |
| `RemoteError` | Unhandled exception in function |

### modal_scrape_job_get

| Property | Value |
|----------|-------|
| Invocation | `Function.from_name("vecinita-scraper", "modal_scrape_job_get").remote(job_id)` |
| Timeout | 120s |

**Request:**

```python
{
    "job_id": str   # UUID
}
```

**Response:**

```python
{
    "id": str,
    "user_id": str,
    "url": str,
    "status": str,           # queued|scraping|processing|chunking|embedding|storing|completed|failed|cancelled
    "pipeline_stage": str,
    "pages_scraped": int,
    "pages_failed": int,
    "error_message": str | None,
    "created_at": str,
    "updated_at": str,
    "completed_at": str | None
}
```

### modal_scrape_job_list

| Property | Value |
|----------|-------|
| Invocation | `Function.from_name("vecinita-scraper", "modal_scrape_job_list").remote(user_id, limit)` |
| Timeout | 120s |

**Request:**

```python
{
    "user_id": str,
    "limit": int    # Default: 50
}
```

**Response:**

```python
{
    "jobs": [ScrapeJobResponse, ...],
    "total": int
}
```

### modal_scrape_job_cancel

| Property | Value |
|----------|-------|
| Invocation | `Function.from_name("vecinita-scraper", "modal_scrape_job_cancel").remote(job_id)` |
| Timeout | 120s |

**Request:**

```python
{
    "job_id": str   # UUID
}
```

**Response:**

```python
{
    "id": str,
    "status": "cancelled",
    "updated_at": str
}
```

### trigger_reindex

| Property | Value |
|----------|-------|
| Invocation (blocking) | `.spawn(...)` then `.get(timeout=60)` |
| Invocation (fire-and-forget) | `.spawn(...)` |
| Timeout | 60s |

**Request:** No arguments required.

**Response (blocking):**

```python
{
    "status": "completed",
    "queues_drained": ["scrape-jobs", "process-jobs", "chunk-jobs", "embed-jobs", "store-jobs"]
}
```

### health_check

| Property | Value |
|----------|-------|
| Invocation | `Function.from_name("vecinita-scraper", "health_check").remote()` |
| Timeout | Default |

**Response:**

```python
{
    "status": "healthy",
    "service": "vecinita-scraper",
    "timestamp": str
}
```

## FastAPI REST Endpoints

Deployed on Render as `vecinita-data-management-api-v1` and on Modal ASGI.

Source: `modal-apps/scraper/src/vecinita_scraper/api/`

### Authentication

All endpoints except `/health` require an API key in the `Authorization` header or `X-API-Key` header. Keys are validated against `SCRAPER_API_KEYS`.

### Job Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/jobs` | API key | Submit scrape job |
| GET | `/api/v1/jobs` | API key | List jobs (with pagination) |
| GET | `/api/v1/jobs/{job_id}` | API key | Get job status |
| POST | `/api/v1/jobs/{job_id}/cancel` | API key | Cancel job |

#### POST /api/v1/jobs

**Request Body:**

```json
{
    "url": "https://example.com",
    "user_id": "user-123",
    "max_depth": 3,
    "timeout_seconds": 60,
    "metadata": {}
}
```

**Response (201):**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "url": "https://example.com",
    "status": "queued",
    "pipeline_stage": null,
    "pages_scraped": 0,
    "pages_failed": 0,
    "created_at": "2026-05-12T12:00:00Z"
}
```

#### GET /api/v1/jobs

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | string | — | Filter by user |
| `status` | string | — | Filter by status |
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response (200):**

```json
{
    "jobs": [...],
    "total": 42,
    "limit": 50,
    "offset": 0
}
```

#### GET /api/v1/jobs/{job_id}

**Response (200):** Full `ScrapeJobResponse` object.

**Response (404):**

```json
{
    "detail": "Job not found"
}
```

#### POST /api/v1/jobs/{job_id}/cancel

**Response (200):** Updated `ScrapeJobResponse` with `status: "cancelled"`.

### Document Browsing

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/documents` | API key | List documents |
| GET | `/api/v1/documents/{doc_id}` | API key | Get document detail |
| GET | `/api/v1/documents/{doc_id}/chunks` | API key | Get document chunks |

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | None | Health check |
| GET | `/health` | None | Health check (alias) |

**Response (200):**

```json
{
    "status": "healthy",
    "service": "vecinita-data-management-api",
    "version": "1.0.0"
}
```

## Error Response Format

All error responses follow a consistent shape:

```json
{
    "detail": "Human-readable error message",
    "error_code": "SCRAPER_ERROR_CODE",
    "status_code": 400
}
```

| Status | Meaning |
|--------|---------|
| 400 | Invalid request (bad URL, missing fields) |
| 401 | Missing or invalid API key |
| 404 | Job or document not found |
| 409 | Job already in terminal state |
| 500 | Internal server error |
| 503 | Service unavailable (DB connection failure) |

## Versioning

| Property | Value |
|----------|-------|
| Strategy | URL prefix (`/api/v1/`) |
| Breaking changes | New major version prefix |
| Current version | v1 |

## Rate Limits

| Property | Value |
|----------|-------|
| REST API | No explicit rate limiting (protected by API key access) |
| Modal functions | Modal platform concurrency limits apply |
| Crawl throttling | Built-in Crawl4AI rate limiting per domain |

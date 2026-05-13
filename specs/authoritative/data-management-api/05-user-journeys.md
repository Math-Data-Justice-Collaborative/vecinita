# Data Management API — User Journeys

> Auto-generated: 2026-05-12

## Overview

End-to-end journeys that pass through the data-management API, from the
operator's perspective using the SPA and from system-level interactions.

## Journeys

### Submit a Scrape Job

**Persona:** Data Operator
**Goal:** Scrape a civic information URL and ingest its content into the corpus

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Operator opens data-management SPA | SPA loads, connects to `VITE_DM_API_BASE_URL` | |
| 2 | Operator enters URL and configures crawl params | SPA builds `ScrapeJobRequest` payload | Optional: `crawl_config`, `chunking_config` |
| 3 | SPA sends `POST /jobs` with bearer token | DM API proxies to scraper via `ScraperClient.forward_jobs()` | Auth header forwarded |
| 4 | Scraper creates job in Postgres, returns `ScrapeJobCreatedResponse` | DM API enriches with `source_of_truth` metadata, returns to SPA | Status 201 |
| 5 | SPA displays job ID and pending status | | |

**Happy path outcome:** Job is queued with `pending` status; operator can poll for progress.
**Failure modes:** Scraper unreachable (503), invalid URL (422), auth failure (401/403)

### Monitor Job Progress

**Persona:** Data Operator
**Goal:** Track a running scrape job until completion

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Operator views job list in SPA | SPA sends `GET /jobs?user_id=...` | Filtered by operator ID |
| 2 | DM API proxies to scraper | Scraper queries `scraping_jobs` with aggregate counts | |
| 3 | SPA receives job list with status, progress, counts | DM API mirrors upstream response | |
| 4 | Operator clicks a specific job | SPA sends `GET /jobs/{job_id}` | |
| 5 | SPA shows detailed status with URL count, chunk count, embedding count | | |

**Happy path outcome:** Operator sees real-time progress (crawl_url_count, chunk_count, embedding_count).
**Failure modes:** Job failed with error_message, scraper unreachable

### Generate Embedding

**Persona:** Data Operator or System
**Goal:** Obtain an embedding vector for a text snippet

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Client sends `POST /embed` with `{ text, model_version }` | | |
| 2 | DM API checks `MODAL_FUNCTION_INVOCATION` | Routes to Modal SDK or HTTP | |
| 3 | Upstream embedding service computes vector | Returns `EmbedResponse` | |
| 4 | DM API enriches metadata with `source_of_truth` | Returns response to client | |

**Happy path outcome:** Client receives embedding vector with model version.
**Failure modes:** Embedding service down (502/503), Modal credentials invalid (503)

### Health Check Probe

**Persona:** Render platform / Platform Administrator
**Goal:** Verify the service and its upstream dependencies are healthy

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Render sends `GET /health` | | Every 30s per Dockerfile HEALTHCHECK |
| 2 | DM API validates `DATABASE_URL` | `corpus_db_guard` checks scheme and placeholder tokens | Strict mode on Render |
| 3 | DM API calls `ScraperClient.health()` | Modal SDK or HTTP based on config | |
| 4 | Returns aggregate health JSON | `{ "status": "ok", "service": "vecinita-scraper" }` | |

**Happy path outcome:** 200 OK with healthy status.
**Failure modes:** Invalid DATABASE_URL (RuntimeError at startup), scraper unreachable (503)

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)

# Infrastructure Plan: Scraper Worker
> Auto-generated: 2026-05-12

## Overview

The scraper worker runs on two platforms: **Modal** (serverless functions and pipeline) and **Render** (FastAPI DM API facade). This document covers build, deployment, scaling, and observability for both.

## Deployment Topology

| Component | Platform | Type | Purpose |
|-----------|----------|------|---------|
| `vecinita-scraper` Modal app | Modal | Serverless functions | Pipeline execution, job CRUD |
| `vecinita-data-management-api-v1` | Render | Web service | REST API facade for DM frontend |
| PostgreSQL | Render | Managed database | Shared data store |

## Modal Deployment

### Build

| Property | Value |
|----------|-------|
| Deploy command | `modal deploy src/vecinita_scraper/app.py` |
| Image base | `debian_slim` (Modal-managed) |
| Python version | ≥3.11 |
| Image layers | System deps → Python packages → Playwright Chromium |
| Secrets | `vecinita-scraper-env` (Modal secret group) |

### Image Configuration

```python
image = modal.Image.debian_slim()
    .pip_install("crawl4ai>=0.4.0", "docling>=0.4.0", "langchain>=0.1.0",
                 "playwright", "psycopg2-binary", "tiktoken", "structlog",
                 "pypdf", "fastembed", "pydantic>=2.0", "fastapi")
    .run_commands("playwright install chromium")
```

### Resources

| Function | CPU | Memory | GPU | Timeout |
|----------|-----|--------|-----|---------|
| `health_check` | Default | Default | None | Default |
| `modal_scrape_job_submit` | Default | Default | None | 300s |
| `modal_scrape_job_get` | Default | Default | None | 120s |
| `modal_scrape_job_list` | Default | Default | None | 120s |
| `modal_scrape_job_cancel` | Default | Default | None | 120s |
| `trigger_reindex` | Default | Default | None | 60s |
| `scraper_worker` | 1-2 CPU | 1-2 GB | None | Worker-defined |
| `drain_*_queue` | Default | Default | None | Worker-defined |

### Scaling

| Property | Value |
|----------|-------|
| Scale-to-zero | Yes (automatic) |
| Cold start | 10-20s (Playwright/Chromium initialization) |
| Max concurrency | Modal platform limits; bounded by `spawn_map.aio` |
| Container keep-alive | Modal-managed (typically 5-15 min) |
| Container reuse | Yes, within keep-alive window |

## Render Deployment

### Service Configuration

| Property | Value |
|----------|-------|
| Service name | `vecinita-data-management-api-v1` |
| Service type | Web Service |
| Plan | Starter |
| Region | Default (US) |
| Runtime | Docker |
| Dockerfile | `modal-apps/scraper/Dockerfile` |
| Port | 10000 (`PORT` env var) |
| Health check | `GET /health` or `GET /api/v1/health` |
| Auto-deploy | On push to submodule branch |

### Render Environment Variables

See [03-integration-points.md](03-integration-points.md) for the full variable reference.

Key variables for Render deployment:

| Variable | Required | Purpose |
|----------|----------|---------|
| `PORT` | Yes | HTTP listen port (10000) |
| `DATABASE_URL` | Yes | Render PostgreSQL connection |
| `SCRAPER_API_KEYS` | Yes (prod) | API authentication keys |
| `CORS_ORIGINS` | No | Allowed CORS origins |
| `ENVIRONMENT` | No | `production` / `development` |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## Database Infrastructure

| Property | Value |
|----------|-------|
| Provider | Render Managed PostgreSQL |
| Plan | Shared (starter) |
| Extensions required | `pgvector` (for `VECTOR` type in chunk_embeddings) |
| Connection limit | ~97 (starter plan) |
| SSL | Enforced in production |
| Backups | Render-managed daily |

### Schema Ownership

The scraper worker writes to these tables:

| Table | Schema | Create/Migrate |
|-------|--------|---------------|
| `scraping_jobs` | `public` | Application-managed |
| `crawled_urls` | `public` | Application-managed |
| `documents` | `data_mgmt` or `public` | Shared migration tooling |
| `document_chunks` | `public` | Application-managed |
| `chunk_embeddings` | `public` | Application-managed |

## Observability

### Logging

| Platform | Tool | Configuration |
|----------|------|--------------|
| Modal | Modal function logs | `structlog` with JSON output; visible in Modal dashboard |
| Render | Render log stream | stdout/stderr captured by Render |
| Both | `LOG_LEVEL` env var | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Structured Log Fields

| Field | Description |
|-------|-------------|
| `job_id` | Scraping job UUID |
| `url` | Target URL |
| `pipeline_stage` | Current processing stage |
| `duration_ms` | Operation duration |
| `error` | Error message if applicable |

### Metrics (Modal Dashboard)

| Metric | Source | Purpose |
|--------|--------|---------|
| Function invocations | Modal dashboard | Call volume per function |
| Function duration | Modal dashboard | Latency per function |
| Container count | Modal dashboard | Scaling behavior |
| Queue depth | Modal queue inspection | Pipeline backpressure |
| Error rate | Modal function logs | Failure tracking |

### Alerting (Future)

| Alert | Condition | Channel |
|-------|-----------|---------|
| High failure rate | >20% jobs failing in 1h window | Slack / PagerDuty |
| Queue backup | Any queue depth >100 for >30 min | Slack |
| Cold start spike | Average cold start >30s | Slack |
| DB connection exhaustion | Active connections >80 | Slack |

## Capacity Profile

| Metric | Value | Notes |
|--------|-------|-------|
| Typical jobs/day | 10-50 | Expected production load |
| Avg scrape duration | 30-120s | Depends on target site complexity |
| Avg pipeline duration | 2-5 min | Full URL-to-embeddings |
| Cold start | 10-20s | Playwright initialization |
| Memory per scraper | 500MB-1.5GB | Chromium + page content |
| Storage growth | ~1MB per scraped page | Chunks + embeddings |

## Disaster Recovery

| Scenario | Recovery |
|----------|----------|
| Modal outage | All scraping stops; pending queue items preserved; resume on recovery |
| Render outage | REST API unavailable; Modal functions continue (direct invocation) |
| Database outage | All writes fail; jobs stall; manual reindex after recovery |
| Corrupted embeddings | Re-scrape affected jobs or re-embed from stored chunks |
| Lost chunks | Re-scrape from `crawled_urls.raw_content` |

## Network Security

| Connection | Encryption | Authentication |
|-----------|------------|----------------|
| Gateway → Modal | Modal SDK (HTTPS/gRPC) | `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` |
| DM Frontend → Render | HTTPS | `SCRAPER_API_KEYS` |
| Scraper → PostgreSQL | SSL (required in prod) | `DATABASE_URL` credentials |
| Scraper → Web targets | HTTPS/HTTP | None (public web) |
| Scraper → Embedding | HTTPS or Modal SDK | Service-dependent |
| Pipeline callbacks → Gateway | HTTPS | `X-Scraper-Pipeline-Ingest-Token` |

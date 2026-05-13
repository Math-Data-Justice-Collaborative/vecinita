# Render Integration Plan: Scraper Worker
> Auto-generated: 2026-05-12

## Overview

The scraper worker has a Render deployment as `vecinita-data-management-api-v1`, serving the FastAPI REST interface for the DM frontend and external callers. This is a lightweight HTTP facade over the same codebase that runs on Modal.

Source: `modal-apps/scraper/Dockerfile`

## Service Configuration

| Property | Value |
|----------|-------|
| Service name | `vecinita-data-management-api-v1` |
| Service type | Web Service |
| Plan | Starter |
| Region | US (default) |
| Runtime | Docker |
| Dockerfile path | `modal-apps/scraper/Dockerfile` |
| Root directory | `modal-apps/scraper` |
| Port | `10000` (via `PORT` env var) |
| Branch | `main` (submodule) |

## Dockerfile

The Render deployment uses the Dockerfile from the scraper submodule:

| Stage | Contents |
|-------|----------|
| Base | Python 3.11 slim |
| System deps | Build essentials, libpq-dev |
| Python deps | FastAPI, psycopg2-binary, pydantic, structlog, uvicorn |
| App code | `src/vecinita_scraper/` |
| Entrypoint | `uvicorn vecinita_scraper.api.main:app --host 0.0.0.0 --port $PORT` |

The Render deployment does **not** include Playwright, Crawl4AI, or other scraping dependencies — it only serves the REST API and database queries. Scraping functions run exclusively on Modal.

## Environment Variables

### Required

| Variable | Value | Source |
|----------|-------|--------|
| `PORT` | `10000` | Render convention |
| `DATABASE_URL` | Render PostgreSQL internal URL | Render env group |
| `ENVIRONMENT` | `production` | Manual |

### Authentication

| Variable | Value | Source |
|----------|-------|--------|
| `SCRAPER_API_KEYS` | Comma-separated API keys | Render env group (sensitive) |
| `SCRAPER_DEBUG_BYPASS_AUTH` | `false` | Manual (never `true` in prod) |

### Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `CORS_ORIGINS` | (empty) | Allowed CORS origins for DM frontend |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `UPSTREAM_TIMEOUT_SECONDS` | `55` | Timeout for upstream calls |

### Modal Credentials (if calling Modal from Render)

| Variable | Purpose |
|----------|---------|
| `MODAL_TOKEN_ID` | Modal SDK auth (if REST API triggers Modal functions) |
| `MODAL_TOKEN_SECRET` | Modal SDK auth |
| `MODAL_WORKSPACE` | Modal workspace |

## Health Check

| Property | Value |
|----------|-------|
| Path | `/health` or `/api/v1/health` |
| Method | GET |
| Expected response | `200 OK` with `{ "status": "healthy" }` |
| Interval | Render default (30s) |

## Scaling

| Property | Value |
|----------|-------|
| Plan | Starter (single instance) |
| Min instances | 1 |
| Max instances | 1 (starter plan) |
| Auto-scale | Not available on starter |
| Upgrade path | Standard plan for auto-scaling |

## Database Connection

| Property | Value |
|----------|-------|
| Database | Shared Render PostgreSQL instance |
| Connection | `DATABASE_URL` (internal Render URL) |
| SSL | Enforced |
| Pool | No pooling (single instance, low concurrency) |

The Render DM API shares the same PostgreSQL database as the Modal scraper functions. Both read and write the same tables (`scraping_jobs`, `documents`, etc.).

## Auto-Deploy

| Property | Value |
|----------|-------|
| Trigger | Push to scraper submodule `main` branch |
| Build | Docker build from `modal-apps/scraper/Dockerfile` |
| Deploy | Automatic on successful build |
| Rollback | Render dashboard → manual deploy of previous commit |

## Relationship to Modal Deployment

```
┌──────────────────────────────────────────────────────────┐
│                   vecinita-scraper codebase               │
│                  (modal-apps/scraper/)                     │
├─────────────────────────┬────────────────────────────────┤
│   Modal Deployment      │   Render Deployment            │
│                         │                                │
│ • All serverless funcs  │ • FastAPI REST API only        │
│ • 5-stage pipeline      │ • No scraping/crawling         │
│ • Queue drainers        │ • DB read/write for jobs       │
│ • Browser + Playwright  │ • No Playwright/Crawl4AI       │
│ • Scrape execution      │ • Lightweight HTTP facade      │
│                         │                                │
│ Callers: Gateway (SDK)  │ Callers: DM Frontend (HTTP)    │
│ Scale: 0-N containers   │ Scale: 1 instance (starter)    │
└─────────────────────────┴────────────────────────────────┘
                     │
                     ▼
              Shared PostgreSQL
              (Render Managed)
```

## API Surface on Render

The Render deployment exposes only the FastAPI REST endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /api/v1/health` | Health check (prefixed) |
| `POST /api/v1/jobs` | Submit scrape job |
| `GET /api/v1/jobs` | List jobs |
| `GET /api/v1/jobs/{id}` | Get job status |
| `POST /api/v1/jobs/{id}/cancel` | Cancel job |
| `GET /api/v1/documents` | List documents |
| `GET /api/v1/documents/{id}` | Get document |
| `GET /api/v1/documents/{id}/chunks` | Get document chunks |

See [08-api-contract.md](08-api-contract.md) for full API documentation.

## CORS Configuration

| Property | Value |
|----------|-------|
| Variable | `CORS_ORIGINS` |
| Format | Comma-separated origins |
| Example | `https://dm.vecinita.app,https://dm-staging.vecinita.app` |
| Default | Empty (no CORS headers) |

## Monitoring on Render

| Metric | Source |
|--------|--------|
| HTTP request rate | Render dashboard → Metrics |
| Response latency | Render dashboard → Metrics |
| Memory usage | Render dashboard → Metrics |
| CPU usage | Render dashboard → Metrics |
| Deploy status | Render dashboard → Deploys |
| Log stream | Render dashboard → Logs |

## Cost

| Resource | Plan | Estimated Cost |
|----------|------|---------------|
| Web service | Starter | ~$7/month |
| PostgreSQL | Shared (starter) | Shared with other services |

## Future Considerations

| Consideration | Impact | Timeline |
|--------------|--------|----------|
| Upgrade to Standard plan | Auto-scaling, more resources | When traffic exceeds starter limits |
| Add PgBouncer | Connection pooling | When connection count approaches limits |
| CDN/caching | Reduce DB load for document reads | When read traffic is significant |
| Custom domain | `api.vecinita.app/dm/` | When public API is needed |

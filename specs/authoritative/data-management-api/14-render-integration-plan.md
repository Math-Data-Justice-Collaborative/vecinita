# Data Management API — Render Integration Plan

> Auto-generated: 2026-05-12

## Overview

The data-management API runs on Render as a Docker web service. The production
image is built from the scraper's Dockerfile (`modal-apps/scraper/Dockerfile`),
not the DM API's own, due to the 003-consolidate-scraper-dm decision.

## Service Definition

| Property | Value |
|----------|-------|
| Name | `vecinita-data-management-api-v1` |
| Type | web |
| Dockerfile | `./modal-apps/scraper/Dockerfile` |
| Docker context | `./modal-apps/scraper` |
| Start command | `uvicorn vecinita_scraper.api.server:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}` |
| Plan | starter |
| Health check | `/health` |
| Region | virginia |
| Auto-deploy trigger | checksPass |

## Environment Variables

| Variable | Source | Type |
|----------|--------|------|
| `PORT` | value: `"10000"` | static |
| `DATABASE_URL` | fromDatabase: `vecinita-postgres` (connectionString) | connection string |
| `MODAL_TOKEN_ID` | sync: false | secret |
| `MODAL_TOKEN_SECRET` | sync: false | secret |
| `MODAL_WORKSPACE` | sync: false | secret |
| `OLLAMA_BASE_URL` | sync: false | URL |
| `EMBEDDING_UPSTREAM_URL` | sync: false | URL |
| `CORS_ORIGINS` | sync: false | comma-separated origins |
| `SCRAPER_API_KEYS` | sync: false | comma-separated bearer tokens |
| `SCRAPER_DEBUG_BYPASS_AUTH` | value: `"false"` | static |
| `ENVIRONMENT` | value: `production` | static |
| `LOG_LEVEL` | value: `INFO` | static |
| `UPSTREAM_TIMEOUT_SECONDS` | value: `"55"` | static |

**Source:** `render.yaml` lines 353-390

## Database Binding

| Database | Variable | Access |
|----------|----------|--------|
| `vecinita-postgres` | `DATABASE_URL` | connectionString (internal URL) |

Database details:
- Region: virginia
- Plan: basic-256mb
- Database name: `vecinita`
- User: `vecinita`
- PostgreSQL version: 16

**Source:** `render.yaml` lines 392-398

## Service-to-Service Bindings

No explicit `fromService` bindings in `render.yaml`. Inter-service communication
is configured via env vars:

| Target Service | Variable | Mechanism |
|----------------|----------|-----------|
| Scraper (self — same image) | implicit (same process) | Direct function calls |
| Embedding service | `EMBEDDING_UPSTREAM_URL` | Manual env var |
| Gateway | n/a | Gateway proxies to this service via its own config |

## Standalone Render Deploy

The `apis/data-management-api/` submodule also has its own `render.yaml`
(`modal-apps/scraper/render.yaml`) for standalone deployments from the scraper
repo:

| Property | Value |
|----------|-------|
| Dockerfile | `./Dockerfile` |
| Docker context | `.` |
| Same service name | `vecinita-data-management-api-v1` |

## CI/CD Integration

| Mechanism | Config |
|-----------|--------|
| GitHub Actions deploy hook | `apis/data-management-api/.github/workflows/deploy.yml` |
| Render auto-deploy | `autoDeployTrigger: checksPass` in `render.yaml` |

## Docker HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1
```

## Preview Environments

Not explicitly configured in `render.yaml`. Preview environments would require
adding `previews` section to the service definition.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)

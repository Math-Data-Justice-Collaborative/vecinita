# Data Management API — Infrastructure Plan

> Auto-generated: 2026-05-12

## Overview

The data-management API is deployed as a Docker web service on Render. The
production image is built from the scraper codebase, not the DM API's own
Dockerfile, due to the consolidation decision (003-consolidate-scraper-dm).

## Build

| Property | Value |
|----------|-------|
| Dockerfile (monorepo) | `modal-apps/scraper/Dockerfile` |
| Dockerfile (standalone) | `apis/data-management-api/Dockerfile` |
| Build context (monorepo) | `./modal-apps/scraper` |
| Base image | `python:3.11-slim` |
| Build args | `VECINITA_SCRAPER_REPO`, `VECINITA_SCRAPER_REF` (standalone only) |

### Standalone Dockerfile

The `apis/data-management-api/Dockerfile` clones the scraper repo at build
time (`git clone --depth 1`), copies `pyproject.toml`, `README.md`, and `src/`
into `/app`, then runs `pip install .` to install the `vecinita-scraper`
package.

### Monorepo Build

The monorepo `render.yaml` builds from `modal-apps/scraper/Dockerfile`
directly, avoiding the git clone step.

## Deployment

| Property | Value |
|----------|-------|
| Platform | Render |
| Service name | `vecinita-data-management-api-v1` |
| Service type | web |
| Plan | starter |
| Region | virginia |
| Auto-deploy trigger | checksPass |
| Health check path | `/health` |
| Port | 10000 |
| Start command | `uvicorn vecinita_scraper.api.server:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}` |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | 1 |
| Max instances | 1 (starter plan) |
| Scaling trigger | n/a (single instance) |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | Structured JSON (structlog) | `LOG_LEVEL=INFO` |
| Health check | `GET /health` (Render + Dockerfile HEALTHCHECK) | 30s interval, 10s timeout, 40s start period, 5 retries |
| Request logging | HTTP middleware in `vecinita_scraper.api.server` | Logs method, path, status code |
| Auth logging | Auth guard middleware | Logs rejected keys with fingerprint |
| Error handling | Global exception handler | Logs unhandled exceptions, returns 500 |

## CI/CD

| Stage | Tool | Config |
|-------|------|--------|
| Lint/validate | GitHub Actions | `apis/data-management-api/.github/workflows/ci.yml` |
| Deploy | GitHub Actions → Render deploy hook | `apis/data-management-api/.github/workflows/deploy.yml` |
| Render auto-deploy | Render checksPass trigger | `render.yaml` |

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)

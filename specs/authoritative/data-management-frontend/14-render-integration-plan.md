# data-management-frontend — Render Integration Plan

> Auto-generated: 2026-05-12

## Overview

Deployed as `vecinita-data-management-frontend-v1` on Render, serving the Vite-built SPA.

## Service Definition

| Property | Value |
|----------|-------|
| Name | `vecinita-data-management-frontend-v1` |
| Type | Web service (Docker) |
| Dockerfile | `frontends/data-management/Dockerfile` |
| Docker context | `./frontends/data-management` |
| Plan | Starter |
| Health check | `/` |
| Region | Virginia |
| Auto-deploy trigger | checksPass |

## Environment Variables

| Variable | Source | Type |
|----------|--------|------|
| PORT | Inline: `10000` | Render Docker default |
| VITE_DM_API_BASE_URL | Env group | DM API URL (sync: false) |
| VITE_DEFAULT_SCRAPER_USER_ID | Env group | Default scraper user ID (sync: false) |
| VITE_EMBEDDING_UPSTREAM_URL | Env group | Embedding service URL (sync: false) |
| VITE_OLLAMA_BASE_URL | Env group | Ollama base URL (sync: false) |

Note: `VITE_*` variables are baked into the static bundle at build time.

## Database Binding

None — the DM frontend does not access the database directly.

## Service-to-Service Bindings

| Target Service | Variable | Mechanism |
|----------------|----------|-----------|
| vecinita-data-management-api-v1 | `VITE_DM_API_BASE_URL` | External URL (env group, not fromService) |

## Preview Environments

DM frontend preview services created for PRs targeting `main`. Preview builds connect to the preview DM API instance.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)

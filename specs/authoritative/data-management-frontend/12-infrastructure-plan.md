# data-management-frontend — Infrastructure Plan

> Auto-generated: 2026-05-12

## Overview

Built as a static SPA via Vite, served in a Docker container on Render.

## Build

| Property | Value |
|----------|-------|
| Dockerfile | `frontends/data-management/Dockerfile` |
| Build context | `./frontends/data-management` |
| Base image | Node (build) → nginx or node-serve (runtime) |
| Build command | `vite build` |
| Build output | `dist/` |

## Deployment

| Property | Value |
|----------|-------|
| Platform | Render |
| Service type | Web service (Docker) |
| Plan/tier | Starter |
| Region | Virginia |
| Auto-deploy | checksPass |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | 1 |
| Max instances | 1 (starter plan) |
| Scaling trigger | N/A — static files |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | Render service logs | stdout |
| Health check | `GET /` | Returns index.html (200) |

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)

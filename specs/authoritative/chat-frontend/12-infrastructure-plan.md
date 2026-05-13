# chat-frontend — Infrastructure Plan

> Auto-generated: 2026-05-12

## Overview

The chat frontend is built as a static SPA via Vite, served by nginx in a Docker container on Render.

## Build

| Property | Value |
|----------|-------|
| Dockerfile | `frontends/chat/Dockerfile` |
| Build context | `./frontends/chat` |
| Base image | Node (build stage) → nginx (runtime stage) |
| Build command | `vite build` |
| Build output | `dist/` directory (static assets) |

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
| Scaling trigger | N/A — static files served by nginx |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | Render service logs (nginx stdout) | Default |
| Health check | `GET /health` | nginx returns 200 |
| Error tracking | Browser console | No external service |

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)

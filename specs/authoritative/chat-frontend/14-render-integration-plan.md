# chat-frontend — Render Integration Plan

> Auto-generated: 2026-05-12

## Overview

The chat frontend is deployed as `vecinita-frontend` on Render, serving the Vite-built SPA via nginx in a Docker container.

## Service Definition

| Property | Value |
|----------|-------|
| Name | `vecinita-frontend` |
| Type | Web service (Docker) |
| Dockerfile | `frontends/chat/Dockerfile` |
| Docker context | `./frontends/chat` |
| Start command | nginx (Dockerfile CMD) |
| Plan | Starter |
| Health check | `/health` |
| Region | Virginia |
| Auto-deploy trigger | checksPass |

## Environment Variables

| Variable | Source | Type |
|----------|--------|------|
| PORT | Inline: `10000` | Render Docker default |
| VITE_GATEWAY_URL | Env group | Gateway API URL (sync: false) |
| VITE_BACKEND_URL | Env group | Fallback gateway URL (sync: false) |
| VITE_AGENT_REQUEST_TIMEOUT_MS | Env group | Non-stream request timeout (sync: false) |
| VITE_AGENT_STREAM_TIMEOUT_MS | Env group | Overall stream timeout (sync: false) |
| VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS | Env group | First SSE event timeout (sync: false) |
| VITE_DEV_ADMIN_ENABLED | Env group | Enable admin auth (sync: false) |
| VITE_DEV_ADMIN_EMAIL | Env group | Admin login email (sync: false) |
| VITE_DEV_ADMIN_PASSWORD | Env group | Admin login password (sync: false) |

Note: `VITE_*` variables are baked into the static bundle at build time.

## Database Binding

None — the chat frontend does not access the database directly.

## Service-to-Service Bindings

| Target Service | Variable | Mechanism |
|----------------|----------|-----------|
| vecinita-gateway | `VITE_GATEWAY_URL` | External URL (env group, not fromService) |

## Preview Environments

Chat frontend preview services are created for PRs targeting `main`. Preview builds use the same Dockerfile and connect to the preview gateway instance via `VITE_GATEWAY_URL`.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)

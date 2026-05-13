# pgadmin — Infrastructure Plan

> Auto-generated: 2026-05-12

## Overview

pgAdmin runs exclusively in local Docker Compose. It is not deployed to Render, Modal, or any cloud environment.

## Build

| Property | Value |
|----------|-------|
| Dockerfile | N/A — uses pre-built `dpage/pgadmin4` image |
| Build context | N/A |
| Base image | `dpage/pgadmin4:latest` |
| Build args | None |

## Deployment

| Property | Value |
|----------|-------|
| Platform | Local Docker Compose only |
| Service type | Web UI (internal) |
| Plan/tier | N/A — local only |
| Region | N/A |
| Auto-deploy | N/A |

## Docker Compose Configuration

**Source:** `docker-compose.yml` — pgadmin service definition

| Property | Value |
|----------|-------|
| Image | `dpage/pgadmin4` |
| Container port | 80 |
| Host port | 5050 |
| Network | Shared Docker network with PostgreSQL |
| Depends on | `postgres` service |

### Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `PGADMIN_DEFAULT_EMAIL` | Configured in docker-compose | Login email |
| `PGADMIN_DEFAULT_PASSWORD` | Configured in docker-compose | Login password |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | 1 (local) |
| Max instances | 1 |
| Scaling trigger | N/A — single developer tool |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | Docker container logs (`docker logs pgadmin`) | stdout |
| Health check | HTTP GET on container port 80 | Docker health check |

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)

# pgadmin — API Contract

> Auto-generated: 2026-05-12

## Overview

pgAdmin exposes a web UI, not a programmatic API consumed by other Vecinita services. The only "API" is the browser-based interface used by the developer.

## Base URL

| Environment | URL |
|-------------|-----|
| Local (Docker Compose) | `http://localhost:5050` |
| Render | N/A — not deployed to Render |

## Endpoints

pgAdmin's internal HTTP API is consumed only by its own web frontend. No Vecinita service calls pgAdmin programmatically.

### Web UI (browser-only)

| Property | Value |
|----------|-------|
| Auth | Email/password login (configured via `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`) |
| Protocol | HTTP (port 5050) |
| Consumers | Solo developer via browser only |

## Schemas

N/A — pgAdmin uses its own internal API schemas, not part of the Vecinita API surface.

## Versioning

Determined by the `dpage/pgadmin4` Docker image tag. Currently uses `latest`.

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)

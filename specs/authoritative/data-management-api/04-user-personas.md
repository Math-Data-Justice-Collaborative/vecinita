# Data Management API — User Personas

> Auto-generated: 2026-05-12

## Overview

The data-management API serves a small set of operator-level personas. It is not
directly accessed by end users — community members interact with the chat
frontend, which uses the gateway. This API serves the **data management**
dashboard and automated systems.

## Personas

### Data Operator

| Attribute | Value |
|-----------|-------|
| Role | Community data administrator who curates civic information |
| Interaction mode | UI (data-management SPA) |
| Goals | Submit scrape jobs, monitor progress, review extracted content, trigger embeddings/predictions |
| Pain points | Long scrape times, unclear job failure reasons, needing to understand multiple service URLs |

### Platform Administrator

| Attribute | Value |
|-----------|-------|
| Role | Developer or DevOps engineer managing the Vecinita platform |
| Interaction mode | API (direct HTTP / cURL) and Render dashboard |
| Goals | Monitor service health, debug integration issues, manage environment configuration |
| Pain points | Complex multi-service topology, Modal vs HTTP routing decisions, Postgres connectivity |

### Data Management SPA (System)

| Attribute | Value |
|-----------|-------|
| Role | React/Vite frontend application |
| Interaction mode | Automated HTTP calls |
| Goals | Provide a unified browser interface over the API surface |
| Pain points | CORS configuration, single-origin constraint, auth token management |

### Gateway Service (System)

| Attribute | Value |
|-----------|-------|
| Role | API gateway that may proxy requests to the data-management API |
| Interaction mode | Internal HTTP |
| Goals | Route data-management traffic through a single gateway origin |
| Pain points | Service discovery, health check aggregation |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Data Operator | `/jobs`, `/embed`, `/predict` via SPA | write (bearer token via SPA) |
| Platform Administrator | `/health`, `/jobs` directly | read / admin |
| Data Management SPA | All endpoints | write (bearer token) |
| Gateway Service | All endpoints (proxy) | write (internal) |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)

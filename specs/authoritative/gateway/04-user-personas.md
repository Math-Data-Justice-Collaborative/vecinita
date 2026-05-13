# User Personas: Gateway
> Auto-generated: 2026-05-12

See [diagrams/user-personas.md](diagrams/user-personas.md) for the actor diagram.

## Personas

### Community Member (End User)

| Property | Value |
|----------|-------|
| Channel | Chat frontend → gateway |
| Goals | Ask questions about civic/community topics, browse knowledge base documents |
| Endpoints | `/api/v1/ask`, `/api/v1/ask/stream`, `/api/v1/ask/config`, `/api/v1/documents/overview`, `/api/v1/documents/preview`, `/api/v1/documents/tags` |
| Auth | Optional (Bearer token when `ENABLE_AUTH=true`) |
| Pain points | Slow LLM responses, missing sources, language barriers (EN/ES) |

### Data Manager (Admin)

| Property | Value |
|----------|-------|
| Channel | Data management frontend → gateway |
| Goals | Submit scrape jobs, monitor job status, trigger reindex, manage embeddings |
| Endpoints | `/api/v1/scrape/*`, `/api/v1/modal-jobs/*`, `/api/v1/embed/*` |
| Auth | Bearer token (required for write operations) |
| Pain points | Job failures without clear errors, dedup confusion, pipeline stage opacity |

### Platform Operator (DevOps)

| Property | Value |
|----------|-------|
| Channel | CLI / monitoring / Render dashboard |
| Goals | Monitor service health, diagnose integration failures, manage deployments |
| Endpoints | `/health`, `/integrations/status`, `/config` |
| Auth | None (health endpoints are public) |
| Pain points | Silent dependency degradation, missing correlation IDs, rate limit tuning |

### Agent Service (Internal)

| Property | Value |
|----------|-------|
| Type | Automated system |
| Relationship | Gateway proxies to agent; agent does not call gateway |
| Protocol | HTTP REST |

### Modal Workers (Internal)

| Property | Value |
|----------|-------|
| Type | Automated system |
| Relationship | Gateway invokes Modal functions; Modal workers call gateway internal pipeline endpoints |
| Protocol | Modal SDK (outbound), HTTP + `X-Scraper-Pipeline-Ingest-Token` (inbound) |

### Chat Frontend (System)

| Property | Value |
|----------|-------|
| Type | SPA (React/Vite) |
| Relationship | Primary consumer of ask, stream, config, and documents endpoints |
| Protocol | HTTP + SSE |

### Data Management Frontend (System)

| Property | Value |
|----------|-------|
| Type | SPA |
| Relationship | Consumer of scrape, modal-jobs, embed, and documents endpoints |
| Protocol | HTTP |

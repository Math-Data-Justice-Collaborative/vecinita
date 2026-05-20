# ADR-001: Five-application monorepo architecture

**Status:** Accepted  
**Stage:** 00-context  
**Date:** 2026-05-19

## Context

Vecinita is rebuilt as a fresh monorepo (`vecinita`, branch `fresh-start`) combining a bilingual community Q&A RAG chatbot and a data management platform. The user specified five applications: ChatRAG Backend, ChatRAG Frontend, Data Management Backend, Data Management Frontend, and Database (resolution R1).

## Decision

Organize the monorepo around five deployable applications under `apps/`:

| App | Role | Primary runtime |
|-----|------|-----------------|
| `chat-rag-backend` | RAG orchestration (LlamaIndex, `/api/v1/ask`, `/api/v1/ask/stream`) | DigitalOcean App Platform |
| `chat-rag-frontend` | Chat UI (bilingual Q&A) | DigitalOcean static / App Platform |
| `data-management-backend` | Ingest jobs, corpus admin API, embedding orchestration | Modal (workers + thin API) + DO gateway optional |
| `data-management-frontend` | Admin UI (corpus list/delete, scrape jobs, job status) | DigitalOcean static / App Platform |
| `database` | Postgres + pgvector schema, migrations, seeds | DigitalOcean Managed Postgres |

Shared logic lives in `packages/` (schemas, rag, ingest, embedding clients). `packages/` must not depend on `apps/`.

**Sixth deployable (ADR-010):** `apps/internal-write-api` is a separate DO App Platform service (not a sixth `apps/` product in R1). It holds `DATABASE_URL` for Modal→Postgres writes per ADR-007.

## Consequences

- Clear ownership and deploy boundaries per app.
- Two frontends and two backends avoid coupling chat UX to admin workflows.
- Database is a first-class artifact (migrations, not an afterthought).
- Cross-app contracts require OpenAPI and shared schemas in `packages/`.

## References

- Resolution R1 (context-brief.md)
- User query: five applications + deployment planning

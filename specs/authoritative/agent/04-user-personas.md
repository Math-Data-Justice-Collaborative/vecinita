# Vecinita Agent — User Personas

> Auto-generated: 2026-05-12

## Overview

The agent service is not directly accessed by end users. All human interaction flows through the chat frontend and gateway. The agent's "users" are other services and operators.

## Personas

### Community Member (indirect)

| Attribute | Value |
|-----------|-------|
| Role | End user seeking civic information |
| Interaction mode | Indirect — via Chat Frontend → Gateway → Agent |
| Goals | Find community resources, health services, environmental info in the Woonasquatucket River Watershed / Rhode Island area |
| Pain points | Language barriers (English/Spanish), vague queries returning no results, slow response times |

### Gateway Service (system)

| Attribute | Value |
|-----------|-------|
| Role | Internal API consumer |
| Interaction mode | HTTP REST (automated) |
| Goals | Proxy user questions to the agent, receive structured answers for the frontend |
| Pain points | Agent downtime blocking user-facing flows, slow LLM responses causing timeouts |

### Operator / Developer

| Attribute | Value |
|-----------|-------|
| Role | System administrator / developer |
| Interaction mode | API (direct HTTP, Swagger UI at `/docs`) |
| Goals | Monitor health, diagnose retrieval issues, inspect database state, switch models |
| Pain points | Limited observability into retrieval quality, no admin dashboard |

### Data Pipeline (system)

| Attribute | Value |
|-----------|-------|
| Role | Automated data ingestion |
| Interaction mode | Direct PostgreSQL writes (vector_loader) |
| Goals | Load scraped document chunks with embeddings into the knowledge base |
| Pain points | Schema mismatches, embedding dimension changes, batch failure recovery |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Community Member | Chat Frontend → Gateway → `/ask`, `/ask-stream` | read (via proxy) |
| Gateway Service | `/ask`, `/ask-stream`, `/health`, `/config` | read |
| Operator / Developer | `/docs`, `/health`, `/test-db-search`, `/db-info`, `/config`, `/model-selection` | read / write (model selection) |
| Data Pipeline | PostgreSQL `document_chunks` table (direct) | write |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)

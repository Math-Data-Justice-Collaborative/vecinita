# ADR-010: Multi-app DigitalOcean deployment topology

**Status:** Accepted (cost validation **passed** for pilot — see execution-plan §Cost Estimate)  
**Stage:** 01-requirements (deployment batch)  
**Date:** 2026-05-19

## Context

ADR-001 defines **five logical applications**. ADR-004 urges **cost consolidation** (≤ $25/mo target, ≤ $50/mo cap) and warns that five always-on App Platform components may exceed budget.

Resolution **R6** (API gateway) remains unresolved. The deployment batch selected **multi-app** on DigitalOcean App Platform (RD-022): separate deployables per backend/frontend rather than a single consolidated Droplet.

## Decision

### v1 DigitalOcean deployables (minimum)

| Deploy unit | Platform | Role |
|-------------|----------|------|
| `chat-rag-backend` | DO App Platform | FastAPI + LlamaIndex + pgvector read |
| `chat-rag-frontend` | DO App Platform (static) | React/Vite chat UI |
| `data-management-frontend` | DO App Platform (static) | Admin UI |
| DO internal write API | DO App Platform | **Separate app** — sole `DATABASE_URL` for writes from Modal |
| Managed Postgres | DO Managed DB | System of record |

**Not on DO:** Modal ASGI, scrape queues, FastEmbed, vLLM (ADR-002).

### Gateway

- **v1:** No dedicated BFF/gateway — frontends call backend URLs directly (R6 deferred).
- Data Management UI calls Modal ASGI with edge-injected secrets; ChatRAG UI calls DO ChatRAG API.

### Cost gate

`04-tech-plan` **must** produce a line-item estimate proving ≤ **$50/mo** (path to **$25/mo**) or raise `[Decision]` to consolidate apps (e.g. single DO service running multiple processes).

## Alternatives considered

| Alternative | Why rejected for v1 default |
|-------------|----------------------------|
| Single Droplet, all processes | User selected multi-app (RD-022); may return if cost fails |
| Dedicated DO API gateway (R6) | Deferred — adds always-on cost |
| Render proxy (siblings) | Superseded by DO per ADR-002 |

## Consequences

- CI/CD needs multiple DO app specs plus Modal deploy pipelines.
- Internal write API is not bundled into ChatRAG Backend — clearer security boundary (ADR-007).
- **Risk R1** in risk register: multi-app + vLLM vs ADR-004 cap.
- Local dev still uses `docker-compose` mimicking DO tier + `modal serve` (RD-011).

## References

- RD-022, R6 (`docs/context-brief.md`, `docs/requirements-decisions.md`)
- `docs/deployment-integration.md` §Services, §Topology note
- `docs/risk-register.md` R1
- ADR-001, ADR-004, ADR-007

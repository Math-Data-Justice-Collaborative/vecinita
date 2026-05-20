# ADR-002: Hybrid deployment — Modal workers + DigitalOcean control plane

**Status:** Accepted  
**Stage:** 00-context  
**Date:** 2026-05-19

## Context

The user initially named Modal as the deployment target, then selected **hybrid Modal + DigitalOcean** (resolution R2): Modal for GPU/async workers; DigitalOcean for APIs, frontends, and Postgres.

Prior sibling repos split Modal (scraper, embedding, model) from Render (proxy). The greenfield design standardizes the non-Modal tier on DigitalOcean.

## Decision

| Layer | Platform | Workloads |
|-------|----------|-----------|
| **Compute (async / GPU)** | Modal | Scrape pipeline queues, batch embedding, optional LLM inference containers |
| **HTTP APIs** | DigitalOcean App Platform | ChatRAG API, **DO internal write API** (corpus persist); optional API gateway |
| **HTTP APIs (Modal)** | Modal ASGI (`requires_proxy_auth`) | Data-management **`/jobs`** job submit/status (RD-019); not on DO |
| **Frontends** | DigitalOcean App Platform or Spaces + CDN | Both React/Vite SPAs |
| **Database** | DigitalOcean Managed Postgres (+ pgvector) | System of record |

Modal credentials (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`) stay on DO backends only — never in browser bundles. Modal `@modal.asgi_app(requires_proxy_auth=True)` remains the pattern for Modal-hosted HTTP entrypoints.

## Consequences

- 04-tech-plan must document DO app specs, DB sizing, and Modal app names separately.
- CI/CD needs two deploy pipelines (DO + `modal deploy`).
- Local dev uses Docker Compose for DO-tier services and `modal serve` for workers.
- Supabase (used in siblings) is **not** the default DB host unless changed in a later ADR.

## Alternatives considered

- Modal-only: rejected — user chose hybrid; frontends and managed Postgres fit DO better.
- Render proxy (sibling pattern): superseded by DO gateway or in-process routing on DO APIs.

## References

- Resolution R2 (context-brief.md)
- Sibling scan: vecinita-modal-proxy (Render), vecinita-scraper (Modal)

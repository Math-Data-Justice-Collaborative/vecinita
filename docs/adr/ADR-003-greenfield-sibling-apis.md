# ADR-003: Greenfield APIs — siblings as reference only

**Status:** Accepted  
**Stage:** 00-context  
**Date:** 2026-05-19

## Context

Seven sibling repositories under `/root/GitHub/VECINA/` implement an earlier split monorepo (submodules, Modal microservices, Render proxy). The user selected **no sibling repos as hard constraints** (resolution R3) while regenerating the context brief.

## Decision

- Implement **new** OpenAPI contracts in the fresh `vecinita` monorepo; do not inherit submodule layout or path-prefix routing as mandatory.
- Sibling code may be **ported or rewritten** during build; it is not a compatibility requirement for v1.
- Patterns worth adopting voluntarily: `VECINITA_*` env prefix, Modal `requires_proxy_auth`, pgvector 384-dim embeddings, split Modal worker vs API apps.

## Consequences

- 01-requirements defines API surface from user journeys, not from `rag-api.ts` or scraper `/jobs` drift.
- License audit required before copying substantial code from siblings.
- Legacy worktree LangGraph agent is a **reference implementation**, not a contract.

## References

- Resolution R3 (context-brief.md)

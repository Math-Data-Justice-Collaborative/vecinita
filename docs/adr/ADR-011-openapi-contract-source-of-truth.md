# ADR-011: OpenAPI as API contract source of truth

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

ADR-003 mandates **greenfield APIs** — contracts are not inherited from sibling `rag-api.ts`, scraper routes, or worktree gateway drift. Multiple HTTP surfaces exist: ChatRAG on DO, Data Management on Modal, DO internal write API.

Without a single machine-readable source of truth, frontends, backends, and tests diverge. Privacy rules (ADR-004) require schemas that **reject identity fields** on public routes.

## Decision

- **OpenAPI 3.x files** in the repo are the **authoritative** contract for each HTTP surface.
- Planned paths (from `docs/api-contract.md`):
  - `openapi/chat-rag.yaml` — `/api/v1/ask`, `/api/v1/ask/stream`, `/health`
  - `openapi/data-management.yaml` — Modal `/jobs`, `/jobs/{id}`, health
  - `openapi/internal-write.yaml` — DO write API (service-auth only)
- Human-readable `docs/api-contract.md` summarizes and links to OpenAPI; on conflict, **OpenAPI wins**.
- Public routes: `additionalProperties: false` where practical; no `email`, `user_id`, `name` in request bodies.
- Contract tests generated or hand-written against OpenAPI examples in CI.

### ChatRAG public routes (v1)

| Method | Path | Notes |
|--------|------|-------|
| POST | `/api/v1/ask` | Non-streaming Q&A (RD-018) |
| POST | `/api/v1/ask/stream` | SSE streaming |
| GET | `/health` | Dependency checks |

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| TypeScript types only (siblings) | Not enforced for Python Modal/DO backends |
| Implicit code-as-contract | Causes greenfield/sibling drift (ADR-003) |
| Postman collections only | Weaker CI integration than OpenAPI |

## Consequences

- New endpoints require OpenAPI update **before** implementation merges (build guardrail in 06-tech-tooling).
- Frontends use generated or hand-maintained clients from OpenAPI where worthwhile.
- Modal `requires_proxy_auth` documented in OpenAPI security schemes (RD-019).
- Breaking changes need version bump (`/api/v1` → future `v2`) and ADR or changelog note.

## References

- RD-018, RD-019, RD-020 (`docs/requirements-decisions.md`)
- `docs/api-contract.md`
- `docs/spec.md` §API surface
- ADR-003, ADR-004

# ADR-012: Monorepo layout — `apps/` and `packages/` dependency rule

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

Vecinita is a **five-application monorepo** (ADR-001). Shared RAG, ingest, schemas, and HTTP clients must be reused without circular imports or hidden coupling between deployables.

Sibling `vecinita-data-management` documented that shared code must not depend on application entrypoints. The 01-requirements interview confirmed paths from context-brief §9 (RD-014).

## Decision

### Directory layout

```text
vecinita/
  apps/
    chat-rag-backend/
    chat-rag-frontend/
    data-management-backend/   # Modal apps + DO-facing config
    data-management-frontend/
    database/                  # Alembic, seeds, privacy tests
  packages/
    shared-schemas/
    rag/                       # LlamaIndex (ADR-006)
    ingest/
    embedding-client/
  infra/
    docker-compose.yml
    modal/
  docs/
    adr/
    openapi/
```

### Dependency rule (hard)

- **`packages/*` must not import `apps/*`.**
- **`apps/*` may import `packages/*`.**
- Cross-app imports between `apps/*` are forbidden — share via `packages/` only.

### Environment convention

- Adopt sibling pattern: **`VECINITA_*`** env prefix for configuration.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Separate git repos per app | User chose single monorepo (R1) |
| `apps/chat-rag-backend` imports `apps/database` | Violates deploy boundaries; use packages + API |
| Flat `src/` only (RFantibody template) | Wrong product; stale Cursor rules — R7 tooling debt |

## Consequences

- Lint/import hooks in 06-tech-tooling should fail CI on `packages → apps` imports.
- OpenAPI and Pydantic models gravitate to `packages/shared-schemas`.
- Each app owns its own `pyproject.toml` or workspace root coordinates versions — exact tooling in `04-tech-plan`.
- Modal code for data-management lives under `apps/data-management-backend` but shared logic stays in `packages/ingest`.

## References

- RD-014 (`docs/requirements-decisions.md`)
- `docs/context-brief.md` §9 Proposed Monorepo Layout
- `docs/spec.md` §Component Overview, H9
- ADR-001, ADR-006

# ADR-008: FastEmbed 384-dimensional embeddings on Modal

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

Both **ingest** and **query** paths require text embeddings. Sibling `vecinita-embedding` used **FastEmbed** on Modal with a model volume. The user requires **self-hosted** inference (ADR-004) — no default paid embedding APIs.

Embedding dimension must match pgvector column definition (ADR-005). Siblings and migrations referenced **384 dimensions** (resolution R8 default).

## Decision

- **Library:** FastEmbed on Modal (`vecinita-embedding` app or equivalent module under `apps/data-management-backend`).
- **Dimension:** **384** — Postgres columns use `vector(384)`.
- **Deployment:** Separate Modal app for embedding HTTP (`/embed`, `/embed/batch`); scale-to-zero where supported.
- **Model weights:** Modal volume or baked image; download from Hugging Face at deploy — not stored in Vecinita DB.
- **Consumers:** Ingest workers (batch embed) and ChatRAG Backend (query embed) call Modal over HTTP with credentials on DO only.

### Not in scope for v1 default

- OpenAI / Cohere / Voyage embedding APIs (require ADR exception per ADR-004).
- Multiple embedding dimensions in one schema.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| OpenAI `text-embedding-*` | Cost + sovereignty + ADR-004 default ban |
| Embed on DO CPU | Slower; Modal already used for GPU/async tier |
| 768/1536-dim models | Schema and sibling reference use 384; change needs migration ADR |

## Consequences

- Alembic migrations must declare `vector(384)` consistently.
- Changing model/dimension requires new ADR, migration, and re-embed corpus.
- ChatRAG and ingest share one embedding service — version skew breaks retrieval.
- License audit before copying sibling embedding code (ADR-003).

## References

- RD-007, R8 (`docs/context-brief.md`, `docs/requirements-decisions.md`)
- feature-list F10 (`docs/feature-list.md`)
- ADR-004, ADR-005, ADR-007

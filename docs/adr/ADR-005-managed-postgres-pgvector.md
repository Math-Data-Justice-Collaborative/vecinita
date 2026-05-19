# ADR-005: DigitalOcean Managed Postgres with pgvector

**Status:** Accepted  
**Stage:** 01-requirements  
**Date:** 2026-05-19

## Context

Vecinita needs a single system of record for corpus documents, chunks, embeddings, and ingest job metadata. Sibling repos used **Supabase** (hosted Postgres + Auth). The user chose **DigitalOcean Managed Postgres** as part of the hybrid deployment (resolution R4) and **zero personal data** (ADR-004), which rules out Supabase Auth and identity-linked tables.

The legacy worktree used **Chroma** as primary vector store with pgvector as fallback. Operating two vector stores increases complexity and violates the greenfield simplification goal.

## Decision

- **Host:** DigitalOcean Managed Postgres (PostgreSQL 15+) in **US regions** (`nyc1` / `sfo3`) per ADR-004.
- **Vector extension:** `pgvector` enabled on the same database; **no separate vector DB** in v1.
- **Default embedding dimension:** `vector(384)` aligned with FastEmbed (ADR-008).
- **Database app:** Schema, Alembic migrations, seeds, and privacy tests live in `apps/database/` (ADR-001).
- **Supabase:** Not used as DB host or auth provider in v1.

### Schema domains (allowed)

| Domain | Examples |
|--------|----------|
| Corpus | `documents`, `chunks`, `embeddings` |
| Jobs | `jobs` (URL, status — no operator identity) |
| Config | Operational non-PII flags |

Forbidden tables/columns per ADR-004: `users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Supabase (siblings) | Auth/invite patterns violate ADR-004; DO chosen in R2 |
| Chroma + Postgres dual store | Ops complexity; worktree pattern not adopted |
| Modal Volume for corpus | Ephemeral; violates durability and sovereignty for corpus |
| Separate vector SaaS (Pinecone, etc.) | Cost + sovereignty; pgvector sufficient for v1 scale |

## Consequences

- All RAG retrieval reads vectors from DO Postgres (ChatRAG Backend holds read `DATABASE_URL`).
- Modal workers **do not** connect to Postgres directly — see ADR-007.
- Migration and seed workflows are first-class in the five-app layout.
- Corpus size growth drives DO Postgres tier sizing in `04-tech-plan` (cost risk vs ADR-004 cap).

## References

- Resolution R4 (`docs/context-brief.md`)
- RD-007, RD-009 (`docs/requirements-decisions.md`)
- feature-list F5, F13 (`docs/feature-list.md`)
- ADR-001, ADR-004

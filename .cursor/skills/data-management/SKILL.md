---
name: data-management
description: >
  Prepares Vecinita's database schema, seed corpus, and eval fixtures before build-executor
  runs tasks that need real documents or vectors. Reads docs/data-management-plan.md,
  applies migrations, loads fixtures, verifies row counts and embedding dimensions, and
  documents local/staging procedures. Use when the RAG service needs a populated DB or
  verified migrations before implementation or deploy.
---

# Data Management (Vecinita)

Prepare the **database** and **corpus fixtures** so build-executor and integration tests
can run ingest, retrieval, and admin flows without manual setup.

## Purpose

Vecinita depends on:

1. **Schema** — migrations applied (documents, chunks, embeddings, jobs)
2. **Fixtures** — dev/staging seed documents and optional eval Q&A sets
3. **Verification** — dimensions, FK integrity, no duplicate checksums
4. **Documentation** — how to reset local DB and re-seed

This skill bridges **04-tech-plan** (`docs/data-management-plan.md`) and **07-build**.

## Prerequisites

1. `docs/data-management-plan.md` (from doc-planner or 04-tech-plan)
2. `docs/deployment-integration.md` — DB URL pattern, migration hook
3. `docs/execution-plan.md` — tasks listing data deps

## State

Track in `docs/data-management-state.md` (same phase table pattern as legacy data-staging).

## Workflow (summary)

### Phase 1 — Parse requirements

Extract from data-management-plan: migrations, fixtures, eval sets, embedding model + dim.

### Phase 2 — Local database

- Start Postgres (Docker Compose or existing)
- `alembic upgrade head` (or project equivalent)
- Confirm extensions (`vector`) installed

### Phase 3 — Seed corpus

- Run `scripts/seed_corpus.py` or documented commands
- Record document/chunk counts in state file

### Phase 4 — Verify

- `scripts/verify_data.py`: row counts, orphan checks, vector dimension
- Optional: run eval_set retrieval expectations (ids only, not LLM judge)

### Phase 5 — Staging notes

- Document staging migrate + seed policy (no production PII unless approved)
- Align with `docs/deployment-integration.md` CI hooks

## AskQuestion triggers

| Category | Example |
|----------|---------|
| **Decision** | pgvector vs external vector DB for staging |
| **Blocker** | `DATABASE_URL` missing |
| **Ambiguity** | Which embedding model revision pins vector column |

## Output rules

1. Never load production customer data without explicit approval.
2. Migrations are forward-only unless ADR says otherwise.
3. Generate reusable `scripts/verify_data.py` and document in `data/README.md`.
4. Report embedding dimension mismatches as blocking before build tasks that embed.

## Ready for

build-executor / 07-build once status is `complete`.

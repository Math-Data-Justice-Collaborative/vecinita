# Data Management Plan

> **Project**: Vecinita  
> **Last updated**: 2026-05-24 (EV-001 tagging schema)

## Overview

Vecinita stores **public corpus data only** in DO Postgres: documents, chunks, 384-dim embeddings, and scrape job metadata. No PII. Assets must be staged before integration/E2E tests that hit real retrieval.

### Total data budget (initial)

| Metric | Value |
|--------|-------|
| Total assets | 4+ fixture groups |
| Total size (local) | < 500 MB (fixtures + seed corpus) |
| Auth-gated assets | 0 (public URLs / bundled fixtures) |

## Asset inventory

| # | Asset | Type | Source | Auth | Needed by |
|---|-------|------|--------|------|-----------|
| D1 | Seed corpus EN | corpus_fixture | `data/fixtures/corpus/en/` | none | TC-001, UJ-001 |
| D2 | Seed corpus ES | corpus_fixture | `data/fixtures/corpus/es/` | none | TC-011 |
| D3 | Eval Q&A pairs | eval_set | `data/fixtures/eval/` | none | Acceptance benchmarks |
| D4 | Ingest HTML fixture | corpus_fixture | `data/fixtures/ingest/` | none | TC-010 |
| D5 | Alembic migrations | migration | `apps/database/alembic/` | none | All DB tests |
| D6 | FastEmbed model weights | model_weights | Hugging Face → Modal volume | HF token if gated | Modal embed |
| D8 | Seed tag vocabulary | config_fixture | `data/fixtures/tags/seed_tags.json` | none | TC-041, F20 |
| D9 | Tagged corpus eval | corpus_fixture | `data/fixtures/corpus/tagged/` | none | TC-040, TC-044 |

## Schema (allowed tables)

| Table | Purpose | PII |
|-------|---------|-----|
| `documents` | Source metadata (url, title, hash) | No |
| `chunks` | Text segments | No |
| `embeddings` | vector(384) + chunk_id | No |
| `jobs` | Scrape job status, urls | No |
| `config` | Operational flags | No |
| `tags` | Normalized tag labels (language, slug) | No |
| `document_tags` | Document ↔ tag assignments (`source`: llm \| human) | No |
| `chunk_tags` | Chunk ↔ tag assignments (`source`: llm \| human) | No |

**Forbidden:** `users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`, `created_by`, operator identity columns on tag tables — enforced by migrations + `tests/privacy/`.

## Sources

- **Fixtures:** Committed in repo under `data/fixtures/` (small, public domain or synthetic).
- **Production corpus:** Public community URLs only; ingested via operator jobs.
- **Models:** Download scripts in `infra/modal/` (04-tech-plan); volumes `embedding-models`, `llm-models`.

## Verification

| Asset | Check |
|-------|-------|
| Fixtures | SHA256 manifest in `data/fixtures/MANIFEST.json` |
| Migrations | `alembic upgrade head` on empty DB |
| pgvector | `SELECT extversion FROM pg_extension WHERE extname='vector'` |
| Embedding dim | `vector_dims(embedding) = 384` sample query |

## Local paths

```text
data/
  fixtures/
    corpus/en/
    corpus/es/
    eval/
    ingest/
apps/database/
  alembic/
  seeds/
```

Add `data/fixtures/**/*.parquet` or large blobs to `.gitignore` if needed; keep manifest in git.

## Staging environments

| Env | Corpus policy |
|-----|---------------|
| Local | Full fixtures + seeds |
| Staging | Fixtures + optional pilot URLs |
| Production | Ingested public URLs **plus** committed seed/eval fixtures allowed (audited S9.2 — user denied “fixtures forbidden in prod”) |

## Quick start

```bash
docker-compose up -d postgres
cd apps/database && alembic upgrade head && python -m seeds.load
# Modal volumes: see infra/modal/README (04-tech-plan)
```

## Dependencies (execution plan)

| Task area | Minimum assets |
|-----------|----------------|
| Database app | D5 |
| ChatRAG tests | D1, D2, D5 |
| Ingest E2E | D4, D5 |
| Modal embed/LLM deploy | D6, D7 |

## Open questions

- Exact vLLM model choice and download size
- Soft-delete vs hard-delete for documents (v1: hard-delete per UJ-003)

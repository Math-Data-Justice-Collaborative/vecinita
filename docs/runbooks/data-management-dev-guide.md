# Data Management — Developer Guide

> **Audience:** Developers working on corpus schema, migrations, APIs, and local setup  
> **Issue:** [#52](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/52)  
> **Last updated:** 2026-07-03  
> **Operator procedures:** [corpus-operator-guide.md](corpus-operator-guide.md)

---

## Overview

Vecinita stores **public corpus data only** in DigitalOcean Managed Postgres: documents, text chunks, 384-dimensional embeddings, tags, and scrape job metadata. No end-user or operator PII in the corpus database (ADR-004); operator identity lives in **Supabase Auth** only (ADR-026).

**Apps involved:**

| App | Path | Role |
|-----|------|------|
| Database | `apps/database` | Alembic migrations, seeds, privacy tests |
| Internal write API | `apps/internal-write-api` | Sole `DATABASE_URL` holder for writes |
| Data mgmt backend | `apps/data-management-backend` | Modal ASGI + ingest workers |
| Data mgmt frontend | `apps/data-management-frontend` | Admin UI |
| ChatRAG backend | `apps/chat-rag-backend` | Read-only corpus access for RAG + public browse |

Architecture overview: [architecture.md](../architecture.md). Asset inventory: [data-management-plan.md](../data-management-plan.md).

---

## Schema

### Allowed tables (corpus DB)

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `documents` | Source metadata | `url`, `title`, `content_hash`, `language` |
| `chunks` | Text segments | `document_id`, `text`, `chunk_index` |
| `embeddings` | Vectors | `chunk_id`, `embedding vector(384)` |
| `jobs` | Scrape job status | `status`, `urls`, `error_code` |
| `config` | Operational flags | key/value |
| `tags` | Normalized labels | `slug`, `language` |
| `document_tags` | Doc ↔ tag | `source`: `llm` \| `human` |
| `chunk_tags` | Chunk ↔ tag | `source`: `llm` \| `human` |
| `audit_log` | Immutable write audit | `request_id`, `actor_id` (UUID), `actor_role` |
| `document_versions` | Version history | snapshot refs |
| `document_serving_stats` | Serving counters | per-document counts |
| `eval_runs` / `eval_run_items` | RAG evaluation (EV-008) | no PII columns |

### Forbidden (CI-enforced)

Tables or columns matching: `users`, `accounts`, `sessions`, `messages`, `profiles`, `invites`, `auth_*`, operator email/name on corpus tables.

Privacy regression: `tests/privacy/test_no_pii_tables.py`.

### pgvector

- Extension: `vector` on Postgres 15+
- Dimension: **384** (FastEmbed default — ADR-008)
- Verify: `SELECT vector_dims(embedding) FROM embeddings LIMIT 1;`

---

## Migrations

### Location

```
apps/database/
  alembic/
    versions/          # revision files
  alembic.ini
  src/vecinita_database/
    models/            # SQLAlchemy models
    seeds/             # load_corpus()
```

### Commands

```bash
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita

cd apps/database
uv run alembic upgrade head          # apply all
uv run alembic current               # show revision
uv run alembic heads                 # show head(s)
uv run alembic revision -m "description"  # new migration (dev)
```

### Deploy hook

On staging/production, run **before** DO app deploy when schema changes:

```bash
export DATABASE_URL='postgresql://...'
cd apps/database && uv run alembic upgrade head
```

Order: migrations → internal-write-api → dependent services. See [staging-runbook.md](../staging-runbook.md).

### Writing migrations safely

1. Never add forbidden table names (see above).
2. New columns on audit tables: no IP, email, or raw prompt text (ADR-016).
3. Run `uv run pytest tests/privacy/ -q` after schema changes.
4. Update [api-contract.md](../api-contract.md) if routes expose new fields.

---

## Seed corpus and fixtures

### Seed loader

```bash
cd apps/database
uv run alembic upgrade head
uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"
```

### Fixture layout

```text
data/fixtures/
  corpus/en/           # D1 — English seed documents
  corpus/es/           # D2 — Spanish seed documents
  corpus/tagged/       # D9 — tagged eval corpus
  ingest/              # D4 — HTML scrape fixtures
  eval/                # D3 — eval Q&A pairs
  tags/seed_tags.json  # D8 — tag vocabulary
```

Manifest: `data/fixtures/MANIFEST.json` (SHA256 checksums).

### Eval golden set

See [eval-golden-set.md](../eval-golden-set.md) for admin evaluation fixtures (EV-008).

---

## APIs

### Internal write API (`apps/internal-write-api`)

Base path: `/internal/v1/*`. Auth: Supabase JWT (operator) or `VECINITA_INTERNAL_API_KEY` (Modal).

| Area | Methods | Notes |
|------|---------|-------|
| Documents | GET list, DELETE, bulk ops | Admin JWT; viewer read-only |
| Chunks | GET list, PATCH tags | |
| Tags | PATCH document/chunk tags | |
| Stats | GET summary, top-served; POST served | ChatRAG fire-and-forget |
| Audit | GET global, GET per-doc history | No PII in rows |
| Health | GET `/internal/v1/health/all` | Polls all 8 services |
| Eval | POST/GET eval runs | EV-008 |

OpenAPI: check repo `openapi/` or app route modules. Contract: [api-contract.md](../api-contract.md).

### Modal data management (`apps/data-management-backend`)

| Method | Path | Auth |
|--------|------|------|
| POST | `/jobs` | Supabase JWT + Modal proxy |
| GET | `/jobs/{id}` | Supabase JWT + Modal proxy |

Workers call internal write API with service key — never direct Postgres.

### ChatRAG public browse (read-only)

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/v1/documents` | None |
| GET | `/api/v1/documents/{id}` | None |
| GET | `/api/v1/tags` | None |

---

## Local setup

Full bootstrap: [LOCAL_DEV.md](../LOCAL_DEV.md). Minimal path:

```bash
# 1. Postgres
docker compose -f infra/docker-compose.yml up -d postgres
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita

# 2. Migrations + seed
cd apps/database && uv run alembic upgrade head
uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"

# 3. Internal write API (port 8002)
export VECINITA_INTERNAL_API_KEY=dev-internal-key
uv run uvicorn vecinita_internal_write_api.app:create_app --factory --host 0.0.0.0 --port 8002

# 4. ChatRAG backend (port 8000) — mock or Modal URLs
export VECINITA_MODAL_EMBED_URL=http://localhost:8003
export VECINITA_MODAL_LLM_URL=http://localhost:8004
uv run uvicorn vecinita_chat_rag_backend.app:create_app --factory --host 0.0.0.0 --port 8000

# 5. Admin frontend (port 5174)
cd apps/data-management-frontend && cp .env.example .env && npm install && npm run dev
```

### Modal serve (optional — real embed/LLM)

```bash
export VECINITA_INTERNAL_WRITE_URL=http://localhost:8002
export VECINITA_INTERNAL_API_KEY=dev-internal-key
modal serve infra/modal/data_management_app.py
```

See [infra/modal/README.md](../../infra/modal/README.md).

### Tests without deploy

```bash
uv run pytest tests/unit tests/integration tests/privacy -q
# E2E local bootstrap:
uv run pytest tests/e2e/test_uj004_local_bootstrap.py -q
```

Integration tests mock Modal HTTP — no GPU required for CI.

---

## Privacy constraints (ADR-004)

| Rule | Enforcement |
|------|-------------|
| No PII in corpus DB | Schema deny-list + `tests/privacy/` |
| Stateless ChatRAG | No `messages` / `sessions` tables |
| No IP in audit | ADR-016 — `request_id` only |
| Operator identity in Supabase only | JWT at API edge; opaque UUID on audit |
| No default paid LLM/embed APIs | Self-hosted Modal inference |
| US-only infrastructure | DO + Modal US regions |

Supabase exception (ADR-026): admin login stores email/password in **Supabase `auth.*`**, not corpus Postgres.

---

## Package dependencies

```
packages/ingest       ← scrape/chunk (used by Modal workers)
packages/tagging      ← LLM tag prompts
packages/embedding-client → Modal FastEmbed HTTP
packages/rag          ← ChatRAG retrieval (read path)
packages/shared-schemas → request/response types
```

**Rule:** `packages/*` must not import `apps/*`.

---

## Known gaps (explicit)

| Gap | Where to track |
|-----|----------------|
| Soft-delete vs hard-delete for documents | data-management-plan §Open questions (v1: hard-delete) |
| PDF/multimodal ingest | Post-v1 |
| Exact vLLM download size / cost proof | execution-plan / ADR-009 |
| API gateway | Deferred (R6) — direct backend URLs in v1 |
| Staging corpus backup verification | [staging-runbook.md](../staging-runbook.md) §Corpus protection |

---

## References

- [corpus-operator-guide.md](corpus-operator-guide.md) — operator-facing workflows
- [architecture.md](../architecture.md) — hosting topology
- [data-flow.md](../data-flow.md) — ingest/query diagrams
- [staging-secrets-matrix.md](../staging-secrets-matrix.md) — env vars
- [ADR-005](../adr/ADR-005-managed-postgres-pgvector.md) — Postgres choice
- [ADR-007](../adr/ADR-007-modal-do-database-write-boundary.md) — write boundary
- [ADR-014](../adr/ADR-014-corpus-tagging-and-browse.md) — tagging model

# Template Registry — Vecinita (RAG + data management)

Central reference for **Vecinita** project templates. Pipeline stages (00–17) use this
registry to classify new work, select a scaffold, and validate conformance. Templates may
live as sibling repos in the org or as in-repo layouts once Vecinita matures.

## Template Catalog

| ID | Template | Typical stack | Project type | Signals |
|----|----------|---------------|--------------|---------|
| `api` | RAG API service | FastAPI (or similar) + Postgres/pgvector + object storage | Synchronous HTTP: ingest metadata, query, admin CRUD on corpus records | REST/OpenAPI, request/response in seconds, state in DB, no long GPU jobs in request path |
| `worker` | Ingestion / indexing worker | Queue (Redis/SQS) or scheduled jobs + embeddings + DB writes | Async: chunk documents, embed, upsert vectors, reindex, bulk import | Background jobs, idempotent tasks, retries, DLQ, minutes per batch |
| `monolith` | Combined API + worker (single deployable) | Same as both, one repo | Small teams, MVP, low ops surface | Single codebase runs API and worker process types (or one process with async tasks) |

## Classification Heuristics

Use during **00-context** or **01-requirements**:

### API signals

- Callers use HTTP (query, search, health, admin)
- Latency target: sub-second to low seconds per request
- Reads/writes go through the database (and optional cache)
- Embedding at query time may call an external API (OpenAI, etc.) — not a multi-hour batch

### Worker signals

- Bulk document import, re-embedding, index rebuild
- Jobs are retriable and tracked (status table or queue)
- Throughput and backpressure matter more than single-request latency
- May run on separate deploy target from API (Render worker, K8s Job, Celery)

### Monolith signals

- MVP or single-service deploy
- Worker logic invoked in-process (FastAPI background tasks) or same container with a second process
- User explicitly wants one deploy unit until scale demands split

### Ambiguous cases

Raise `[Decision]`:

```
prompt: "Project classification is ambiguous:
  API signals:    [list]
  Worker signals: [list]

  Which template fits best?"

options:
  1. "API — HTTP RAG service with DB-backed state"
  2. "Worker — async ingestion and indexing"
  3. "Monolith — API + worker in one deployable"
  4. "None — greenfield layout without a template"
  5. "Let me explain / provide more context"
```

## Template Structure Reference

### API (`api`)

```
src/
├── app.py              # ASGI entry (FastAPI app factory)
├── api/                # Routers: query, ingest, admin, health
├── rag/                # Retrieval, rerank, prompt assembly (no framework imports in tests)
├── db/                 # Models, repositories, migrations (Alembic/SQLAlchemy or equivalent)
└── config.py           # Settings from env

tests/
├── unit/
├── integration/        # DB + API with testcontainers or ephemeral DB
└── e2e/                # HTTP journeys (UJ-NNN)

migrations/             # Schema revisions
```

**Key patterns:**

- App name / service id: `vecinita` (or org prefix `cognichem-vecinita`)
- Config via environment variables (12-factor); secrets never in repo
- OpenAPI contract is source of truth for external surface
- Core RAG logic in `src/rag/` — testable without HTTP
- Database is system of record for documents, chunks, embeddings metadata

### Worker (`worker`)

```
src/
├── worker.py           # Job consumer entry
├── jobs/               # ingest, reindex, embed_batch, purge
├── rag/                # Shared with API template (embed, chunk)
└── db/                 # Same schema as API

tests/
├── unit/
└── integration/        # job handlers with test DB
```

**Key patterns:**

- Idempotent job handlers keyed by `job_id` / document version
- Progress persisted in DB (`ingestion_jobs`, `chunks`, etc.)
- Dead-letter or failed state visible to data-management admin APIs

### Monolith (`monolith`)

Combines API and worker layouts:

- `src/app.py` — HTTP
- `src/worker.py` or `src/jobs/runner.py` — background consumer
- Shared `db/`, `rag/`, `config.py`

## How Pipeline Stages Use Templates

| Stage | Template usage |
|-------|----------------|
| **00-context** | Classify repo vs templates; note existing DB, vector extension, queue |
| **01-requirements** | Pre-fill deployment, module layout, API vs worker split |
| **02-verify-plan** | Spec must not claim GPU batch in API template unless overridden |
| **03-plan-tooling** | Scope rules reference `docs/feature-list.md` + `docs/spec.md` components |
| **04-tech-plan** | Phase 1 scaffold from template; data-management plan for corpus + schema |
| **07-build** | First tasks: layout, migrations, health endpoint, minimal query path |
| **10-e2e** | HTTP for `api`/`monolith`; job completion polling for `worker` |
| **13-deploy-smoke** | Migrate DB, smoke query, optional ingest of fixture doc |
| **15-service-health** | Live API + DB + queue depth + retrieval smoke |

## Template Selection Output

Record in `workflow-state.yaml`:

```yaml
template:
  id: api | worker | monolith | none
  repo: null | path-to-template-repo
  selected_at: 00-context | 01-requirements
  classification_confidence: high | medium | low
  overridden_by_user: false | true
  service_name: vecinita
  database: postgres   # primary store; document in deployment-catalog.md
  vector_store: pgvector | external  # per ADR
```

## Adding New Templates

1. Document ID, signals, and directory layout in this file
2. Add classification heuristics
3. Update stage table if behavior differs
4. Add ADR when deviating from default Vecinita stack

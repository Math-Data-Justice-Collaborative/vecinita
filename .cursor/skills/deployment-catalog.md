# Deployment Catalog — Vecinita

Reference for **infrastructure choices** during technical planning (04-tech-plan) and
deploy verification (12–13). Not a mandate — user selections and ADRs override defaults.

## Primary data plane

| Component | Default | Alternatives | Notes |
|-----------|---------|--------------|-------|
| **Relational DB** | PostgreSQL 15+ | — | System of record: documents, chunks, jobs, ACLs |
| **Vector search** | pgvector extension | Pinecone, Weaviate, Qdrant, OpenSearch k-NN | Prefer pgvector for single-DB ops; external if scale/team requires |
| **Migrations** | Alembic (SQLAlchemy) | Drizzle, raw SQL flyway | Versioned schema; required before deploy smoke |
| **Object storage** | S3-compatible (optional) | Local FS dev only | Raw files if not inlined in DB |

## Application runtime

| Target | When to use | Smoke checks |
|--------|-------------|--------------|
| **Render** | Managed web + worker + Postgres | Health URL, migrate, sample query |
| **Fly.io** | Low-latency API + attached Postgres | Same |
| **Docker Compose** | Local dev / CI integration | `docker compose up`, test DB |
| **Kubernetes** | Org standard for multi-service | Helm release, job cron for worker |

Record chosen target in `docs/deployment-plan.md` and repo-root
[`workflow-state.yaml`](../../workflow-state.yaml) §`template.deploy` (see
[workflow-state-reference.md](workflow-state-reference.md)).

## Embeddings & LLM (external APIs)

| Provider | Env vars (examples) | Planning notes |
|----------|---------------------|----------------|
| OpenAI | `OPENAI_API_KEY` | Embedding + chat models; rate limits |
| Anthropic | `ANTHROPIC_API_KEY` | Generation only if not OpenAI |
| Local (optional) | `EMBEDDING_BASE_URL` | Dev-only; not default for production ADR |

Surface `[Decision]` if embedding model dimension ≠ existing vector column — requires migration.

## Caching & queues (optional)

| Component | Use case |
|-----------|----------|
| Redis | Query cache, rate limits, Celery broker |
| SQS / RabbitMQ | Worker job queue when not DB-backed outbox |

## Environment variables (minimum)

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes | Postgres connection |
| `OPENAI_API_KEY` or equivalent | If using hosted embeddings/LLM | Inference |
| `APP_ENV` | Yes | `development` / `staging` / `production` |
| `LOG_LEVEL` | No | Default `info` |

Never commit secrets. Use platform secret stores (Render, GitHub Actions secrets, etc.).

## Health check tiers (maps to 15-service-health)

| Tier | Scope | Example |
|------|-------|---------|
| H0 | Local unit/integration | `pytest tests/integration` |
| H1 | Deployed liveness | `GET /health` → 200 |
| H2 | DB ready | Migrations applied; `SELECT 1` |
| H3 | RAG smoke | Ingest fixture doc → query returns expected chunk id |
| H4 | Browser CORS | `OPTIONS` from frontend origin → `Access-Control-Allow-Origin` |
| H5 | Frontend bundle | Live JS contains staging API hosts (not `localhost`) |
| H6 | Full UJ suite | All `tests/e2e/` against staging URL or browser automation |

**Detail:** [connectivity-gates.md](connectivity-gates.md) — required for Vecinita hybrid (DO static + APIs).

## Performance planning hooks

| Metric | Typical interview question |
|--------|---------------------------|
| Query p95 latency | Target ms for retrieval + generation |
| Corpus size | Document count, avg chunk size, embedding dim |
| Ingest throughput | Docs/hour, max concurrent jobs |
| Cost | Embedding + LLM $/1k queries |

If unknown, surface `[Ambiguity]` in 01-requirements / 04-tech-plan — do not invent SLOs.

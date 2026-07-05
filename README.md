# Vecinita

Bilingual community Q&A (ChatRAG) and corpus data management — hybrid **DigitalOcean** + **Modal** stack with zero personal data (ADR-004).

## Apps

| App | Path | Role |
|-----|------|------|
| ChatRAG Backend | `apps/chat-rag-backend` | FastAPI `/api/v1/ask`, pgvector retrieval |
| ChatRAG Frontend | `apps/chat-rag-frontend` | React/Vite chat UI |
| Data Management | `apps/data-management-backend` | Modal ASGI `/jobs` |
| Data Mgmt Frontend | `apps/data-management-frontend` | Admin ingest UI |
| Database | `apps/database` | Alembic migrations + seeds |
| Internal write API | `apps/internal-write-api` | Sole `DATABASE_URL` holder for Modal writes |

Shared logic: `packages/rag`, `packages/ingest`, `packages/embedding-client`, `packages/llm-client`.

**EV-004 (planned):** Shared frontend packages — `packages/frontend-i18n` (en/es locale + messages) and `packages/frontend-ui` (React components consumed by both frontends). UI locale persists in browser `localStorage` key `vecinita.locale`.

## Quick start (local)

```bash
# 1. Postgres
docker compose -f infra/docker-compose.yml up -d postgres

# 2. Migrations + seed
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
cd apps/database && uv run alembic upgrade head && uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"

# 3. Tests (mocks Modal — no deploy required)
cd ../.. && bash scripts/run_tests.sh -q
```

Full bootstrap: **[docs/LOCAL_DEV.md](docs/LOCAL_DEV.md)** · non-secret defaults: **[infra/vecinita.yaml](infra/vecinita.yaml)**

## Features (v1 + EV-001 + EV-002 + EV-004)

| Area | Features |
|------|----------|
| ChatRAG | Bilingual Q&A, streaming, tag-filtered RAG, corpus browse, **en/es UI chrome** (F31 shared packages) |
| Data Management | URL ingest, job queue, corpus CRUD, LLM auto-tagging |
| Admin Dashboard | Summary stats, health checks, bulk operations, audit log, **en/es UI chrome** (F31) |
| Data Integrity | Serving statistics, version history, configurable retention |
| Privacy | Zero personal data (ADR-004), no IP tracking (ADR-016) |

## Docs

- [Architecture overview](docs/architecture.md) — service map, environments, deploy pipeline
- [Data flow diagrams](docs/data-flow.md) — Mermaid ingest/query/admin paths
- [Hosting migration summary](docs/hosting-migration-summary.md) — infrastructure switch overview
- [OSCAR feasibility (Carlos review)](docs/oscar-hosting-feasibility.md)
- [Data management dev guide](docs/runbooks/data-management-dev-guide.md)
- [Corpus operator guide](docs/runbooks/corpus-operator-guide.md)
- [Feature list](docs/feature-list.md) — F1–F31
- [API contract](docs/api-contract.md)
- [Config spec](docs/config-spec.md)
- [ADR index](docs/adr/README.md)
- [Modal apps](infra/modal/README.md)
- [GitHub Wiki](https://github.com/Math-Data-Justice-Collaborative/vecinita/wiki) — auto-synced public docs subset

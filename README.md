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

## Docs

- [Execution plan](docs/execution-plan.md)
- [API contract](docs/api-contract.md)
- [Config spec](docs/config-spec.md)
- [Modal apps](infra/modal/README.md)

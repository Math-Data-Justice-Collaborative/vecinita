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

Shared packages: `packages/rag`, `packages/ingest`, `packages/embedding-client`, `packages/llm-client`, `packages/tagging`, `packages/shared-schemas`, `packages/eval`, `packages/frontend-i18n`, `packages/frontend-ui`.

UI locale persists in browser `localStorage` key `vecinita.locale` (shared `frontend-i18n` / `frontend-ui`).

**Modal (infra):** embedding, data-management, prod `vecinita-llm`, playground `vecinita-llm-playground`; LoRA fine-tune app planned (`vecinita-llm-finetune`, ADR-053).

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

Commits and PRs use short plain English subjects (optional feature/ADR cites) — see LOCAL_DEV §Commits and PRs.

## Features (through corpus automations + LoRA FT)

| Area | Capabilities |
|------|----------------|
| ChatRAG | Bilingual Q&A, streaming, tag-filtered RAG, corpus browse, en/es UI chrome, citation UX |
| Data Management | URL ingest, job queue, corpus CRUD, LLM auto-tagging, admin dashboard |
| Embeddings | Multilingual 384-d pin (`intfloat/multilingual-e5-small`) |
| Corpus automations | Catch-up for failed/partial/missing embeds; freshness (default 30-day stale, Refresh now) |
| Fine-tune | LoRA/PEFT on pinned Qwen; human approve train; human promote to prod LLM |
| Privacy | Zero personal data (ADR-004), no IP tracking (ADR-016) |

See [docs/feature-list.md](docs/feature-list.md) for the full feature catalog (F1–F77).

## Docs

- [Architecture overview](docs/architecture.md) — service map, environments, deploy pipeline
- [Data flow diagrams](docs/data-flow.md) — Mermaid ingest/query/admin paths
- [Local development](docs/LOCAL_DEV.md) — bootstrap, CI tiers, coverage
- [Hosting migration summary](docs/hosting-migration-summary.md) — infrastructure switch overview
- [OSCAR feasibility (Carlos review)](docs/oscar-hosting-feasibility.md)
- [Data management dev guide](docs/runbooks/data-management-dev-guide.md)
- [Corpus operator guide](docs/runbooks/corpus-operator-guide.md)
- [Feature list](docs/feature-list.md) — F1–F77
- [API contract](docs/api-contract.md)
- [Config spec](docs/config-spec.md)
- [ADR index](docs/adr/README.md)
- [Modal apps](infra/modal/README.md)
- [GitHub Wiki](https://github.com/Math-Data-Justice-Collaborative/vecinita/wiki) — auto-synced public docs subset

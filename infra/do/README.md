# DigitalOcean App Platform specs (ADR-010)

One App spec per deployable (multi-app topology). Region: **nyc** (US-only per ADR-004).

| File | Service | Type |
|------|---------|------|
| `chat-rag-backend.yaml` | ChatRAG API | Web service |
| `internal-write-api.yaml` | Internal write API | Web service |
| `chat-rag-frontend.yaml` | Chat UI | Static site |
| `data-management-frontend.yaml` | Admin UI | Static site |

**Not on DO:** Modal apps — see `scripts/deploy/modal.sh` and [infra/modal/README.md](../modal/README.md).

## Prerequisites

- [doctl](https://docs.digitalocean.com/reference/doctl/) authenticated
- DO Managed Postgres with `pgvector` enabled
- Modal apps deployed; copy embed/LLM URLs into ChatRAG backend secrets
- Secrets matrix: [docs/staging-secrets-matrix.md](../../docs/staging-secrets-matrix.md)

## Create apps (staging)

```bash
doctl apps create --spec infra/do/internal-write-api.yaml
doctl apps create --spec infra/do/chat-rag-backend.yaml
doctl apps create --spec infra/do/chat-rag-frontend.yaml
doctl apps create --spec infra/do/data-management-frontend.yaml
```

Set **SECRET** env vars in the DO dashboard (or `doctl apps update`) before first deploy succeeds.

## Post-deploy

```bash
export VECINITA_STAGING_CHAT_URL=https://<chat-rag-backend>.ondigitalocean.app
export VECINITA_STAGING_WRITE_URL=https://<internal-write-api>.ondigitalocean.app
bash scripts/deploy/staging_smoke.sh
```

Migrations (one-time per database):

```bash
export DATABASE_URL='postgresql://...'
cd apps/database && uv run alembic upgrade head
uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"
```

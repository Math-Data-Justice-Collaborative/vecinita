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

- **API token:** `DIGITALOCEAN_TOKEN` with App Platform read/write
- **CLI (pick one):**
  - [pydo](https://docs.digitalocean.com/reference/pydo/reference/) — `scripts/deploy/do_apps.py` (preferred in CI/agents)
  - [doctl](https://docs.digitalocean.com/reference/doctl/) — equivalent commands below
- DO Managed Postgres with `pgvector` enabled
- Modal apps deployed; copy embed/LLM URLs into ChatRAG backend secrets
- Secrets matrix: [docs/staging-secrets-matrix.md](../../docs/staging-secrets-matrix.md)

## Create apps (staging)

**pydo (recommended):**

```bash
export DIGITALOCEAN_TOKEN='...'
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py create-all
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py list
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls   # staging smoke env hints
```

**doctl (equivalent):**

```bash
doctl apps create --spec infra/do/internal-write-api.yaml
doctl apps create --spec infra/do/chat-rag-backend.yaml
doctl apps create --spec infra/do/chat-rag-frontend.yaml
doctl apps create --spec infra/do/data-management-frontend.yaml
```

Set **SECRET** env vars in the DO dashboard (or sync from shell — see below) before first deploy succeeds.

### Sync environment variables (EV-005 F34 + existing secrets)

Template with placeholders: **[`.env.example`](.env.example)** (copy values into `prod.env`, never commit).

```bash
# Load operator env (prod.env is gitignored)
set -a && source prod.env && set +a
export DIGITALOCEAN_TOKEN='dop_v1_...'

# Push shell env into one app (preserves other encrypted keys on the live spec)
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-secrets --name vecinita-internal-write-api
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-secrets --name vecinita-admin-frontend

# Or all four apps at once
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets

# Or sync every provider at once (Supabase JWKS check + Modal secret + DO apps)
bash scripts/deploy/sync_env.sh --apply
```

After updating **BUILD_TIME** vars (`VITE_*`, `VITE_SUPABASE_*`), trigger a redeploy so the static site rebuilds:

```bash
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-admin-frontend
```

## Post-deploy

Full procedure: [docs/staging-runbook.md](../../docs/staging-runbook.md).

```bash
export VECINITA_STAGING_CHAT_URL=https://<chat-rag-backend>.ondigitalocean.app
export VECINITA_STAGING_WRITE_URL=https://<internal-write-api>.ondigitalocean.app
export VECINITA_STAGING_DATABASE_URL='postgresql://...'   # H2 (or DATABASE_URL)
bash scripts/deploy/staging_smoke.sh
```

Migrations (one-time per database):

```bash
export DATABASE_URL='postgresql://...'
cd apps/database && uv run alembic upgrade head
uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"
```

## Corpus protection

Staging corpus is on **DO Managed Postgres** (`DATABASE_URL` on chat-rag-backend and
internal-write-api). Test helpers refuse `TRUNCATE` on `.ondigitalocean.com` hosts — see
[docs/staging-runbook.md](../../docs/staging-runbook.md) §Corpus protection.

Verify daily backups (recovery after accidental wipe):

```bash
set -a && source prod.env && set +a
bash scripts/infra/do_verify_staging_backups.sh
```

# Staging DigitalOcean App Platform specs (F83 / ADR-054)

Distinct non-prod stack. App names are shortened to stay within DO’s **32-character**
`name` limit.

| Spec file | App name | Role |
|-----------|----------|------|
| `internal-write-api.yaml` | `vecinita-staging-write-api` | Write API + `DATABASE_URL` |
| `chat-rag-backend.yaml` | `vecinita-staging-chat-api` | ChatRAG API |
| `chat-rag-frontend.yaml` | `vecinita-staging-chat-fe` | Chat UI |
| `data-management-frontend.yaml` | `vecinita-staging-admin-fe` | Admin UI |

```bash
export DIGITALOCEAN_TOKEN='...'
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py create-all --env staging
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --env staging --frontend
```

Modal workspace for this env: **`vecinita`** with Environment **`staging`**
(`MODAL_ENVIRONMENT=staging`; web suffix → URL prefix `vecinita-staging--`).
Secrets: [docs/staging-secrets-matrix.md](../../docs/staging-secrets-matrix.md) §Dual environment.

Prod specs remain under `infra/do/*.yaml` (legacy names; treat as **prod** per ADR-054).

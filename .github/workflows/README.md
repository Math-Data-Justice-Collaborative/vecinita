# Workflows

## Cross-Repo Orchestration

- `multi-repo-release-orchestrator.yml`: Parent workflow that dispatches independent service pipelines across mapped repositories.
- `reusable-dispatch-repo-workflow.yml`: Reusable workflow invoked by the orchestrator to dispatch and optionally wait for a downstream workflow.

## Local Repository Workflows

- `quality-gate.yml`: Root quality checks.
- `test.yml`: Core test execution.
- `render-deploy.yml`: Quality gates + staging/production validation notices. Deploys are driven by blueprint **`autoDeployTrigger: checksPass`** (not deploy hooks).
- `render-post-deploy.yml`: Runs after **Render Deploy** completes — waits for Render services to go live via the API (avoids `checksPass` deadlock). See `docs/deployment/RENDER_STAGING_PROD_CICD.md`.
- `modal-deploy.yml`: Root Modal deployment flow for this repository surfaces.

### Sync GitHub Actions secrets from local `.env` (GitHub CLI)

Prerequisite: [`gh auth login`](https://cli.github.com/manual/gh_auth_login) with permission to set repository secrets.

From the **repository root**, merge your gitignored env files (same keys as [`.env.local.example`](../../.env.local.example)) and **dry-run** first:

```bash
python3 scripts/env_sync.py gh --preset github-actions --file .env --file .env.local --dry-run
```

Apply (writes `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `DATABASE_URL`, and `MODAL_API_PROFILE` when present, resolving `MODAL_API_TOKEN_*` / `MODAL_AUTH_*` and `DB_URL` like the workflows):

```bash
python3 scripts/env_sync.py gh --preset github-actions --file .env --file .env.local --yes
```

Optional: `--repo OWNER/REPO`, `--environment staging|production` for [environment-scoped secrets](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment#environment-secrets). See [`docs/deployment/RENDER_STAGING_PROD_CICD.md`](../../docs/deployment/RENDER_STAGING_PROD_CICD.md) for `RENDER_*` sync with the same tool.

### Modal GitHub Actions secrets

Workflows resolve credentials in this order (first non-empty wins):

1. `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` — canonical (matches Render `MODAL_*` naming).
2. `MODAL_API_TOKEN_ID` / `MODAL_API_TOKEN_SECRET` — same tokens under names used in local `.env` templates.
3. `MODAL_AUTH_KEY` / `MODAL_AUTH_SECRET` — legacy names still supported in submodule deploy workflows.

Optional: `MODAL_API_PROFILE` secret or `MODAL_API_PROFILE` variable for `MODAL_PROFILE` (default `vecinita`). Scraper Modal deploy jobs also accept `DATABASE_URL` or `DB_URL` for deploy-time env if your Modal apps read them from the runner environment.
- `microservices-contracts.yml`: Local microservices contract stack verification.

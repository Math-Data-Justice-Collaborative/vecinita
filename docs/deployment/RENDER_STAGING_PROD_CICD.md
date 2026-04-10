# Render Staging and Production CI/CD

## Goal

This repo uses **Render blueprint `autoDeployTrigger: checksPass`** (“After CI Checks Pass”) as the **primary** deploy driver, aligned with [Render: integrating with CI](https://render.com/docs/deploys#integrating-with-ci).

1. Pull request to `main` runs backend and frontend checks in `.github/workflows/render-deploy.yml` (path-filtered) plus repo-wide workflows such as **Tests**.
2. When **all** GitHub checks pass, **Render** starts deploys for services linked to the relevant branch — this workflow **does not** POST deploy hooks (avoids **double deploys**).
3. Staging smoke checks run against staging URLs (optional if URLs unset).
4. Merge to `main`: same model for production. When **Render Deploy** completes, **Render Post-Deploy** (`.github/workflows/render-post-deploy.yml`) runs: **deploy-wait** polls Render until services are live, then **production HTTP smoke** and **post-deploy-smoke** (pytest live) run in parallel.

Pipeline files: `.github/workflows/render-deploy.yml`, `.github/workflows/render-post-deploy.yml`

### Why two workflows?

Render **checksPass** waits until **all** GitHub checks for the commit succeed. A job that waits for Render to finish **inside the same workflow** would block those checks and prevent Render from ever starting. Post-deploy wait and smoke therefore run in **`workflow_run`** after **Render Deploy** completes ([GitHub: `workflow_run`](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)).

## Deploy trigger model (Option A — Render-led)

| Mechanism | Role |
|-----------|------|
| **`checksPass` in `render.yaml` / `render.staging.yaml`** | Render deploys only after GitHub checks complete successfully (`success`, `neutral`, or `skipped` per Render docs). |
| **Render Deploy workflow** | Quality gates, optional gateway Docker runtime validation. **No deploy hooks**, **no** deploy-wait (deadlock risk — see above). |
| **Render Post-Deploy workflow** | **`workflow_run`** after Render Deploy: deploy-wait, production HTTP smoke, live pytest smoke. |
| **Legacy deploy hooks** | Not used by the current workflow. Old secret names may remain in the repo unused. |

Render **will not** deploy if **zero** checks are reported for a commit; keep at least one workflow (e.g. **Tests** on `main`) always reporting checks. Use `[skip render]` in commit messages to skip auto-deploy when needed ([Render: skipping an auto-deploy](https://render.com/docs/deploys#skipping-an-auto-deploy)).

## Render Blueprints

- Production blueprint: `render.yaml`
- Staging blueprint: `render.staging.yaml`

Blueprints use `autoDeployTrigger: checksPass`. Sync them to the Render dashboard so **Settings → Auto-Deploy** matches ([Blueprint spec: `autoDeployTrigger`](https://render.com/docs/blueprint-spec)).

Optional: per-service [build filters](https://render.com/docs/monorepo-support#setting-build-filters) to limit deploys to relevant path changes.

Both staging and production gateway services should use the dedicated Docker image path defined by `backend/Dockerfile.gateway`.

## Required GitHub Environments

Create these GitHub environments in repository settings:

- `staging`
- `production`

Optional but recommended:

- Add required reviewers for `production`.
- Add wait timers for `production`.

## GitHub Secrets and Variables (smoke + wait)

### Staging smoke URLs

Secrets or Variables:

- `RENDER_STAGING_AGENT_URL`
- `RENDER_STAGING_GATEWAY_URL`
- `RENDER_STAGING_FRONTEND_URL`

Optional: `RENDER_STAGING_DATA_MANAGEMENT_*` for data-management smoke steps.

### Production smoke URLs

Preferred secrets or Variables:

- `RENDER_PROD_AGENT_URL`
- `RENDER_PROD_GATEWAY_URL`
- `RENDER_PROD_FRONTEND_URL`

Fallback names: `RENDER_AGENT_URL`, `RENDER_GATEWAY_URL`, `RENDER_FRONTEND_URL`.

### Wait for deploy + runtime validation

- `RENDER_API_KEY` — used by `deploy-wait` and optional `validate_render_runtime.py`
- `RENDER_AGENT_SERVICE_ID`, `RENDER_GATEWAY_SERVICE_ID`, `RENDER_FRONTEND_SERVICE_ID`
- `RENDER_STAGING_GATEWAY_SERVICE_ID` — staging gateway Docker validation
- Optional: `RENDER_DATA_MANAGEMENT_FRONTEND_SERVICE_ID`, `RENDER_DATA_MANAGEMENT_API_SERVICE_ID`

### Legacy deploy hooks (unused by current workflow)

The workflow no longer reads `RENDER_*_DEPLOY_HOOK_*` secrets. You may remove them from GitHub or keep them for manual/external automation.

## Workflow Behavior

Trigger conditions:

- PR to `main` (path filter): backend/frontend quality, staging **validation** job (no hooks), staging smoke
- Push to `main` (path filter): quality, production **validation** job (no hooks), **deploy-wait**, **smoke-production**, **post-deploy-smoke**
- Manual: `workflow_dispatch`

**Production job order:** In **Render Deploy**: `deploy-production` (validation + notices) completes → Render can start deploys. In **Render Post-Deploy**: `deploy-wait` (matrix) → `smoke-production` and `post-deploy-smoke` in parallel.

Checks that gate Render (must exist on the commit for `checksPass`):

- This workflow’s backend + frontend jobs when path filters match
- Other workflows on `main` (e.g. **Tests**, **Quality Gate**) with no path filter — ensures non-zero checks

## Frontend Notes

Frontend and backend deploy together from Render’s perspective when each service’s linked branch receives a passing commit; no hook synchronization is required in GitHub Actions.

## Manual Rollout

1. Create or update Render services from `render.staging.yaml` and `render.yaml`; apply blueprints so **Auto-Deploy** is **After CI Checks Pass**.
2. Configure GitHub environments, smoke URLs (secrets or variables), and `RENDER_API_KEY` + service IDs for deploy wait.
3. Open a PR to `main` and verify checks and staging smoke (if URLs are set).
4. Ensure the production gateway service uses Docker runtime and `backend/Dockerfile.gateway`.
5. Merge to `main` and verify Render deploys, then **Render Post-Deploy** (deploy-wait + smoke jobs).

## Local sync: `gh` CLI and Render API (`scripts/env_sync.py`)

Real values live in **gitignored** files (for example `.env`, `.env.prod.render`, `.env.staging.render`, `.env.dev`, `.env.local` copied from `.env.local.example`). Never commit them.

Prerequisites:

- [GitHub CLI](https://docs.github.com/en/github-cli/github-cli/about-github-cli): `gh auth login`
- [Render CLI](https://render.com/docs/cli) (optional, for `render-list`): `render login` then `render whoami -o json`
- Render REST: set `RENDER_API_KEY` in your shell (Dashboard → Account → API keys)

### GitHub Actions secrets

Default: only keys starting with `RENDER_` (typical CI secrets). Always dry-run first:

```bash
python3 scripts/env_sync.py gh --file .env --file .env.prod.render --prefix RENDER_ --dry-run
python3 scripts/env_sync.py gh --file .env --file .env.prod.render --prefix RENDER_ --yes
```

Environment-scoped secrets (staging / production):

```bash
python3 scripts/env_sync.py gh --file .env --prefix RENDER_ --environment staging --dry-run
python3 scripts/env_sync.py gh --file .env --prefix RENDER_ --environment staging --yes
```

Exact key names (repeat `--key`):

```bash
python3 scripts/env_sync.py gh --file .env --key RENDER_API_KEY --key RENDER_GATEWAY_SERVICE_ID --dry-run
```

See [Using secrets in workflows](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

### Render service environment variables

The Render CLI in this repo does not expose bulk env upload; the script uses the [Render API](https://render.com/docs/api) `PATCH /v1/services/{serviceId}` with an `envVars` array (same pattern as `scripts/apply-render-env-api.sh`). Confirm merge behavior on a **staging** service before production.

List service IDs:

```bash
python3 scripts/env_sync.py render-list
# or: render services -o json
```

Push keys from a dotenv file (all non-empty keys in file by default):

```bash
export RENDER_API_KEY=...
python3 scripts/env_sync.py render-api --file .env.prod.render --service-id srv-xxxxxxxx --dry-run
python3 scripts/env_sync.py render-api --file .env.prod.render --service-id srv-xxxxxxxx --yes
```

Limit to a prefix or explicit keys:

```bash
python3 scripts/env_sync.py render-api --file .env.staging.render --service-id srv-xxx --prefix MODAL_ --yes
```

## Render MCP Env Sync Checklist

Use Render MCP **or** `scripts/env_sync.py render-api` for Render service environment variable updates.
Do not store long-lived Render API keys in the repo; export `RENDER_API_KEY` only in your local shell or a secrets manager.

### Boundary: What goes where

- Render (dashboard, MCP, or `env_sync.py render-api`): runtime env vars for services (content of `.env.prod.render` / `.env.staging.render`-style groups).
- GitHub (`env_sync.py gh` or dashboard): Actions secrets and variables such as `RENDER_*` URLs, `RENDER_API_KEY`, service IDs for CI wait/smoke.

### Staging first, production second

1. Update staging service env vars via Render MCP (`gateway`, `agent`, `frontend`).
2. Verify staging health + documents smoke endpoints.
3. Promote the same key set to production via Render MCP.
4. Verify production health + documents smoke endpoints.

### Minimum runtime vars to verify for Documents tab path

- Frontend service:
	- `VITE_GATEWAY_URL`
	- `VITE_BACKEND_URL`
- Gateway service:
	- `ALLOWED_ORIGINS`
	- `ALLOWED_ORIGIN_REGEX`
	- `AGENT_SERVICE_URL` (service binding)
	- `DATABASE_URL` (database binding)
- Agent service:
	- `DATABASE_URL` (database binding)

### GitHub configuration for smoke and deploy wait

- Staging smoke: `RENDER_STAGING_AGENT_URL`, `RENDER_STAGING_GATEWAY_URL`, `RENDER_STAGING_FRONTEND_URL` (secrets or variables)
- Production smoke: `RENDER_PROD_*` or legacy `RENDER_*` URLs (secrets or variables)
- Deploy wait: `RENDER_API_KEY` and per-service `RENDER_*_SERVICE_ID` secrets

### Production gateway Render settings

For the production gateway service:

1. Keep the runtime set to Docker.
2. Point the service at `backend/Dockerfile.gateway`.
3. Use **After CI Checks Pass** with blueprint `checksPass`; no deploy hook required from GitHub Actions.

# Render Staging and Production CI/CD

## Goal

This repo uses **Render blueprint `autoDeployTrigger: checksPass`** (“After CI Checks Pass”) as the **primary** deploy driver, aligned with [Render: integrating with CI](https://render.com/docs/deploys#integrating-with-ci).

1. Pull request to `main` runs backend and frontend checks in `.github/workflows/render-deploy.yml` (path-filtered) plus repo-wide workflows such as **Tests**.
2. When **all** GitHub checks pass, **Render** starts deploys for services linked to the relevant branch — this workflow **does not** POST deploy hooks (avoids **double deploys**).
3. Staging and production deploys are **Render-driven** only (`autoDeployTrigger: checksPass` in `render.staging.yaml` / `render.yaml`). GitHub Actions does **not** curl staging or production URLs for smoke tests.
4. Merge to `main`: same model for production. When **Render Deploy** completes, **Render Post-Deploy** (`.github/workflows/render-post-deploy.yml`) may run **deploy-wait** only (optional Render API poll until services report live). Use Render health checks, dashboard logs, or local [`Makefile`](../../Makefile) / manual probes for live verification.

Pipeline files: `.github/workflows/render-deploy.yml`, `.github/workflows/render-post-deploy.yml`

### Why two workflows?

Render **checksPass** waits until **all** GitHub checks for the commit succeed. A job that waits for Render to finish **inside the same workflow** would block those checks and prevent Render from ever starting. Optional **deploy-wait** therefore runs in **`workflow_run`** after **Render Deploy** completes ([GitHub: `workflow_run`](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)).

## Deploy trigger model (Option A — Render-led)

| Mechanism | Role |
|-----------|------|
| **`checksPass` in `render.yaml` / `render.staging.yaml`** | Render deploys only after GitHub checks complete successfully (`success`, `neutral`, or `skipped` per Render docs). |
| **Render Deploy workflow** | Quality gates, optional gateway Docker runtime validation. **No deploy hooks**, **no** deploy-wait (deadlock risk — see above). |
| **Render Post-Deploy workflow** | **`workflow_run`** after Render Deploy: optional **deploy-wait** only (no live URL smoke in CI). |
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

## GitHub Secrets and Variables (deploy wait + validation)

Staging and production **service URLs** are not required for GitHub Actions smoke jobs (removed). Keep them in GitHub or Render only if you use them for scripts, MCP, or manual checks.

### Wait for deploy + runtime validation

- `RENDER_API_KEY` — used by `deploy-wait` and optional `validate_render_runtime.py`
- `RENDER_AGENT_SERVICE_ID`, `RENDER_GATEWAY_SERVICE_ID`, `RENDER_FRONTEND_SERVICE_ID`
- `RENDER_STAGING_GATEWAY_SERVICE_ID` — staging gateway Docker validation
- Optional: `RENDER_DATA_MANAGEMENT_FRONTEND_SERVICE_ID`, `RENDER_DATA_MANAGEMENT_API_SERVICE_ID`

### Legacy deploy hooks (unused by current workflow)

The workflow no longer reads `RENDER_*_DEPLOY_HOOK_*` secrets. You may remove them from GitHub or keep them for manual/external automation.

## Workflow Behavior

Trigger conditions:

- PR to `main` (path filter): backend/frontend quality, staging **validation** job (no hooks)
- Push to `main` (path filter): quality, production **validation** job (no hooks); **Render Post-Deploy** runs **deploy-wait** only (after **Render Deploy** completes)
- Manual: `workflow_dispatch`

**Production job order:** In **Render Deploy**: `deploy-production` (validation + notices) completes → Render can start deploys (`checksPass`). In **Render Post-Deploy**: `deploy-wait` (matrix) only.

Checks that gate Render (must exist on the commit for `checksPass`):

- This workflow’s backend + frontend jobs when path filters match
- Other workflows on `main` (e.g. **Tests**, **Quality Gate**) with no path filter — ensures non-zero checks

## Frontend Notes

Frontend and backend deploy together from Render’s perspective when each service’s linked branch receives a passing commit; no hook synchronization is required in GitHub Actions.

## Manual Rollout

1. Create or update Render services from `render.staging.yaml` and `render.yaml`; apply blueprints so **Auto-Deploy** is **After CI Checks Pass**.
2. **Credentials:** Populate the Render Environment Group (or each service) using the **same keys** as [`.env.prod.render.example`](../../.env.prod.render.example) / [`.env.staging.render.example`](../../.env.staging.render.example) — copy values from your gitignored `.env` / `.env.prod.render` / `.env.staging.render`, not ad-hoc names. See [RENDER_SHARED_ENV_CONTRACT.md](RENDER_SHARED_ENV_CONTRACT.md) (*Credentials parity with local `.env`*).
3. Configure GitHub environments and `RENDER_API_KEY` + service IDs if you use **deploy-wait** in **Render Post-Deploy**.
4. Open a PR to `main` and verify checks; confirm staging services deploy on Render after checks pass.
5. Ensure the production gateway service uses Docker runtime and `backend/Dockerfile.gateway`.
6. Merge to `main` and verify Render deploys; optionally confirm **Render Post-Deploy** **deploy-wait** if secrets are set.

## Local sync: `gh` CLI and Render API (`scripts/env_sync.py`)

Real values live in **gitignored** files (for example `.env`, `.env.prod.render`, `.env.staging.render`, `.env.dev`, `.env.local` copied from `.env.local.example`). Never commit them.

Prerequisites:

- [GitHub CLI](https://docs.github.com/en/github-cli/github-cli/about-github-cli): `gh auth login`
- [Render CLI](https://render.com/docs/cli) (optional, for `render-list`): `render login` then `render whoami -o json`
- Render REST: set `RENDER_API_KEY` in your shell (Dashboard → Account → API keys)

### GitHub Actions secrets

**Modal / DB credentials for workflows** (from your local `.env` / `.env.local`, never committed): use `scripts/env_sync.py` with the `github-actions` preset so GitHub receives the same names the workflows read (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `DATABASE_URL`, `MODAL_API_PROFILE`). Requires [`gh auth login`](https://cli.github.com/manual/gh_auth_login).

```bash
python3 scripts/env_sync.py gh --preset github-actions --file .env --file .env.local --dry-run
python3 scripts/env_sync.py gh --preset github-actions --file .env --file .env.local --yes
```

**Render / CI helpers** — default: only keys starting with `RENDER_` (typical CI secrets). Always dry-run first:

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

The official Render CLI does not expose bulk env upload; `scripts/env_sync.py` uses the [Render API](https://render.com/docs/api) `PATCH /v1/services/{serviceId}` with an `envVars` array. Use **`render login`** plus **`--service-name`** so the script can resolve a service id from `render services -o json`, or pass **`--service-id`** explicitly. **`RENDER_API_KEY`** may be set in the shell or inside a merged **`--file`** (for example a gitignored `.env`). Confirm merge behavior on a **staging** service before production.

List service IDs:

```bash
python3 scripts/env_sync.py render-list
# or: render services -o json
```

Push Modal tokens + `MODAL_FUNCTION_INVOCATION` from `.env` to the gateway (dry-run first):

```bash
render login
python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  --file .env \
  --service-name vecinita-gateway \
  --dry-run
python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  --file .env \
  --service-name vecinita-gateway \
  --yes
```

Push keys from a dotenv file (all non-empty keys in file by default):

```bash
export RENDER_API_KEY=...
python3 scripts/env_sync.py render-api --file .env.prod.render --service-id srv-xxxxxxxx --dry-run
python3 scripts/env_sync.py render-api --file .env.prod.render --service-id srv-xxxxxxxx --yes
```

**Scraper API keys (`SCRAPER_API_KEYS`):** use the Render CLI for service-id discovery plus the same REST sync, and Modal CLI for `vecinita-scraper-env`:

```bash
render login
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --dry-run
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --yes

modal secret create vecinita-scraper-env --from-dotenv ~/path/to/scraper-modal.env --force
# or: ./scripts/sync_scraper_auth_render_modal.sh modal --from-dotenv ~/path/to/scraper-modal.env --force
```

Limit to a prefix or explicit keys:

```bash
python3 scripts/env_sync.py render-api --file .env.staging.render --service-id srv-xxx --prefix MODAL_ --yes
```

## Render MCP Env Sync Checklist

Use Render MCP **or** `scripts/env_sync.py render-api` for Render service environment variable updates.
Keep long-lived `RENDER_API_KEY` out of committed files; a **gitignored** `.env` is fine for local sync.

### Boundary: What goes where

- Render (dashboard, MCP, or `env_sync.py render-api`): runtime env vars for services (content of `.env.prod.render` / `.env.staging.render`-style groups).
- GitHub (`env_sync.py gh` or dashboard): Actions secrets and variables such as optional `RENDER_*` URLs (for local tooling), `RENDER_API_KEY`, service IDs for **deploy-wait**.

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

### GitHub configuration for deploy wait

- Deploy wait: `RENDER_API_KEY` and per-service `RENDER_*_SERVICE_ID` secrets (optional; skips if unset)

### Production gateway Render settings

For the production gateway service:

1. Keep the runtime set to Docker.
2. Point the service at `backend/Dockerfile.gateway`.
3. Use **After CI Checks Pass** with blueprint `checksPass`; no deploy hook required from GitHub Actions.

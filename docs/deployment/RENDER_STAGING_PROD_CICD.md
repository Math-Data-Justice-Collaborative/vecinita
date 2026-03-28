# Render Staging and Production CI/CD

## Goal

This repo now supports a staged promotion flow:

1. Pull request to `main` runs backend and frontend checks.
2. If checks pass, GitHub Actions triggers **staging** Render deploy hooks.
3. Staging smoke checks run against staging URLs.
4. Merge to `main` triggers **production** deploy hooks.
5. Production smoke checks run against production URLs.

Pipeline file: `.github/workflows/render-deploy.yml`

## Render Blueprints

- Production blueprint: `render.yaml`
- Staging blueprint: `render.staging.yaml`

Both are configured with `autoDeployTrigger: off` so deployments are controlled by CI/CD deploy hooks.

## Required GitHub Environments

Create these GitHub environments in repository settings:

- `staging`
- `production`

Optional but recommended:

- Add required reviewers for `production`.
- Add wait timers for `production`.

## Required GitHub Secrets

### Staging deploy hooks

- `RENDER_STAGING_DEPLOY_HOOK_AGENT`
- `RENDER_STAGING_DEPLOY_HOOK_EMBEDDING`
- `RENDER_STAGING_DEPLOY_HOOK_FRONTEND`
- `RENDER_STAGING_DEPLOY_HOOK_SCRAPER` (optional)

### Staging smoke URLs

- `RENDER_STAGING_AGENT_URL`
- `RENDER_STAGING_EMBEDDING_URL`
- `RENDER_STAGING_FRONTEND_URL`

### Production deploy hooks

Preferred names:

- `RENDER_PROD_DEPLOY_HOOK_AGENT`
- `RENDER_PROD_DEPLOY_HOOK_EMBEDDING`
- `RENDER_PROD_DEPLOY_HOOK_FRONTEND`
- `RENDER_PROD_DEPLOY_HOOK_SCRAPER` (optional)

Backward-compatible names also supported by workflow:

- `RENDER_DEPLOY_HOOK_AGENT`
- `RENDER_DEPLOY_HOOK_EMBEDDING`
- `RENDER_DEPLOY_HOOK_FRONTEND`
- `RENDER_DEPLOY_HOOK_SCRAPER`
- `RENDER_VECINITA_AGENT_DEPLOY_HOOK`
- `RENDER_VECINITA_EMBEDDING_DEPLOY_HOOK`
- `RENDER_VECINITA_FRONTEND_DEPLOY_HOOK`

### Production smoke URLs

Preferred names:

- `RENDER_PROD_AGENT_URL`
- `RENDER_PROD_EMBEDDING_URL`
- `RENDER_PROD_FRONTEND_URL`

Backward-compatible names:

- `RENDER_AGENT_URL`
- `RENDER_EMBEDDING_URL`
- `RENDER_FRONTEND_URL`

## Workflow Behavior

Trigger conditions:

- PR to `main`: checks + staging deploy + staging smoke
- Push to `main`: checks + production deploy + production smoke
- Manual: `workflow_dispatch`

Checks included in deployment gate:

- Backend: Ruff, Black check, mypy, backend unit tests
- Frontend: ESLint, Prettier check, TypeScript typecheck, Vitest coverage run

## Frontend Notes

Frontend deploy is part of both staging and production hook triggers in the same workflow, so frontend promotion is synchronized with backend promotion.

## Manual Rollout

1. Create or update Render services from `render.staging.yaml` and `render.yaml`.
2. Add all required secrets and environment protections in GitHub.
3. Open a PR to `main` and verify staging deployment and smoke pass.
4. Merge PR to `main` and verify production deployment and smoke pass.

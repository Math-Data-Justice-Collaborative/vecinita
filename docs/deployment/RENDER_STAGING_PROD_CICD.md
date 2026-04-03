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
- `RENDER_STAGING_DEPLOY_HOOK_GATEWAY`
- `RENDER_STAGING_DEPLOY_HOOK_FRONTEND`

### Staging smoke URLs

- `RENDER_STAGING_AGENT_URL`
- `RENDER_STAGING_GATEWAY_URL`
- `RENDER_STAGING_FRONTEND_URL`

### Production deploy hooks

Preferred names:

- `RENDER_PROD_DEPLOY_HOOK_AGENT`
- `RENDER_PROD_DEPLOY_HOOK_GATEWAY`
- `RENDER_PROD_DEPLOY_HOOK_FRONTEND`

Backward-compatible names also supported by workflow:

- `RENDER_DEPLOY_HOOK_AGENT`
- `RENDER_DEPLOY_HOOK_GATEWAY`
- `RENDER_DEPLOY_HOOK_FRONTEND`
- `RENDER_VECINITA_GATEWAY_DEPLOY_HOOK`
- `RENDER_VECINITA_AGENT_DEPLOY_HOOK`
- `RENDER_VECINITA_FRONTEND_DEPLOY_HOOK`

### Production smoke URLs

Preferred names:

- `RENDER_PROD_AGENT_URL`
- `RENDER_PROD_GATEWAY_URL`
- `RENDER_PROD_FRONTEND_URL`

Backward-compatible names:

- `RENDER_AGENT_URL`
- `RENDER_GATEWAY_URL`
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

## Render MCP Env Sync Checklist

Use Render MCP for Render service environment variable updates only.
Do not use Render MCP for GitHub Actions secrets.

### Boundary: What goes where

- Render MCP updates: service env vars used at runtime by Render services.
- GitHub secrets updates: deploy hooks and smoke URLs consumed by `.github/workflows/render-deploy.yml`.

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

### GitHub secrets required for the gateway deployment path

- Staging deploy hooks:
	- `RENDER_STAGING_DEPLOY_HOOK_AGENT`
	- `RENDER_STAGING_DEPLOY_HOOK_GATEWAY`
	- `RENDER_STAGING_DEPLOY_HOOK_FRONTEND`
- Staging smoke URLs:
	- `RENDER_STAGING_AGENT_URL`
	- `RENDER_STAGING_GATEWAY_URL`
	- `RENDER_STAGING_FRONTEND_URL`
- Production deploy hooks:
	- `RENDER_PROD_DEPLOY_HOOK_AGENT`
	- `RENDER_PROD_DEPLOY_HOOK_GATEWAY`
	- `RENDER_PROD_DEPLOY_HOOK_FRONTEND`
- Production smoke URLs:
	- `RENDER_PROD_AGENT_URL` (or fallback `RENDER_AGENT_URL`)
	- `RENDER_PROD_GATEWAY_URL` (or fallback `RENDER_GATEWAY_URL`)
	- `RENDER_PROD_FRONTEND_URL` (or fallback `RENDER_FRONTEND_URL`)

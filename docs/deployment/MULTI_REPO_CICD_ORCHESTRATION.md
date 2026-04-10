# Multi-Repo CI/CD Orchestration

This document defines the independent pipeline ownership model and the top-level orchestrator used from this repository.

## Canonical Control Plane

This repository is the **single release control plane** for cross-repo deployments.

- Canonical service mapping lives in `.github/release/release-manifest.json`.
- `.github/workflows/multi-repo-release-orchestrator.yml` reads that manifest and dispatches child workflows.
- Service repositories remain owners of their own test + deploy workflows.

This provides one place to manage "everything" without violating the required multi-repo ownership model.

## Deployment Ownership Mapping

| Service | Repository | Deployment Target | Region/Network Policy |
|---|---|---|---|
| Chat Frontend | joseph-c-mcguire/Vecinitafrontend | Render Frontend | Virginia |
| Data Management Frontend | Math-Data-Justice-Collaborative/vecinita-data-management-frontend | Render Static Site | Virginia |
| Data Management API (proxy) | Math-Data-Justice-Collaborative/vecinita-modal-proxy | Render Web Service (CORS-restricted) | Virginia |
| Data Management Monorepo CI | Math-Data-Justice-Collaborative/vecinita-data-management | CI only (layout + submodule validation) | N/A |
| Scraper | Math-Data-Justice-Collaborative/vecinita-scraper | Modal Deploy | N/A |
| Embedding Modal | Math-Data-Justice-Collaborative/vecinita-embedding | Modal Deploy | N/A |
| Model Modal | Math-Data-Justice-Collaborative/vecinita-model | Modal Deploy | N/A |

> **Architecture note — why the data-management API is a public web service, not a private service:**
> The data-management frontend is a static site (CDN-served HTML/JS). The browser makes API calls
> directly to the data-management API. Render private services have no public URL; browsers cannot
> reach them. Therefore the API must be a public Render web service with CORS restricted to the
> frontend origin. The proxy (`vecinita-modal-proxy`) enforces this via `CORS_ORIGINS`.

> **Orchestrator mapping — data-management-api job:**
> The `deploy_data_management_api` orchestrator input dispatches `vecinita-data-management/deploy.yml`,
> which triggers the Render deploy hook for the `vecinita-modal-proxy` service (set `RENDER_DEPLOY_HOOK_URL`
> in `vecinita-data-management` Actions secrets to the proxy's Render deploy hook URL).
> The proxy owns its own `render.yaml` and `Dockerfile`.

## Workflow Design

This repo provides:

1. Independent service pipelines in each service repository.
2. One parent orchestrator that dispatches those pipelines.

Files:

- .github/workflows/reusable-dispatch-repo-workflow.yml
- .github/workflows/multi-repo-release-orchestrator.yml
- .github/release/release-manifest.json

The parent orchestrator dispatches workflow_dispatch events into each service repo and optionally waits for completion.

## Why Not One Literal Render File For All Repos

Render blueprints are repository-scoped, and this architecture requires each service repository to own its own deployment workflow. A single literal Render blueprint that deploys every repository is therefore not feasible without collapsing all services into one repository.

The manifest-driven orchestrator is the supported "single place" solution.

## Required Secrets

Set the following secret in this repository:

- CROSS_REPO_WORKFLOW_TOKEN

Token requirements:

- Must have permission to trigger and read workflow runs in all mapped repositories.
- Fine-grained PAT is recommended with Actions read/write on each target repository.

## Triggering the Parent Orchestrator

Manual run:

1. Open Actions.
2. Select Multi-Repo Release Orchestrator.
3. Choose target_ref and which services to deploy.
4. Run workflow.

You can also override workflow filenames per repo from workflow_dispatch inputs.

## Data Management Isolation Policy

Data management architecture policy:

- Data Management Frontend (static site) calls the Data Management API proxy directly from the browser.
- The API proxy (`vecinita-modal-proxy`) is a Render **web service** (public) with CORS restricted to
  the frontend origin. It is NOT a Render private service — private services have no public URL and
  browsers cannot reach them.
- The proxy routes authenticated requests to Modal-deployed backends (scraper, embedding, model).
- Modal Routing traffic does not go through the chat gateway (`vecinita-gateway`).

CORS policy guidance for the data-management API proxy:

- Set `CORS_ORIGINS` to the data-management frontend's Render URL (e.g. `https://vecinita-data-management-frontend.onrender.com`).
- Do not use `*` (wildcard) in production.
- The proxy also supports `PROXY_AUTH_TOKEN` for X-Proxy-Token header authentication.

## Region Policy (Virginia)

Render services in this mapping should use Virginia region:

- chat frontend
- data-management frontend
- data-management API
- modal routing

Because Render deployment is controlled by each service repo, enforce region in those repos' render manifests or service settings.
The parent orchestrator logs expected region and fails only on downstream workflow failures.

## Chat Frontend Naming Realignment

Current repository name in mapping is joseph-c-mcguire/Vecinitafrontend.
Desired naming is chat-focused (for example vecinita-chat-frontend).

Recommended migration sequence:

1. Rename repository in GitHub settings.
2. Update deploy hooks and repository references in all repos.
3. Update target_repo value in the parent orchestrator workflow.
4. Validate with one orchestrator run.

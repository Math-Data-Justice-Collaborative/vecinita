# Multi-Repo CI/CD Orchestration

This document defines the independent pipeline ownership model and the top-level orchestrator used from this repository.

## Deployment Ownership Mapping

| Service | Repository | Deployment Target | Region/Network Policy |
|---|---|---|---|
| Chat Frontend | joseph-c-mcguire/Vecinitafrontend | Render Frontend | Virginia |
| Data Management Frontend | Math-Data-Justice-Collaborative/vecinita-data-management-frontend | Render Frontend | Virginia |
| Data Management API | Math-Data-Justice-Collaborative/vecinita-data-management | Render Private Service | Virginia, private-only |
| Modal Proxy | Math-Data-Justice-Collaborative/vecinita-modal-proxy | Render Private Service | Virginia, private-only |
| Scraper | Math-Data-Justice-Collaborative/vecinita-scraper | Modal Deploy | N/A |
| Embedding Modal | Math-Data-Justice-Collaborative/vecinita-embedding | Modal Deploy | N/A |
| Model Modal | Math-Data-Justice-Collaborative/vecinita-model | Modal Deploy | N/A |

## Workflow Design

This repo provides:

1. Independent service pipelines in each service repository.
2. One parent orchestrator that dispatches those pipelines.

Files:

- .github/workflows/reusable-dispatch-repo-workflow.yml
- .github/workflows/multi-repo-release-orchestrator.yml

The parent orchestrator dispatches workflow_dispatch events into each service repo and optionally waits for completion.

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

Data Management architecture policy:

- Data Management Frontend talks directly to Data Management API.
- Data Management API is Render private service and should not be publicly exposed.
- Modal Proxy is private and consumed by agent backend and data-management API.

CORS policy guidance for Data Management API:

- Allow only the data-management frontend origin(s).
- Deny wildcard origins in production.

## Region Policy (Virginia)

Render services in this mapping should use Virginia region:

- chat frontend
- data-management frontend
- data-management API
- modal proxy

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

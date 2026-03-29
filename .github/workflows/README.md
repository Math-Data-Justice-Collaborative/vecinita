# Workflows

## Cross-Repo Orchestration

- `multi-repo-release-orchestrator.yml`: Parent workflow that dispatches independent service pipelines across mapped repositories.
- `reusable-dispatch-repo-workflow.yml`: Reusable workflow invoked by the orchestrator to dispatch and optionally wait for a downstream workflow.

## Local Repository Workflows

- `quality-gate.yml`: Root quality checks.
- `test.yml`: Core test execution.
- `render-deploy.yml`: Root Render deployment flow for this repository surfaces.
- `modal-deploy.yml`: Root Modal deployment flow for this repository surfaces.
- `microservices-contracts.yml`: Local microservices contract stack verification.

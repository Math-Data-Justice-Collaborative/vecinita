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
- `microservices-contracts.yml`: Local microservices contract stack verification.

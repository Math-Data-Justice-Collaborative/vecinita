---
name: deploy-verify
description: >
  Deploys Vecinita to the configured target (Render, Docker, K8s, etc.), monitors CI/CD,
  validates migrations and API health, and runs post-deploy checks. Use when deploying,
  pushing to production, or validating a staging environment.
---

# Deploy & Verify (Vecinita)

Deploy the RAG API (and worker if separate), run database migrations, and validate
the deployment against `docs/deployment-integration.md`.

**Cross-cutting:** [considerations.md](../considerations.md).

## Prerequisites

1. `docs/execution-plan.md` — deploy phase ready
2. `docs/deployment-integration.md` — services, secrets, migrate hook
3. `docs/data-management-plan.md` — migration revision, seed policy
4. Build/verify green (08-verify-build / 09-qa) unless user waives

## State

`docs/deploy-state.md` — status, URL, commit, step log.

## Workflow (summary)

### Phase 1 — Pre-deploy

Parallel checks:

- **Config**: app name, `DATABASE_URL`, required secrets (names only)
- **Dependencies**: lockfile install dry-run
- **Migrations**: `alembic current` vs head locally
- **Data**: `scripts/verify_data.py` on fixtures

### Phase 2 — Deploy

Execute deploy per plan (e.g. Render deploy, `docker compose up`, `kubectl apply`).
Run **migrations** on target before traffic.

### Phase 3 — Post-deploy validation

- `GET /health` → 200
- H3 smoke: ingest fixture doc → query returns expected source id
- Worker: one job completes if separate service
- Query p95 logged (informational)

### Phase 4 — Changelog & monitoring

Per [considerations.md](../considerations.md) §3 — update `docs/CHANGELOG.md` or deploy report.

## Failure handling

AskQuestion: fix and retry (max 3), abort, or rollback per deployment-integration.md.

## Rollback

Documented in deployment plan (revert release, forward-only migrations policy).

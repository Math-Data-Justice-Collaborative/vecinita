# Current Render Integration Landscape

> Auto-generated: 2026-05-11

## Summary

Vecinita runs five web services and one PostgreSQL database on Render, deployed via a root `render.yaml` Blueprint. All services use Docker runtimes, the `starter` plan, and `autoDeployTrigger: checksPass` (deploy only after GitHub CI passes). Environment variables are managed through a shared Render env group with `sync: false` semantics — the Blueprint declares keys but the dashboard/env group holds authoritative values.

## Services

| Service | Type | Dockerfile | Context | Plan | Health | Region |
|---------|------|------------|---------|------|--------|--------|
| vecinita-agent | web | `apis/agent/Dockerfile` | `.` (root) | starter | `/health` | virginia |
| vecinita-frontend | web | `frontends/chat/Dockerfile` | `./frontends/chat` | starter | `/health` | virginia |
| vecinita-gateway | web | `apis/gateway/Dockerfile.gateway` | `.` (root) | starter | `/health` | virginia |
| vecinita-data-management-frontend-v1 | web | `frontends/data-management/Dockerfile` | `./frontends/data-management` | starter | `/` | virginia |
| vecinita-data-management-api-v1 | web | `modal-apps/scraper/Dockerfile` | `./modal-apps/scraper` | starter | `/health` | virginia |

## Database

| Name | Engine | Version | Plan | Disk | Region |
|------|--------|---------|------|------|--------|
| vecinita-postgres | PostgreSQL | 16 | basic-256mb | 1 GB | virginia |

**Consumers:** Agent (fromDatabase), Gateway (fromDatabase), DM API (fromDatabase)

## Service Connectivity

| Source | Target | Mechanism | Variable |
|--------|--------|-----------|----------|
| vecinita-gateway | vecinita-agent | fromService (hostport) | `AGENT_SERVICE_URL` |
| vecinita-agent | vecinita-postgres | fromDatabase (connectionString) | `DATABASE_URL` |
| vecinita-gateway | vecinita-postgres | fromDatabase (connectionString) | `DATABASE_URL` |
| vecinita-data-management-api-v1 | vecinita-postgres | fromDatabase (connectionString) | `DATABASE_URL` |
| vecinita-frontend | vecinita-gateway | VITE_GATEWAY_URL (external) | `VITE_GATEWAY_URL` |
| vecinita-data-management-frontend-v1 | vecinita-data-management-api-v1 | VITE_DM_API_BASE_URL (external) | `VITE_DM_API_BASE_URL` |
| vecinita-agent | Modal (embedding) | Modal Function SDK | `MODAL_TOKEN_*` |
| vecinita-gateway | Modal (scraper) | Modal Function SDK | `MODAL_TOKEN_*` |

## Environment Variable Contract

**Governance model:** The `render.yaml` Blueprint declares environment keys. Infrastructure bindings (`fromDatabase`, `fromService`, inline `PORT`) are set directly. All other variables use `sync: false` — values are managed in the Render dashboard env group and never overwritten by Blueprint syncs.

**Ownership legend (from render.yaml header):**
- **CORE** — shared infrastructure: DATABASE_URL, ALLOWED_ORIGINS
- **AGENT** — consumed by vecinita-agent
- **GW** — consumed by vecinita-gateway
- **FE** — consumed by frontends (VITE_* vars)
- **MODAL** — Modal SDK / upstream endpoint refs
- **STRICT** — strict-mode / enforcement flags

**Key policies:**
- PORT is always `10000` (Render Docker default)
- `MODAL_SCRAPER_PERSIST_VIA_GATEWAY=1` (gateway owns scraping_jobs persistence)
- `SCRAPER_DEBUG_BYPASS_AUTH=false` (never bypass auth in production)
- FR-004 canonical URL names: `RENDER_GATEWAY_URL`, `RENDER_AGENT_URL`, `DATA_MANAGEMENT_API_URL`
- No shadow/parallel base URL vars for the same destination

## CI/CD Workflows

### render-deploy.yml

| Trigger | Purpose |
|---------|---------|
| PR + push to main | Quality gates, path-filtered checks |

Runs lint, type-check, unit tests, and contract tests. Render deploys only after this workflow's checks pass (`autoDeployTrigger: checksPass`).

### render-post-deploy.yml

| Trigger | Purpose |
|---------|---------|
| workflow_run (after render-deploy) | Optional deploy-wait polling |

Monitors deployment completion; can be used to run post-deploy smoke tests.

### render-preview-attestation-gate.yml

| Trigger | Purpose |
|---------|---------|
| PR to main | Validate preview deploy + attestation freshness |

Checks:
- PR title includes `[render preview]`
- `.ci/render-live-attestation.json` exists and validates
- Attestation is fresh (< 24h), tied to PR head SHA
- All live checks report passed

## Attestation Pipeline

| File | Purpose |
|------|---------|
| `.ci/render-live-attestation.json` | Committed proof that PR preview is healthy |
| `scripts/ci/render_live_attestation_generate.py` | Generate attestation from live health checks |
| `scripts/ci/render_live_attestation_validate.py` | Validate attestation format, freshness, and check status |

**Current attestation state:**
```json
{
  "format_version": 1,
  "git_head": "3f77232",
  "status": "passed",
  "live_checks": ["health (200)", "openapi.json (200)"]
}
```

**Attestation refresh workflow:**
1. Push PR with `[render preview]` in title
2. Wait for Render preview service to deploy (use Render MCP to poll)
3. Run `python3 scripts/ci/render_live_attestation_generate.py` against preview URL
4. Commit updated `.ci/render-live-attestation.json`
5. `render-preview-attestation-gate.yml` validates on PR

## PR Preview Environments

Render automatically creates preview services for PRs targeting `main` when the Blueprint is connected. Preview services mirror production topology but run against their own isolated preview URLs.

**Requirements:**
- PR title must include `[render preview]`
- Preview services must reach live status before merge
- Attestation must validate for the PR head SHA

**Monitoring via Render MCP:**
- `list_services` with `includePreviews: true` → find PR preview services
- `list_deploys` → check deploy status per service
- `get_deploy` → poll until terminal state
- `list_logs` → investigate failures

## Deploy Pipeline Flow

```
Code push → GitHub PR
  → GitHub Actions CI (render-deploy.yml)
    → Tests pass
      → Render auto-deploys (checksPass trigger)
        → Docker build + deploy
          → Health check validates
            → [PR] Attestation generated + committed
              → render-preview-attestation-gate validates
                → PR is merge-ready
```

## Local Development Parity

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Full local stack (Postgres, pgAdmin, all services) |
| `docker-compose.dev.yml` | Dev overrides |
| `docker-compose.microservices.yml` | Microservices variant |
| `docker-compose.render-parity.yml` | Mimics Render topology locally |
| `docker-compose.render-local.yml` | Lightweight Render-local variant |

## Monitoring

| Tool | Usage |
|------|-------|
| Render MCP (`project-0-vecinita-render`) | `list_services`, `list_deploys`, `get_deploy`, `list_logs` |
| Health check endpoints | `GET /health` on each service |
| GitHub Actions | CI status, attestation gate |
| Render Dashboard | Logs, metrics, scaling, env group management |

## Key Documentation

| Document | Path |
|----------|------|
| Shared env contract | `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` |
| Service boundaries | `docs/deployment/SERVICE_BOUNDARIES.md` |
| Service connectivity | `docs/deployment/SERVICE_CONNECTIVITY.md` |
| CI/CD pipeline | `docs/deployment/RENDER_STAGING_PROD_CICD.md` |
| Troubleshooting | `docs/deployment/RENDER_TROUBLESHOOTING_RUNBOOK.md` |
| Gateway troubleshooting | `docs/deployment/RENDER_GATEWAY_DEPLOY_TROUBLESHOOTING.md` |
| DM deploy guide | `docs/deployment/DATA_MANAGEMENT_RENDER_DEPLOYMENT_GUIDE.md` |

## Spec-driven development context

This document is part of the project's spec-driven development workflow. Feature specs live under `specs/NNN-slug-name/`. Key related specs:
- `specs/002-dm-api-docker-build/` — DM API Docker build
- `specs/016-faster-render-ci-builds/` — Faster Render CI builds
- `specs/019-contract-ci-json-gate/` — Contract CI and attestation gate

Cross-reference `specs/authoritative/` for other authoritative documents (dependencies, Modal integration, changelogs).

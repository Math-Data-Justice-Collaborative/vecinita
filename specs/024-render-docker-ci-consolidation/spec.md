# Feature Specification: Render, Docker, and CI Consolidation

**Spec ID**: 024  
**Feature Branch**: `024-render-docker-ci-consolidation`  
**Created**: 2026-05-13  
**Status**: Draft  
**Phase**: 5 (Migration Sequence — see `specs/monorepo-decomposition/09-migration-sequence.md`)  
**Technical Decisions**: TD-003 (Docker Compose with profiles), TD-004 (PgAdmin as private service), TD-005 (Per-app CI workflows)

## Overview

Consolidate the deployment, local development, and CI infrastructure from the current fragmented
state (5 docker-compose files, 17 GitHub Actions workflows, submodule-era render.yaml) into a clean
single-file-per-concern model: one `render.yaml`, one `docker-compose.yml` with profiles, and
~8-10 focused CI workflows with path filters.

This eliminates configuration drift between environments, reduces cognitive overhead for a solo
developer, and ensures local development closely mirrors production.

## Dependencies

| Spec | Title | Relationship |
|------|-------|-------------|
| 020 | Monorepo Layout | Must complete first — file paths in configs reference `apps/` structure |

## Requirements

### Functional Requirements

#### Render Blueprint

- **FR-001**: A single `render.yaml` at the repository root MUST define all Render-deployed services.
  No other Render blueprint files may exist in the repository.

- **FR-002**: The `render.yaml` MUST define the following services:
  | Service Name | Type |
  |-------------|------|
  | `vecinita-chat-frontend` | web |
  | `vecinita-data-management-frontend` | web |
  | `vecinita-docs-site` | web |
  | `vecinita-gateway` | web |
  | `vecinita-agent` | web |
  | `vecinita-data-management-api` | web |
  | `vecinita-pgadmin` | pserv |

- **FR-003**: All backend service Dockerfiles (`gateway`, `agent`, `data-management-api`) MUST use
  the repository root (`.`) as `dockerContext` to allow `COPY` of `packages/` shared code.

- **FR-004**: All frontend service Dockerfiles (`chat-frontend`, `data-management-frontend`,
  `docs-site`) MUST use their own directory as `dockerContext` (self-contained builds).

- **FR-005**: PgAdmin MUST be deployed as a Render private service (`type: pserv`), not publicly
  accessible from the internet.

#### Docker Compose

- **FR-006**: A single `docker-compose.yml` at the repository root MUST provide local development
  with the following profiles:
  - `core`: PostgreSQL + PgAdmin (infrastructure only)
  - `services`: Backend API services (gateway, agent, data-management-api)
  - `frontends`: Frontend development servers
  - `full`: All of the above combined

- **FR-007**: The following legacy docker-compose files MUST be removed:
  - `docker-compose.dev.yml`
  - `docker-compose.microservices.yml`
  - `docker-compose.render-local.yml`
  - `docker-compose.render-parity.yml`

- **FR-011**: `docker compose --profile core up` MUST start PostgreSQL 16 and PgAdmin with no
  other services.

- **FR-012**: `docker compose --profile full up` MUST start all services (postgres, pgadmin,
  gateway, agent, data-management-api, chat-frontend, data-management-frontend).

#### CI/CD

- **FR-008**: Per-app GitHub Actions CI workflows MUST use path filters so that changes to
  `apps/gateway/**` trigger only `ci-gateway.yml`, changes to `apps/agent/**` trigger only
  `ci-agent.yml`, etc. Changes to `packages/**` MUST trigger CI for all backend services that
  depend on shared packages.

- **FR-009**: A shared `quality-gate.yml` workflow MUST run on all pull requests regardless of path,
  performing linting, type checking, and security scanning.

- **FR-010**: The existing 17 workflow files MUST be consolidated to ~8-10 focused workflows:
  | Workflow | Trigger Paths |
  |----------|--------------|
  | `ci-gateway.yml` | `apps/gateway/**`, `packages/**` |
  | `ci-agent.yml` | `apps/agent/**`, `packages/**` |
  | `ci-data-management-api.yml` | `apps/data-management-api/**`, `packages/**` |
  | `ci-chat-frontend.yml` | `apps/chat-frontend/**` |
  | `ci-data-management-frontend.yml` | `apps/data-management-frontend/**` |
  | `ci-modal-workers.yml` | `apps/vllm-inference/**`, `apps/embedding-worker/**`, `apps/scraper-worker/**`, `apps/indexing-worker/**` |
  | `deploy-render.yml` | Push to main (post-CI) |
  | `quality-gate.yml` | All PRs |

#### Health Checks

- **FR-013**: All services MUST pass health checks in both the local `docker-compose.yml`
  environment and the Render production environment after this consolidation is applied.

### Non-Functional Requirements

- **NFR-001**: `docker compose --profile core up` MUST reach healthy state within 30 seconds on a
  developer machine with images cached.
- **NFR-002**: CI workflows MUST not trigger for unrelated path changes (no false positives from
  path filters).
- **NFR-003**: The render.yaml MUST be valid according to `render blueprint validate` (Render CLI).

## User Stories

### US-001: Developer starts local infrastructure (Priority: P1)

A developer clones the repo and wants to start just the database and pgadmin for local development
(running app services directly with `uv run` or similar).

**Acceptance Scenarios**:

- **AS-001**: Given a fresh clone with Docker installed, when the developer runs
  `docker compose --profile core up`, then PostgreSQL 16 and PgAdmin start and become healthy within
  30 seconds.
- **AS-002**: Given the core profile is running, when the developer connects to PgAdmin at
  `localhost:5050`, then the PgAdmin UI loads and the local PostgreSQL server is pre-configured.
- **AS-003**: Given only the core profile is running, when the developer checks running containers,
  then no application service containers (gateway, agent, frontends) are running.

### US-002: Developer starts full stack locally (Priority: P1)

A developer wants to run the entire application stack in Docker for integration testing.

**Acceptance Scenarios**:

- **AS-004**: Given Docker installed and `.environments/` files configured, when the developer runs
  `docker compose --profile full up`, then all services start including postgres, pgadmin, gateway,
  agent, data-management-api, chat-frontend, and data-management-frontend.
- **AS-005**: Given the full profile is running, when the developer curls `localhost:<gateway-port>/health`,
  then it returns HTTP 200.
- **AS-006**: Given the full profile is running, when the developer opens `localhost:<frontend-port>`,
  then the chat frontend loads.

### US-003: Developer pushes changes to gateway only (Priority: P1)

A developer modifies files only in `apps/gateway/` and pushes. Only the gateway CI should run.

**Acceptance Scenarios**:

- **AS-007**: Given a PR that only modifies files under `apps/gateway/`, when GitHub Actions
  triggers, then only `ci-gateway.yml` and `quality-gate.yml` run.
- **AS-008**: Given a PR that only modifies files under `apps/gateway/`, when GitHub Actions
  triggers, then `ci-chat-frontend.yml`, `ci-agent.yml`, and other app-specific workflows do NOT
  run.
- **AS-009**: Given a PR that modifies files under `packages/db/`, when GitHub Actions triggers,
  then `ci-gateway.yml`, `ci-agent.yml`, and `ci-data-management-api.yml` all run (shared
  dependency changed).

### US-004: Developer removes legacy docker-compose files (Priority: P2)

Legacy files are removed and no references to them remain in documentation or scripts.

**Acceptance Scenarios**:

- **AS-010**: Given the consolidation is complete, when searching the repository for references to
  `docker-compose.dev.yml`, `docker-compose.microservices.yml`, `docker-compose.render-local.yml`,
  or `docker-compose.render-parity.yml`, then zero references exist in any non-git-history file.
- **AS-011**: Given the legacy files are removed, when the Makefile is inspected, then all
  `docker compose` targets reference only the single `docker-compose.yml` (via profiles).

### US-005: Render deployment uses consolidated blueprint (Priority: P1)

The Render platform reads the single `render.yaml` and deploys all services correctly.

**Acceptance Scenarios**:

- **AS-012**: Given the new `render.yaml` is pushed to main, when Render performs a blueprint sync,
  then all 7 services are created/updated with correct Dockerfile paths and docker contexts.
- **AS-013**: Given the render.yaml is deployed, when checking the PgAdmin service on Render, then
  it is marked as a private service (`pserv`) and has no public URL.
- **AS-014**: Given the render.yaml is deployed, when the gateway service builds, then it
  successfully copies `packages/` from the root docker context into the image.

### US-006: Quality gate runs on every PR (Priority: P1)

All PRs get baseline quality checks regardless of which files changed.

**Acceptance Scenarios**:

- **AS-015**: Given a PR that only modifies `README.md`, when GitHub Actions triggers, then
  `quality-gate.yml` still runs (linting, type checking).
- **AS-016**: Given the quality gate workflow, when it runs, then it performs at minimum: Python
  linting (ruff), TypeScript type checking (tsc), and security scanning.

## Success Criteria

- **SC-001**: Exactly one `render.yaml` exists at repository root; zero other Render blueprint files
  exist anywhere in the repository.
- **SC-002**: Exactly one `docker-compose.yml` exists at repository root; zero legacy
  docker-compose files remain.
- **SC-003**: `docker compose --profile core up` starts postgres + pgadmin and both pass health
  checks.
- **SC-004**: `docker compose --profile full up` starts all services and all pass health checks.
- **SC-005**: The workflow count in `.github/workflows/` is between 8 and 10 (down from 17).
- **SC-006**: A PR touching only `apps/chat-frontend/**` triggers exactly `ci-chat-frontend.yml`
  and `quality-gate.yml` — no other CI workflows.
- **SC-007**: `render blueprint validate` (or equivalent Render CLI check) passes on the new
  `render.yaml`.
- **SC-008**: PgAdmin is deployed as a private service on Render with no public URL.
- **SC-009**: All backend Docker images successfully build with root context (can access `packages/`).

## Implementation Notes

### Profile Structure

```yaml
services:
  postgres:
    profiles: ["core", "full"]
    image: postgres:16-alpine
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vecinita"]
      interval: 5s
      timeout: 3s
      retries: 5

  pgadmin:
    profiles: ["core", "full"]
    image: dpage/pgadmin4:latest
    ports: ["5050:80"]

  gateway:
    profiles: ["services", "full"]
    build:
      context: .
      dockerfile: ./apps/gateway/Dockerfile
    depends_on:
      postgres: { condition: service_healthy }

  # ... etc
```

### CI Workflow Template

```yaml
# .github/workflows/ci-gateway.yml
name: CI - Gateway
on:
  push:
    paths:
      - 'apps/gateway/**'
      - 'packages/**'
  pull_request:
    paths:
      - 'apps/gateway/**'
      - 'packages/**'
```

### Files to Remove

```
docker-compose.dev.yml
docker-compose.microservices.yml
docker-compose.render-local.yml
docker-compose.render-parity.yml
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Profile syntax differences across Docker Compose versions | `--profile` flag not recognized | Pin minimum docker compose version in README; test with v2.20+ |
| Path filters too narrow — miss shared dependency changes | Broken deploys pass CI | Include `packages/**` in all backend workflow triggers |
| Render blueprint sync overwrites manual env var changes | Lost configuration | Document which vars are blueprint-managed vs manually set |
| Legacy compose references in developer muscle memory | Confusion, stale commands | Update Makefile targets; add deprecation notice in commit message |

## Open Questions

- Should `docs-site` be included in the Render blueprint or deployed via GitHub Pages instead?
- Should Modal workers have a CI workflow that validates `modal deploy --dry-run`?
- What is the minimum Docker Compose version to enforce for profile support?

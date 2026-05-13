# Feature Specification: Environment Consolidation

**Spec ID**: 025  
**Feature Branch**: `025-environment-consolidation`  
**Created**: 2026-05-13  
**Status**: Draft  
**Phase**: 6 (Migration Sequence — see `specs/monorepo-decomposition/09-migration-sequence.md`)

## Overview

Consolidate all environment variable files from their current scattered locations (19 `.env` files
across service directories) into a single `.environments/` directory at the repository root. Each
service gets a dedicated `.env` file with a corresponding `.env.example` template that is version-
controlled. This eliminates duplication, makes secrets management predictable, and ensures new
developers can onboard by running a single command.

## Dependencies

| Spec | Title | Relationship |
|------|-------|-------------|
| 020 | Monorepo Layout | Must complete first — services in `apps/` structure |
| 024 | Render/Docker/CI Consolidation | Must complete first — docker-compose.yml references `.environments/` paths |

## Requirements

### Functional Requirements

#### Directory Structure

- **FR-001**: A `.environments/` directory MUST be created at the repository root to house all
  service environment files.

- **FR-002**: The following per-service `.env` files MUST be created in `.environments/`:
  - `gateway.env`
  - `agent.env`
  - `data-management-api.env`
  - `chat-frontend.env`
  - `data-management-frontend.env`
  - `pgadmin.env`
  - `vllm-inference.env`
  - `embedding-worker.env`
  - `scraper-worker.env`
  - `indexing-worker.env`

- **FR-003**: For each service `.env` file, a corresponding `.env.example` file MUST be created with
  documented defaults, placeholder values, and descriptions. These example files MUST be checked
  into version control.

#### Documentation

- **FR-004**: A `.environments/README.md` MUST be created documenting:
  - Every environment variable across all services
  - Which service owns each variable
  - Whether the variable is required or optional
  - Description of what each variable controls
  - Default values where applicable
  - Cross-references between services that share variables (e.g., database connection strings)

#### Integration

- **FR-005**: The `docker-compose.yml` MUST reference environment files using `env_file` directives
  pointing to `.environments/<service>.env` paths. Example:
  ```yaml
  gateway:
    env_file: .environments/gateway.env
  ```

- **FR-006**: The `render.yaml` MUST be updated to document which environment variables are managed
  via the Render dashboard (secrets, connection strings) versus which come from the `.environments/`
  templates. A comment block in `render.yaml` MUST map each service to its corresponding
  `.environments/<service>.env.example` for reference.

#### Cleanup

- **FR-007**: All scattered `.env` files currently in service directories (19 files) MUST be
  removed. No `.env` files may exist outside of `.environments/` after this migration.

#### Git Configuration

- **FR-008**: The repository `.gitignore` MUST be updated with the following rules:
  ```gitignore
  # Environment secrets — never commit
  .environments/*.env
  # Templates are safe to commit
  !.environments/*.env.example
  # README is safe to commit
  !.environments/README.md
  ```

#### Developer Tooling

- **FR-009**: A `make setup-env` target MUST be provided that copies every `.env.example` to its
  corresponding `.env` for all services in a single command. The target MUST NOT overwrite existing
  `.env` files (to protect developer customizations).

- **FR-010**: All services MUST start correctly when using their `.environments/<service>.env` file
  as the sole source of environment configuration (no hidden reliance on other env files or shell
  exports).

### Non-Functional Requirements

- **NFR-001**: The `.env.example` files MUST contain only non-secret placeholder values. No real
  API keys, passwords, or connection strings with credentials may appear in example files.
- **NFR-002**: The `make setup-env` command MUST complete in under 2 seconds.
- **NFR-003**: Environment variable names MUST follow the convention `SERVICE_VARNAME` or standard
  names (e.g., `DATABASE_URL`, `PORT`) — no ambiguous or conflicting names across services.

## User Stories

### US-001: New developer onboards with environment setup (Priority: P1)

A new developer clones the repository and needs to configure environment variables for local
development.

**Acceptance Scenarios**:

- **AS-001**: Given a fresh clone of the repository, when the developer runs `make setup-env`, then
  `.environments/<service>.env` files are created for all 10 services from their `.env.example`
  templates.
- **AS-002**: Given `make setup-env` has run, when the developer inspects any generated `.env` file,
  then it contains commented descriptions explaining each variable and safe default values where
  possible.
- **AS-003**: Given `.env` files already exist in `.environments/`, when the developer runs
  `make setup-env` again, then existing files are NOT overwritten (no data loss of custom values).

### US-002: Developer understands environment variable ownership (Priority: P1)

A developer needs to know which service owns a particular environment variable and what it controls.

**Acceptance Scenarios**:

- **AS-004**: Given the `.environments/README.md` exists, when a developer searches for
  `DATABASE_URL`, then they find which services use it, what format it expects, and whether it
  differs per service (e.g., different `search_path` per schema).
- **AS-005**: Given the README, when a developer looks up any variable from any `.env.example` file,
  then it appears in the README with owner, description, required/optional status, and default value.

### US-003: Docker Compose uses centralized env files (Priority: P1)

The docker-compose.yml sources environment from `.environments/` rather than scattered locations.

**Acceptance Scenarios**:

- **AS-006**: Given `docker-compose.yml` references `env_file: .environments/gateway.env`, when
  `docker compose --profile services up` runs, then the gateway container has all variables from
  `gateway.env` available in its process environment.
- **AS-007**: Given only `.environments/` env files exist (no other .env files), when all services
  start via docker-compose, then no service fails due to missing environment variables.

### US-004: Secrets never leak to version control (Priority: P1)

Real secrets in `.env` files are protected from accidental commits.

**Acceptance Scenarios**:

- **AS-008**: Given the updated `.gitignore`, when a developer creates `.environments/gateway.env`
  with real secrets and runs `git status`, then the file appears as untracked/ignored.
- **AS-009**: Given the updated `.gitignore`, when a developer modifies
  `.environments/gateway.env.example`, then `git status` shows it as a tracked change (not
  ignored).
- **AS-010**: Given the repository history after this migration, when searching git log for common
  secret patterns (API keys, passwords), then no real secrets appear in any committed
  `.env.example` file.

### US-005: Scattered env files are removed (Priority: P2)

All old `.env` files in service directories are cleaned up to prevent confusion.

**Acceptance Scenarios**:

- **AS-011**: Given the migration is complete, when searching the repository for `.env` files
  outside of `.environments/`, then zero results are found (excluding `.gitignore` and
  documentation references).
- **AS-012**: Given a developer who previously used `apis/gateway/.env`, when they look for
  environment configuration, then they find a clear pointer to `.environments/gateway.env` (via
  README or Makefile output).

### US-006: Render deployment documentation is clear (Priority: P2)

Operators understand which env vars are managed by Render vs which come from templates.

**Acceptance Scenarios**:

- **AS-013**: Given the updated `render.yaml`, when an operator reads the service definition for
  gateway, then comments or documentation clearly indicate which variables are set via Render env
  groups and which match the `.environments/gateway.env.example` template.
- **AS-014**: Given Render environment groups, when an operator needs to add a new env var for
  gateway, then the README documents the process: add to `.env.example`, add to Render group, update
  README.

## Success Criteria

- **SC-001**: `.environments/` directory exists at repo root with exactly 10 `.env.example` files
  (one per service) checked into version control.
- **SC-002**: `make setup-env` creates all 10 `.env` files from examples in a single invocation
  without errors.
- **SC-003**: Zero `.env` files exist outside of `.environments/` in the repository tree (verified
  by `find . -name "*.env" -not -path "./.environments/*" -not -path "./.git/*"`).
- **SC-004**: `git status` shows `.environments/*.env` as ignored and `.environments/*.env.example`
  as tracked.
- **SC-005**: `docker compose --profile full up` starts all services successfully using only
  `.environments/<service>.env` as their env source.
- **SC-006**: `.environments/README.md` documents every variable from every `.env.example` file
  with owner, description, and required/optional designation.
- **SC-007**: No `.env.example` file contains real secrets (validated by scanning for common secret
  patterns: actual API keys, non-placeholder passwords, real connection strings with credentials).

## Implementation Notes

### Makefile Target

```makefile
.PHONY: setup-env
setup-env:
	@echo "Setting up environment files..."
	@for example in .environments/*.env.example; do \
		target="$${example%.example}"; \
		if [ ! -f "$$target" ]; then \
			cp "$$example" "$$target"; \
			echo "  Created $$target"; \
		else \
			echo "  Skipped $$target (already exists)"; \
		fi \
	done
	@echo "Done. Edit .environments/*.env files with your local values."
```

### Example .env.example Format

```bash
# .environments/gateway.env.example
# Gateway Service Environment Configuration
# Copy to gateway.env and fill in real values

# === Database ===
# PostgreSQL connection string (schema-scoped to gateway)
DATABASE_URL=postgresql://vecinita:changeme@localhost:5432/vecinita?options=-c search_path=gateway,shared,public

# === Server ===
# Port the gateway listens on
PORT=8000
# Host binding
HOST=0.0.0.0

# === Auth ===
# API key for authenticating external requests (generate a random string)
API_KEY=changeme-generate-a-real-key

# === Services ===
# Internal URL for the agent service
AGENT_SERVICE_URL=http://localhost:8001
# Internal URL for the data management API
DATA_MANAGEMENT_API_URL=http://localhost:8002

# === Modal ===
# Modal token for triggering serverless workers
MODAL_TOKEN_ID=changeme
MODAL_TOKEN_SECRET=changeme
```

### Current Scattered Files to Remove (19 total)

Locations to audit and clean:
- `apis/gateway/.env`
- `apis/gateway/.env.example`
- `apis/data-management-api/.env`
- `frontends/chat/.env`
- `frontends/chat/.env.local`
- `frontends/data-management/.env`
- `modal-apps/scraper/.env`
- `modal-apps/embedding-modal/.env`
- `modal-apps/model-modal/.env`
- Various other service-level `.env` files

(Exact list to be confirmed during implementation by scanning the repository.)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Developers have local `.env` files with custom values | Lost customization during migration | Announce migration; provide `make setup-env` that doesn't overwrite; document in PR |
| CI workflows may depend on `.env` file locations | Broken CI | Audit all workflow files for `env_file` or `.env` references before removing old files |
| Docker Compose env_file paths are relative to compose file | Wrong path resolution | Test with `docker compose config` to verify variable resolution |
| Some services may source env vars from multiple files | Missing variables after consolidation | Audit each service's actual env var reads; ensure single file contains all needed vars |

## Open Questions

- Should there be a `.environments/shared.env` for variables common across all services (e.g.,
  `DATABASE_HOST`, `DATABASE_PORT`)?
- Should the `make setup-env` target also run `docker compose config --quiet` to validate the
  generated env files work with docker-compose?
- Should env var validation (checking required vars are set) be added to each service's startup?

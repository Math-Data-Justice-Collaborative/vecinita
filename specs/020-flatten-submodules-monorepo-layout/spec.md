# Feature Specification: Flatten submodules to monorepo layout

**Spec ID**: 020  
**Feature Branch**: `020-flatten-submodules-monorepo-layout`  
**Created**: 2026-05-13  
**Status**: Draft  
**Phase**: 1 (Layout) — per `specs/monorepo-decomposition/09-migration-sequence.md`  
**Blocks**: Specs 021, 022, and all subsequent migration phases  
**Dependencies**: None (first phase)  
**Risk**: Medium — import path changes may break across many files  
**Effort**: M (2–3 days)

## Overview

Convert Vecinita from a git-submodule-based repository to a true `apps/` + `packages/` monorepo. This phase deinits all 6 git submodules, moves every service to its target directory under `apps/`, creates the `packages/` and `.environments/` directories, and updates all references (imports, Dockerfiles, Makefile, .gitignore) so the codebase builds from the new layout.

This is the foundational migration step. Every subsequent spec (gateway/agent extraction, vLLM integration, schema-per-service, infrastructure consolidation) depends on this layout being in place.

### Submodule Migration Map

| Current Path (Submodule) | Target Path | Submodule URL |
|--------------------------|-------------|---------------|
| `frontends/chat/` | `apps/chat-frontend/` | `Vecinitafrontend.git` (branch: dev) |
| `frontends/data-management/` | `apps/data-management-frontend/` | `vecinita-data-management-frontend.git` (branch: main) |
| `apis/data-management-api/` | `apps/data-management-api/` | `vecinita-data-management.git` (branch: main) |
| `modal-apps/scraper/` | `apps/scraper-worker/` | `vecinita-scraper.git` (branch: main) |
| `modal-apps/embedding-modal/` | `apps/embedding-worker/` | `vecinita-embedding.git` (branch: main) |
| `modal-apps/model-modal/` | `apps/vllm-inference/` | `vecinita-model.git` (branch: main) |

### Non-Submodule Moves

| Current Path | Target Path | Action |
|-------------|-------------|--------|
| `apis/gateway/` | `apps/gateway/` | Move |
| `apis/agent/` | `apps/agent/` | Move (placeholder — populated in spec 021) |
| `docs-site/` | `apps/docs-site/` | Move |
| `packages/python/db` | `packages/db/` | Move |
| (docker-compose pgadmin) | `apps/pgadmin/` | Create config dir |
| (new) | `apps/indexing-worker/` | Create placeholder |
| (scattered config) | `packages/config/` | Create placeholder |
| (scattered types) | `packages/common/` | Create placeholder |
| (scattered .env) | `.environments/` | Create with per-service env files |

## User Scenarios & Testing

### User Story 1 — Flat service discovery (Priority: P1)

**US-001**: As a developer, I can find any service under `apps/<name>/` without navigating git submodules, so that I have a single mental model for the project structure.

**Why this priority**: The submodule layout is the primary source of onboarding friction and CI complexity. Every developer interaction starts with knowing where code lives.

**Independent Test**: From a clean clone, `ls apps/` lists all 11 service directories. No `git submodule init` or `git submodule update` is required to access any service's source code.

**Acceptance Scenarios**:

1. **Given** a fresh `git clone` of the repository, **When** a developer runs `ls apps/`, **Then** they see exactly 11 directories: `chat-frontend`, `data-management-frontend`, `docs-site`, `gateway`, `agent`, `data-management-api`, `pgadmin`, `vllm-inference`, `embedding-worker`, `scraper-worker`, `indexing-worker`.
2. **Given** the flattened repository, **When** a developer opens any service directory, **Then** they find the service's source code, Dockerfile (where applicable), and dependency manifest — not a git submodule pointer.
3. **Given** the flattened repository, **When** a developer runs `git submodule status`, **Then** the command reports no submodules (or `.gitmodules` does not exist / is empty).

---

### User Story 2 — CI builds from monorepo root (Priority: P1)

**US-002**: As CI, I can build any service from the monorepo root using standard Docker and make commands, so that builds do not depend on submodule initialization.

**Why this priority**: Current CI must `git submodule update --init --recursive` before building. This adds latency, introduces authentication requirements for submodule URLs, and creates a fragile dependency on external repository availability.

**Independent Test**: Run `docker build -f apps/gateway/Dockerfile .` from the repo root — it succeeds without any submodule commands.

**Acceptance Scenarios**:

1. **Given** the monorepo root, **When** CI runs `docker build -f apps/<service>/Dockerfile .` (or the service-specific context) for each Render-deployed service, **Then** the build completes without errors related to missing files or broken paths.
2. **Given** the monorepo Makefile, **When** CI runs any service build target (e.g., `make build-gateway`), **Then** the target succeeds using the new `apps/` paths.
3. **Given** the repository, **When** CI checks out the repo without `--recurse-submodules`, **Then** all service source code is present and builds succeed.

---

### User Story 3 — Shared package imports (Priority: P2)

**US-003**: As a developer, I can import shared code from `packages/` in any Python service, so that common DB models, config loading, and utility types live in one place.

**Why this priority**: Shared code is currently duplicated or tightly coupled inside the gateway. Extracting it to `packages/` is a prerequisite for the gateway/agent split in spec 021.

**Independent Test**: A Python service under `apps/` can `from packages.db.models import ...` (or equivalent pip-installed path) and the import resolves at runtime.

**Acceptance Scenarios**:

1. **Given** `packages/db/` contains database models, **When** `apps/gateway/` imports from the `db` package, **Then** the import resolves without `sys.path` hacks or symlinks.
2. **Given** `packages/config/` contains config loading utilities, **When** any Python service imports from the `config` package, **Then** environment-specific configuration loads correctly.
3. **Given** the shared packages have `pyproject.toml` files, **When** a service's Dockerfile installs dependencies, **Then** shared packages are installed as editable or path dependencies.

---

### Edge Cases

- Submodule deinit on a repository where submodules are not initialized (fresh clone without `--recurse-submodules`) must not fail.
- Files in `.git/modules/` must be removed to prevent ghost submodule state.
- Any service with a `.git` directory inside it (from the submodule) must have that directory removed after flattening.
- Import path changes in Python must handle both relative and absolute imports.
- Dockerfiles that use `COPY . .` with a subdirectory context must be updated if the context changes to root.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST deinit all 6 git submodules (`frontends/chat`, `frontends/data-management`, `apis/data-management-api`, `modal-apps/scraper`, `modal-apps/embedding-modal`, `modal-apps/model-modal`), preserving their code as local directories tracked directly by the parent repository.
- **FR-002**: The system MUST create the `apps/` directory containing all 11 service directories: `chat-frontend`, `data-management-frontend`, `docs-site`, `gateway`, `agent`, `data-management-api`, `pgadmin`, `vllm-inference`, `embedding-worker`, `scraper-worker`, `indexing-worker`.
- **FR-003**: The system MUST create the `packages/` directory with shared Python packages: `db` (database models + migrations), `config` (shared config loading), `common` (shared types + constants). Each package MUST have a `pyproject.toml`.
- **FR-004**: The system MUST create the `.environments/` directory with per-service `.env.example` files for all services, and a `.gitignore` rule that ignores `*.env` but not `*.env.example`.
- **FR-005**: The system MUST move all existing service code to the new `apps/` locations per the migration map, preserving file contents and directory structure within each service.
- **FR-006**: The system MUST update all Python import paths in services that reference moved modules. Imports MUST resolve at runtime from the new layout without `sys.path` manipulation.
- **FR-007**: The system MUST update all Dockerfile `dockerfilePath` and `dockerContext` references so that `docker build` succeeds from the monorepo root. Backend services (`gateway`, `agent`, `data-management-api`) MUST use root `.` as dockerContext to access `packages/`. Frontend services MUST use their own directory as dockerContext.
- **FR-008**: The system MUST update Makefile targets to reference the new `apps/` and `packages/` paths. All existing `make` commands MUST continue to work.
- **FR-009**: The system MUST remove the now-empty legacy directories: `frontends/`, `apis/`, `modal-apps/`, `clients/`, `packages/openapi-clients/` (per TD-006), and `packages/python/`. The `.gitmodules` file MUST be removed or emptied.
- **FR-010**: The system MUST update `.gitignore` for the new layout, including: `.environments/*.env` (ignored), `.environments/*.env.example` (tracked), removal of submodule-specific ignore rules.

### Key Entities

- **Git submodule**: A pointer to an external repository at a specific commit, tracked in `.gitmodules` and `.git/modules/`.
- **Service directory**: A deployable unit under `apps/` with its own Dockerfile, dependency manifest, and source code.
- **Shared package**: A non-deployable library under `packages/` consumed by multiple services via path dependencies.
- **Migration map**: The mapping from current path to target path, as defined in `specs/monorepo-decomposition/02-app-inventory.md`.

## Acceptance Scenarios

- **AS-001**: **Given** the migration is complete, **When** `find apps/ -maxdepth 1 -type d | sort` is run, **Then** exactly 11 service directories are listed (matching FR-002).
- **AS-002**: **Given** the migration is complete, **When** `find packages/ -maxdepth 1 -type d | sort` is run, **Then** exactly 3 package directories are listed: `common`, `config`, `db`.
- **AS-003**: **Given** the migration is complete, **When** `cat .gitmodules` is run, **Then** the file is empty or does not exist.
- **AS-004**: **Given** the migration is complete, **When** `git submodule status` is run, **Then** no submodules are reported.
- **AS-005**: **Given** the migration is complete, **When** `docker build -f apps/gateway/Dockerfile .` is run from root, **Then** the build succeeds.
- **AS-006**: **Given** the migration is complete, **When** `docker build -f apps/chat-frontend/Dockerfile ./apps/chat-frontend` is run, **Then** the build succeeds.
- **AS-007**: **Given** the migration is complete, **When** Python services are started, **Then** all imports from `packages.db`, `packages.config`, and `packages.common` resolve without errors.
- **AS-008**: **Given** the migration is complete, **When** `ls frontends/ apis/ modal-apps/` is run, **Then** those directories do not exist.
- **AS-009**: **Given** the migration is complete, **When** `grep -r "submodule" .gitmodules .git/config 2>/dev/null` is run, **Then** no submodule references are found.
- **AS-010**: **Given** the migration is complete, **When** `make build-gateway` (or equivalent) is run, **Then** the Makefile target succeeds using `apps/gateway/` paths.

## Success Criteria

- **SC-001**: All 11 service directories exist under `apps/` with their source code, verified by `ls apps/` listing exactly 11 entries.
- **SC-002**: All 3 shared packages exist under `packages/` with valid `pyproject.toml` files, verified by `ls packages/` listing `db`, `config`, `common`.
- **SC-003**: Zero git submodule references remain in the repository — `.gitmodules` is removed or empty, `.git/modules/` contains no submodule data, and `git submodule status` reports nothing.
- **SC-004**: Docker builds succeed for all Render-deployed services when run from the monorepo root, verified by running `docker build` for each service's Dockerfile.
- **SC-005**: All Python import paths resolve at runtime — verified by starting each Python service and confirming no `ModuleNotFoundError` or `ImportError` on startup.
- **SC-006**: The Makefile contains updated targets for all services and `make help` (or equivalent) lists them correctly.
- **SC-007**: `.environments/` directory exists with `.env.example` files for all services, and `.gitignore` correctly ignores `.env` files but tracks `.env.example` files.
- **SC-008**: Legacy directories (`frontends/`, `apis/`, `modal-apps/`, `clients/`) do not exist in the repository.
- **SC-009**: A single `git clone` (without `--recurse-submodules`) yields a complete, buildable repository.

## Assumptions

- Submodule code is currently checked out and available locally (or can be fetched before deinit).
- The `packages/python/db` directory already exists and contains the DB models to move to `packages/db/`.
- `apps/agent/` is created as a placeholder in this phase; its source code is populated in spec 021.
- `apps/indexing-worker/` is created as a placeholder; its source code is populated in spec 022.
- `packages/config/` and `packages/common/` are created with minimal scaffolding (`__init__.py`, `pyproject.toml`); full extraction happens during spec 021.
- TD-006 (drop OpenAPI clients) is in effect — `packages/openapi-clients/` is removed.
- TD-007 (uv for dependency management) is the assumed tool for Python services.

## Technical References

- `specs/monorepo-decomposition/08-recommended-boundaries.md` — target layout
- `specs/monorepo-decomposition/09-migration-sequence.md` — Phase 1 details
- `specs/monorepo-decomposition/02-app-inventory.md` — full migration map
- `specs/monorepo-decomposition/11-infrastructure-impact.md` — Dockerfile and render.yaml changes
- `specs/.technical-decisions-log.json` — TD-001 (layout), TD-006 (drop OpenAPI clients), TD-007 (uv)
- `.gitmodules` — current submodule definitions

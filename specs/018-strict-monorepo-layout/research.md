# Research: Strict Canonical Monorepo Layout

## 1. Migration sequencing (phased vs big-bang)

**Decision**: **Phased migration by deployable or thin vertical slice**, merging only when `make ci` is green.

**Rationale**: Reduces blast radius; matches FR-011 (time-bounded legacy inventory) and SC-005. Render and Modal configs can be updated per slice without freezing the whole repo for one PR.

**Alternatives considered**:

- **Single big-bang PR**: Rejected — high risk of unreviewable diff and long-lived red CI.
- **Directories-only symlink first**: Deferred — extra complexity on Linux/Render; only revisit if moves break tooling.

## 2. Git history for moves

**Decision**: Prefer **`git mv`** (or `git mv`-equivalent renames in a single commit) for large trees where history is valuable (`backend/`, `services/*`, `frontend/`).

**Rationale**: Easier archaeology and `git blame` across the refactor.

**Alternatives considered**:

- **Copy + delete**: Acceptable only for generated output (e.g., regenerated clients) where history is noise.

## 3. `backend/` split (agent + gateway)

**Decision**: Treat **splitting shared `backend/src` into `apis/agent` and `apis/gateway`** as a **dedicated phase** after inventory: (1) document module boundaries (which packages import gateway-only vs agent-only code), (2) optionally extract **`packages/python/shared-schemas`** or internal libs only where already shared, (3) then physical split. Until split completes, path map may show **intermediate** rows (e.g., `backend/` → `apis/agent` only) with a follow-up row for gateway extraction.

**Rationale**: Both Dockerfiles copy `backend/src/` today; a naive folder rename would break gateway or agent entrypoints.

**Alternatives considered**:

- **Leave combined `apis/backend`**: Rejected — violates spec FR-001 (one Render API per folder).
- **Duplicate `src/` for gateway**: Rejected unless temporarily required for a single PR with explicit removal task—violates DRY and constitution service-boundary spirit.

## 4. Data-management API Render image (current state)

**Decision**: Document **as-is**: `render.yaml` service `vecinita-data-management-api-v1` uses **`./modal-apps/scraper/Dockerfile`** with context **`./modal-apps/scraper`** (see `render.yaml` comments). The same fact is recorded under **`PM-003`** in [artifacts/path-mapping.md](./artifacts/path-mapping.md). During refactor, **either** (a) keep that wiring until `apis/data-management-api` owns a dedicated image, or (b) introduce `apis/data-management-api/Dockerfile` and switch Render in the same task row as the path map.

**Rationale**: Prevents silent behavior change; operators must know DM API is not currently built from `apis/data-management-api/` subtree on Render.

**Alternatives considered**:

- **Assume DM API Dockerfile lives in submodule**: Incorrect for current production Render config—must be corrected in mapping and tasks.

## 5. OpenAPI / typed clients location

**Decision**: Migrate **`packages/openapi-clients/`** toward **`clients/apis/<gateway|agent|data-management-api>/`** per FR-005, updating codegen config, imports, and CI in the same change sets as defined in tasks.

**Rationale**: Matches spec and existing “contract-first” repo rules.

**Alternatives considered**:

- **Keep clients under `packages/openapi-clients`**: Rejected — conflicts with target tree and FR-005 naming.

## 6. Root `render.yaml` vs `infra/`

**Decision**: Keep **primary `render.yaml` at repository root** for Render’s default discovery; use **`infra/`** later only for non-primary fragments (e.g., compose helpers) with **README + quickstart** pointer if added.

**Rationale**: Satisfies FR-008 with minimal operator confusion; matches current repo.

**Alternatives considered**:

- **Move sole blueprint under `infra/render.yaml` only**: Possible but requires Render dashboard/doc updates—defer unless explicitly requested.

## 7. Submodule data-management API (canonical `apis/data-management-api/`)

**Decision**: Plan **`apis/data-management-api/`** as the canonical home (moved from **`services/data-management-api/`**); **preserve submodule relationship** (move `.git` / gitlink) where tooling allows, or document **submodule URL relocation** in path map if Git requires re-init.

**Rationale**: Keeps upstream DM API history and contribution model intact.

**Alternatives considered**:

- **Vendor subtree without submodule**: Only if product owners explicitly drop submodule—out of scope unless requested.

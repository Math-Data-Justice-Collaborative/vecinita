# Path migration map (authoritative)

**Feature**: [spec.md](../spec.md) · **Plan**: [plan.md](../plan.md)  
**Rule**: One source of truth (FR-013). `tasks.md` must cite `row_id` for structural work.

| row_id | legacy_path | canonical_path | deployable | status | owner | cutover_date | notes |
|--------|-------------|----------------|------------|--------|-------|--------------|-------|
| PM-001 | `frontend/` | `frontends/chat/` | chat | done | repo | | Render `vecinita-frontend` uses `./frontends/chat/Dockerfile` + context `./frontends/chat` |
| PM-002 | `apps/data-management-frontend/` | `frontends/data-management/` | data-management-frontend | done | repo | | Render `vecinita-data-management-frontend-v1` uses `./frontends/data-management/Dockerfile` + context `./frontends/data-management` |
| PM-003 | `services/scraper/` | `modal-apps/scraper/` | scraper | done | repo | | **Render:** `vecinita-data-management-api-v1` builds from **`./modal-apps/scraper/Dockerfile`** + context **`./modal-apps/scraper`** (same image/scrape tree as before the folder move). DM API still not built from `apis/data-management-api/` submodule on Render—reconcile when `apis/data-management-api/` owns a dedicated Dockerfile. |
| PM-004 | `services/embedding-modal/` | `modal-apps/embedding-modal/` | embedding-modal | done | repo | | Submodule path updated in `.gitmodules`; `git mv` completed |
| PM-005 | `services/model-modal/` | `modal-apps/model-modal/` | model-modal | done | repo | | Submodule path updated in `.gitmodules`; `git mv` completed |
| PM-006 | `services/data-management-api/` | `apis/data-management-api/` | data-management-api | done | repo | | Git submodule path + `.gitmodules` key `apis/data-management-api`; worktree at `apis/data-management-api/` (internal `gitdir` may remain under `.git/modules/services/data-management-api` until a future `git submodule` relocation). |
| PM-007 | `backend/` (agent image / agent entry) | `apis/agent/` | agent | done | repo | | **T016**: `apis/agent/Dockerfile`; canonical Python for agent app is `apis/agent/src/agent/` (Render/Compose **dockerContext `.`**). Shared `src.*` modules ship from `apis/gateway/src/` (see **PM-008**); `apis/gateway/src/agent` is a **symlink** → `../../agent/src/agent` so one import graph. |
| PM-008 | `backend/` (gateway image / gateway entry) | `apis/gateway/` | gateway | done | repo | | **T016**: `apis/gateway/Dockerfile.gateway`, `pyproject.toml`, `uv.lock`, `tests/`, `scripts/`, and shared `src/` (minus physical `agent/` package dir — replaced by symlink). **T015**: [artifacts/backend-split-inventory.md](./backend-split-inventory.md). |
| PM-009 | `packages/openapi-clients/` | `clients/apis/*` (per API) | clients | planned | TBD | | Split gateway / agent / data-management client trees to match FR-005 |
| PM-010 | _(extracted DB helpers from APIs)_ | `packages/python/db/` | packages | planned | TBD | | FR-004; see **Shared** table in [artifacts/backend-split-inventory.md](./backend-split-inventory.md) (`src/services/db/` + runtime callers). |
| PM-011 | `render.yaml` | `render.yaml` (root) OR `infra/` + pointer | infra | done | repo | | **Current**: root `render.yaml` is canonical (FR-008) |
| PM-012 | `specs/` | `specs/` | specs (Spec Kit) | done | repo | | **FR-006**: feature specs stay under `specs/`; identity row—no relocation in this refactor |
| PM-013 | `Makefile` (repo root) | `Makefile` (repo root) | repo-automation | done | repo | | **FR-006** anchor; update relative path strings as **PM-001–PM-008** rows complete |
| PM-014 | `.github/workflows/` | `.github/workflows/` | ci | done | repo | | CI job paths must track path-map rows when deployables move |
| PM-015 | Root `docker-compose*.yml` | Root `docker-compose*.yml` | local-dev | done | repo | | Files: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.microservices.yml`, `docker-compose.render-local.yml`, `docker-compose.render-parity.yml`; update `build` / `context` when **PM-001–PM-003** move |

### T006 — `render.yaml` audit (docker services ↔ path map)

Snapshot of root `render.yaml` **web** services whose `dockerfilePath` / `dockerContext` tie to **PM-001–PM-008** (Modal-only deploys are not in this file).

| Render `name:` | `dockerfilePath` | `dockerContext` | Path-map rows |
|----------------|------------------|-----------------|---------------|
| `vecinita-agent` | `./apis/agent/Dockerfile` | `.` | PM-007 |
| `vecinita-gateway` | `./apis/gateway/Dockerfile.gateway` | `.` | PM-008 |
| `vecinita-frontend` | `./frontends/chat/Dockerfile` | `./frontends/chat` | PM-001 |
| `vecinita-data-management-frontend-v1` | `./frontends/data-management/Dockerfile` | `./frontends/data-management` | PM-002 |
| `vecinita-data-management-api-v1` | `./modal-apps/scraper/Dockerfile` | `./modal-apps/scraper` | PM-003 (DM API image built from scraper tree; path updated with submodule move) |

_Add rows for Makefile targets beyond **PM-013**, workflow subtrees, nested compose under `services/*`, and any `auth/`, `config/`, `deploy/` relocations as they are decided (**PM-016+**)._

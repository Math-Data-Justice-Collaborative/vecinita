# Data Model: Migration & Layout (Feature 018)

This feature does not introduce new application database tables. It defines **repository-level records** used for migration tracking and reviews.

## Entity: Path map row

| Field | Description |
|-------|-------------|
| `row_id` | Stable identifier (e.g., `PM-001`) used by `tasks.md` |
| `legacy_path` | Current repo-relative path (file or directory) |
| `canonical_path` | Target path per spec |
| `deployable` | Optional: gateway, agent, data-management-api, scraper, embedding-modal, model-modal, chat, data-management-frontend, infra, clients, packages |
| `status` | `planned` \| `in_progress` \| `done` \| `blocked` |
| `owner` | Team or role accountable for the row |
| `cutover_date` | Optional; **required** when a row documents legacy-only primary source per **FR-011** (must retire by this date) |
| `notes` | Render wiring, submodule, or Dockerfile caveats |

**FR-011 linkage**: Any production deployable whose primary source remains only on a legacy path after the refactor cutover MUST have a path-map row with `status` (e.g. `planned` / `blocked`), **`owner`**, and **`cutover_date`** populated; [tasks.md](./tasks.md) **T025** closes or extends those rows. Rows without a cutover date are **not** sufficient to justify indefinite legacy-only ownership.

**Validation rules**:

- No two rows may claim the same `canonical_path` as primary owner for the same deployable without an explicit `notes` merge strategy.
- Rows that change Render `dockerfilePath` / `dockerContext` must name the Render service (`name:` from `render.yaml`).

## Entity: Deployable binding

| Field | Description |
|-------|-------------|
| `name` | Logical service name (matches folder under `apis/`, `modal-apps/`, or `frontends/` where applicable) |
| `render_service` | Render `name:` key if applicable, else `N/A` |
| `modal_app` | Modal app identifier if applicable, else `N/A` |
| `canonical_root` | Single folder path owning the deployable |

**Relationship**: One deployable binding references **one** canonical root; path map rows may list many legacy paths converging on that root.

## Entity: Shared package consumer

| Field | Description |
|-------|-------------|
| `package_path` | e.g., `packages/python/db` |
| `consumer_path` | Deployable or client that depends on it |
| `visibility` | `api_only` \| `modal_ok` \| `frontend_ts` — encodes who may import (aligns with spec intent for DB helpers) |

**Validation**: `packages/python/db` consumers default to `apis/*` only unless spec/clarification extends.

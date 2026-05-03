# Quickstart: Monorepo layout refactor (018)

## Before you move code

1. Read [spec.md](./spec.md) (FR-013) and open [artifacts/path-mapping.md](./artifacts/path-mapping.md).
2. Add or update a **row** with a stable `row_id` before opening a move PR.
3. Ensure `make ci` is green on your branch **before** and **after** the move (SC-005).

### When you must update the path map (SC-006)

Normative definition: **[spec.md](./spec.md)** success criterion **SC-006** (trivial vs non-trivial path depth). Update **`artifacts/path-mapping.md`** for any PR that moves or retires a **deployable root** or a **whole subtree** listed under `apis/`, `modal-apps/`, `frontends/`, `clients/apis/`, or (until **PM-009** completes) `packages/openapi-clients/`—including **renames of those roots**. After **T020**, canonical generated client roots are **`clients/apis/<api>/`** per **FR-005**; keep **`PM-009`** and path-map `notes` accurate during transition.

**Trivial** changes that do **not** require a new or updated row: fixing typos in comments, one-off single-file edits outside deployable roots, formatting-only diffs, and dependency bumps that do not relocate directories.

[plan.md](./plan.md) links to the path map in its **Path governance** section; keep that section accurate if the map filename changes.

## Updating the path map

- One row per logical move (directory or important file cluster).
- Set `status` to `done` only when **all** references (Makefile, `render.yaml`, workflows, imports) point at the canonical path for that slice.
- If Render changes: note the exact Render service `name:` in `notes`.

**FR-005 interim / “release cycle”**: Matches [spec.md §Assumptions](./spec.md#assumptions)—count **merges to the default branch** that touch the same consumer layout; after **two** such merges still on a legacy client path, set **`cutover_date`** on the path-map row (FR-011).

## Canonical blueprint (FR-008)

- **Primary**: `render.yaml` at repository root (current standard).
- **Optional**: If you add `infra/`, put non-authoritative fragments there and add a **one-line pointer** in [README.md](../../README.md) or this quickstart—do not create a second “source of truth” blueprint without removing the ambiguity in the same PR.

## Agent / gateway split

Do **not** bulk-rename `backend/` until [research.md](./research.md) section 3 boundary work is reflected in `tasks.md`. Prefer small commits with `git mv`.

## After layout changes

- Regenerate or relocate OpenAPI clients per [research.md](./research.md) section 5.
- Run `make ci` from repo root.
- Update [artifacts/path-mapping.md](./artifacts/path-mapping.md) `status` fields.

## Next command

Execute **`tasks.md`** in dependency order; for automation, **`/speckit.implement`** consumes the same task list (tasks already cite `row_id` in the path map).

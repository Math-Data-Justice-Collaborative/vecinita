# Branch Workflow For Multi-Component Development

This workflow provides a fast way to switch branch context across component repositories when working with a staged monorepo migration.

## Commands

- `make branch-status`
  - Shows branch and dirty state per configured component.

- `make branch-save`
  - Saves current component branch positions.

- `make branch-switch BRANCH=<name>`
  - Tries to check out `<name>` in each component.
  - If `<name>` is not available, falls back to `main`.

- `make branch-restore`
  - Restores branch positions from the last `branch-save` snapshot.

- `make branch-pull [BRANCH=<name>]`
  - Pulls latest commits from `origin` for each component branch.
  - If `BRANCH` is provided, components attempt to switch to that branch first.

- `make branch-sync-main`
  - Shortcut to move all configured components to `main`.

## Dirty Worktrees

By default, components with uncommitted changes are skipped to avoid accidental context loss.

To override:

```bash
FORCE=1 make branch-switch BRANCH=feature/my-change
```

## Configuration

Component definitions live in `run/branch-components.conf`.

Format:

```text
name|relative/path|fallback_branch
```

Example:

```text
data-management|services/data-management-api|main
data-management-frontend|apps/data-management-frontend|main
direct-routing|services/direct-routing|main
```

## Typical Flow

```bash
make branch-save
make branch-switch BRANCH=feature/rag-refactor
# work
make branch-restore
```

This provides a low-friction way to hop between coordinated feature branches during migration work.

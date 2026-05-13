---
name: repo-cleanup
description: Clean up the Vecinita monorepo by deleting unnecessary files, moving misplaced files to their canonical locations per spec 018, refactoring imports, and updating config references. Produces a dry-run audit first and asks for approval before destructive actions. Use when the user asks to clean up the repo, reorganize files, delete junk, enforce monorepo structure, or tidy the repository layout.
disable-model-invocation: true
---

# Repo Cleanup

Systematically clean and reorganize the Vecinita monorepo to match the canonical layout defined in `specs/018-strict-monorepo-layout/spec.md`.

**Safety rule**: Always produce a dry-run report and get user approval before deleting or moving anything.

## Canonical Layout (spec 018)

```
vecinita/
├── apis/                  # Render-deployed HTTP APIs (one child = one service)
│   ├── agent/
│   ├── gateway/
│   └── data-management-api/
├── modal-apps/            # Modal-deployed apps (one child = one app)
│   ├── scraper/
│   ├── embedding-modal/
│   └── model-modal/
├── frontends/             # Render-deployed web UIs (one child = one site)
│   ├── chat/
│   └── data-management/
├── packages/              # Shared libraries (not deployed standalone)
│   ├── python/
│   │   ├── db/
│   │   └── shared-schemas/
│   ├── openapi-clients/
│   └── ...
├── clients/apis/          # Typed HTTP clients per API
├── infrastructure/        # Docker helpers, Render fragments, deploy scripts
├── scripts/               # Repo-level automation
├── specs/                 # Feature specifications
├── docs/                  # Documentation
├── tests/                 # Cross-service / E2E tests
├── .github/               # CI workflows
├── Makefile               # Developer entry point
├── render.yaml            # Canonical deploy blueprint
├── .env.local.example     # Single env example (FR-007)
├── docker-compose*.yml    # Local dev orchestration
└── package.json           # Root workspace
```

## Workflow

Follow these phases in order. Complete each phase fully before moving to the next.

### Phase 1: Audit

Scan the repo and produce a categorized report. Do NOT modify anything yet.

#### 1a. Identify deletable files

Search for files and directories that should not be in the repo:

| Category | How to find | Examples |
|----------|-------------|---------|
| Build artifacts | `dist/`, `build/`, `coverage/`, `playwright-report/`, `test-results/` | `frontends/chat/dist/`, `website/build/` |
| Cache dirs | `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.hypothesis/`, `__pycache__/`, `.docusaurus/` | Root `.hypothesis/`, scattered `__pycache__/` |
| Virtual envs | `.venv/` dirs inside service folders | `apis/gateway/.venv/`, `tests/.venv/` |
| Log files | `*.log`, `logs/` | Root `pytest.log`, `apis/gateway/logs/` |
| Stale one-off docs | Root `*_COMPLETE.md`, `*_IMPLEMENTATION.md`, `*_REPORT.md` that duplicate info in `docs/` or `specs/` | `IMPLEMENTATION_COMPLETE.md`, `PHASES_1_TO_5_COMPLETION_REPORT.md` |
| Stale config | Files superseded by per-service configs | Root `requirements.txt` if services use `pyproject.toml`, root `Dockerfile` if services have their own |
| Node artifacts | `node_modules/` (should be gitignored) | `frontends/chat/node_modules/` |
| Schemathesis reports | `schemathesis-report/` | `apis/gateway/schemathesis-report/` |

Check `.gitignore` — if these are already ignored, note that but still flag committed instances.

#### 1b. Identify misplaced files

Compare the current tree against the canonical layout. Flag anything outside the expected structure:

| Current location | Canonical destination | Rationale |
|------------------|----------------------|-----------|
| Root stale docs (`DATA_MANAGEMENT_SETUP_COMPLETE.md`, etc.) | `docs/reports/` or delete if obsolete | FR-006: docs belong in `docs/` |
| `auth/` at root | `apis/auth/` or `packages/python/auth/` | Depends on whether it's a deployed service or shared lib |
| `config/` at root | `infrastructure/config/` or per-service | Infra config → `infrastructure/` |
| `data/` at root | `infrastructure/data/` or `scripts/data/` | Seed data / fixtures |
| `deploy/` at root | `infrastructure/deploy/` | Deploy scripts → `infrastructure/` |
| `docker/` at root | `infrastructure/docker/` | Docker helpers → `infrastructure/` |
| `run/` at root | `scripts/run/` or delete | Automation scripts |
| `website/` at root | `apps/website/` or `docs-site/` | If deployed, goes under `apps/`; if docs, collocate with `docs/` |
| `apps/` (if empty/vestigial) | Delete or repurpose per spec | Check if anything remains |
| `services/` (if empty/vestigial) | Delete | Successors are `apis/` and `modal-apps/` |
| Root `Dockerfile` | Delete or move to service | Each service owns its Dockerfile |
| `render.blueprint.yaml`, `render.staging.yaml` | `infrastructure/` or consolidate into `render.yaml` | FR-008: single canonical blueprint |
| `runtime.txt` | Delete if unused | Heroku artifact |
| Root shell scripts (`setup.sh`, `setup_local_dev.sh`, `dev-session.sh`) | `scripts/` | FR-010 |

#### 1c. Check the path migration map

Read `specs/018-strict-monorepo-layout/artifacts/path-mapping.md`. For any row with status `planned` or `in-progress`, note that those moves are tracked by the spec and should be coordinated, not duplicated.

#### 1d. Present the audit report

Format the report as three tables:

1. **Delete** — files/dirs to remove (with reason)
2. **Move** — files/dirs to relocate (with source, destination, reason)
3. **Investigate** — ambiguous items needing user input

Ask: "Which items should I proceed with? You can approve all, select specific items, or ask me to investigate further."

### Phase 2: Clean (after approval)

#### 2a. Delete approved files

For each approved deletion:
1. Verify the file/dir is not imported or referenced anywhere (use grep/ripgrep)
2. Check git status to confirm it's tracked (if untracked, just delete; if tracked, `git rm`)
3. Delete it
4. Record what was deleted

#### 2b. Move approved files

For each approved move:
1. Create the destination directory if needed
2. Move the file/dir (`git mv` for tracked files)
3. Search the entire repo for references to the old path:
   - `Makefile` targets and paths
   - `docker-compose*.yml` build contexts and volumes
   - `render.yaml` / `render.*.yaml` dockerfile paths and contexts
   - `.github/workflows/*.yml` paths
   - `package.json` workspace entries
   - `pnpm-workspace.yaml` entries
   - `turbo.json` pipeline entries
   - Python imports (`from old.path import ...`)
   - TypeScript imports (`from "old/path"`)
   - README and doc links
   - `.gitmodules` paths
4. Update every reference found
5. Record old path → new path

#### 2c. Update the path migration map

If any moves were made, update `specs/018-strict-monorepo-layout/artifacts/path-mapping.md`:
- Add new rows for moves not already tracked
- Update status of existing rows if completed

### Phase 3: Verify

After all changes:

1. Run `make lint` or equivalent to catch broken imports
2. Run `make typecheck` if available
3. Check that `render.yaml` service paths still resolve
4. Verify docker-compose builds still reference valid paths
5. Run a quick `git diff --stat` to summarize all changes
6. Present a summary of everything done

### Phase 4: Gitignore hardening

Check `.gitignore` covers all artifact patterns found in Phase 1. Add missing patterns:

```gitignore
# Build artifacts
dist/
build/
coverage/
playwright-report/
test-results/

# Caches
.pytest_cache/
.ruff_cache/
.mypy_cache/
.hypothesis/
__pycache__/
.docusaurus/

# Virtual environments
.venv/

# Logs
*.log
logs/

# Schemathesis
schemathesis-report/
```

## Reference files

- Canonical layout spec: [specs/018-strict-monorepo-layout/spec.md](../../../specs/018-strict-monorepo-layout/spec.md)
- Path migration map: [specs/018-strict-monorepo-layout/artifacts/path-mapping.md](../../../specs/018-strict-monorepo-layout/artifacts/path-mapping.md)
- Backend split inventory: [specs/018-strict-monorepo-layout/artifacts/backend-split-inventory.md](../../../specs/018-strict-monorepo-layout/artifacts/backend-split-inventory.md)

## Rules

- **Never delete without asking.** Always present the audit first.
- **Never move a deployable root** (anything under `apis/`, `modal-apps/`, `frontends/`) without checking `render.yaml`, docker-compose, and CI workflows.
- **Respect spec 018 path-map.** If a move is already tracked there with status `planned`, coordinate rather than creating a parallel tracking artifact.
- **One commit per logical batch.** Group related deletions or moves into coherent commits (e.g., "remove build artifacts", "move root docs to docs/").
- **Update all references.** A moved file with stale references is worse than an unmoved file.

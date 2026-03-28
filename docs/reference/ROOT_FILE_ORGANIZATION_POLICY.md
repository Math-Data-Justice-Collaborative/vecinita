# Root File Organization Policy

This policy defines how root-level files are organized and migrated without breaking setup, CI, or developer workflows.

## Goals

- Keep root focused on repository contracts and entry points.
- Move only low-risk files in early phases.
- Maintain backward compatibility with shims for moved scripts.

## Must Stay at Root (Do Not Move)

- `.dockerignore`
- `.env`
- `.env.example`
- `.gitignore`
- `.gitleaks.toml`
- `.gitleaksignore`
- `.gitmodules`
- `.pre-commit-config.yaml`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `LICENSE`
- `README.md`
- `setup.sh`

## Staged Candidates (Move with Compatibility)

### Stage 1 (Low Risk)

- `schema_v1_2026-02-16.sql` -> `supabase/migrations/archive/schema_v1_2026-02-16.sql`
- `upgrade_schema.sql` -> `supabase/migrations/archive/upgrade_schema.sql`

Stage 1 status: completed (migrated on 2026-02-27).

Stage 1.5 status: completed (index/readme migration pointers added).

Stage 1.6 status: completed (`supabase/migrations/archive/README.md` added with archive conventions).

Stage 1.7 status: completed (root `README.md` now distinguishes active migration paths vs archived SQL files).

### Stage 2 (Medium Risk)

- `dev-session.sh` -> `run/dev-session.sh` (keep root wrapper script)
- `setup_local_dev.sh` -> `run/setup_local_dev.sh` (keep root wrapper script)

Stage 2 status: completed (migrated on 2026-02-27 with executable root wrapper shims retained).

### Stage 3 (Conditional, Validate Consumers First)

- `package.json`, `package-lock.json` (root manifests): keep unless root npm workflow is fully retired
- `requirements.txt` (root): keep unless all root Python entrypoints are retired

Stage 3 status: planning + dry-run audit complete. Use `docs/reference/STAGE3_DEPRECATION_CHECKLIST.md` and `docs/reference/STAGE3_DRY_RUN_AUDIT.md` before any move/removal.

## File List Scope

This policy explicitly covers:

`.dockerignore .env .env.example .gitignore .gitleaks.toml .gitleaksignore .gitmodules .pre-commit-config.yaml CHANGELOG.md CONTRIBUTING.md dev-session.sh docker-compose.dev.yml docker-compose.yml LICENSE package-lock.json package.json README.md requirements.txt schema_v1_2026-02-16.sql setup_local_dev.sh setup.sh upgrade_schema.sql`

## Migration Checklist

Before moving any file:

1. Search references in workflows/scripts/docs.
2. Move file to target location.
3. Add root shim or redirect note when needed.
4. Update references.
5. Run impacted tests/scripts.

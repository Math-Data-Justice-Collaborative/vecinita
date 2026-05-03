# Canonical Postgres Corpus Sync

This directory tracks planning and implementation artifacts for feature `017-canonical-postgres-sync`.

## Artifact map

- `spec.md`: source requirements and success criteria.
- `plan.md`: implementation architecture and scope constraints.
- `tasks.md`: execution-ordered task checklist.
- `research.md`: technical decisions and rationale.
- `data-model.md`: canonical entities and invariants.
- `contracts/`: boundary and testing gate contracts.
- `quickstart.md`: validation workflow for contributors.
- `checklists/`: requirements-quality and plan-consistency checklists.
- `artifacts/`: generated validation evidence during implementation.

## Test run mapping

- Pact and contract rerun registry: `.cursor/hooks/registry-contract-pact-tests.json`
- CI workflow impacted-suite routing: `.github/workflows/test.yml`
- Local gate commands:
  - `make test-corpus-sync-impacted`
  - `make test-corpus-sync-full`
  - `make ci`

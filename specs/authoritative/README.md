# Authoritative Spec Documentation

> Auto-generated: 2026-05-11

This directory contains the authoritative documentation for the Vecinita
monorepo, produced by the spec-driven development workflow.

## Contents

| Document | Path | Description |
|----------|------|-------------|
| Dependencies | [dependencies/DEPENDENCIES.md](dependencies/DEPENDENCIES.md) | Full dependency inventory across all services |
| Environments | [environments/ENVIRONMENTS.md](environments/ENVIRONMENTS.md) | Per-service environment variable reference |
| Modal landscape | [modal/current-landscape.md](modal/current-landscape.md) | Current Modal integration state |
| Render landscape | [render/current-landscape.md](render/current-landscape.md) | Current Render integration state |
| Changelog | [changelog/CHANGELOG.md](changelog/CHANGELOG.md) | Spec-driven changelog with task completion |

## Regeneration

To regenerate all documents, use the `create-spec` skill or run each
skill individually:

- `repo-dependencies-doc` → dependencies/
- `env-documentation` → environments/
- `modal-integration-planning` → modal/
- `render-integration-planning` → render/
- `spec-changelog` → changelog/

## Relationship to feature specs

Feature specs live under `specs/NNN-slug-name/`. The documents here are
**cross-cutting authoritative artifacts** that summarize the monorepo
state across all features. Individual feature specs reference these
when they need to understand dependencies, deployment topology, or
integration patterns.

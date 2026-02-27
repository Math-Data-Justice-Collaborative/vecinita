# SQL Archive

This directory stores legacy or superseded SQL files moved out of the repository root during staged organization.

## What belongs here

- Historical schema snapshots
- One-off upgrade scripts preserved for traceability
- SQL artifacts that are no longer the active migration entrypoint

## Naming conventions

- Keep original filenames when migrating existing files for continuity.
- Prefer date-stamped names for new archived items, for example:
  - `schema_v1_2026-02-16.sql`
  - `upgrade_schema_2026-02-27.sql`
- Use lowercase with underscores.

## Handling rules

- Do not run archived SQL in production without validation.
- Treat files here as reference/history unless explicitly promoted.
- If a file is moved here from root, update docs that referenced the old path.

## Current archived files

- `schema_v1_2026-02-16.sql`
- `upgrade_schema.sql`

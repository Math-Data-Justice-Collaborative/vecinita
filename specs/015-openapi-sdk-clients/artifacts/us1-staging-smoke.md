## US1 staging smoke notes (T018)

Date: 2026-04-25
Feature: `015-openapi-sdk-clients`

### Quickstart section 1 (Environment)

- Verified approved connectivity names are documented and wired in templates/manifests:
  - `DATABASE_URL`
  - `RENDER_GATEWAY_URL`
  - `RENDER_AGENT_URL`
  - `DATA_MANAGEMENT_API_URL`
  - `GATEWAY_SCHEMA_URL`
  - `DATA_MANAGEMENT_SCHEMA_URL`
  - `AGENT_SCHEMA_URL`
- Deprecated connection env names were removed from committed examples/manifests in this pass.

### Quickstart section 2 (Regenerate clients)

- `make openapi-codegen` path remains available from root `Makefile`.
- This US1 pass did not regenerate clients (US2 scope), but command wiring is present.

### Quickstart section 3 (Validate contracts)

- Ran full repository gate: `make ci` (PASS) after updates.
- Contract and lint/format checks succeeded on current branch state.

### PR description note for SC-004

- Operator checklist is pending until `T045` lands (`docs/deployment/SC004_STAGING_RELEASE_CHECKLIST.md`).
- Link `specs/015-openapi-sdk-clients/quickstart.md` section 7 (Staging release) in PR.
- Track follow-up in `specs/015-openapi-sdk-clients/tasks.md` item `T045`.

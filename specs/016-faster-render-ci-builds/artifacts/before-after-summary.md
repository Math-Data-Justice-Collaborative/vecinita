# Before/after summary — faster Render builds + CI (016)

## Scope and status

- Phases complete: Setup (T001–T003), Foundational baseline (T004–T005), US1 (T006–T011 + T022), US2 (T012–T015).
- Evidence files: `baseline-pre-optimization.md`, `required-checks-inventory.md`, `post-optimization-snapshot.md`, `fr008-regression-playbook.md`, `engineer-retro-template.md`.
- Remaining measured values are provisional (`N < 20`) until sample windows are filled per FR-001.

## Baseline vs post-optimization links

| evidence type | baseline source | post-change source | status |
|--------------|-----------------|--------------------|--------|
| CI job-level inventory | `artifacts/baseline-pre-optimization.md` section (A) | `artifacts/post-optimization-snapshot.md` (M1 + additional dimensions) | ready for measurement fill-in |
| CI required checks inventory | `artifacts/required-checks-inventory.md` (`baseline_present`) | same file (`post_change_present` + EquivalenceRecord) | complete |
| Render build phase (`backend/Dockerfile`) | `artifacts/baseline-pre-optimization.md` sections T005/T015 | `artifacts/post-optimization-snapshot.md` (M2) | ready for measurement fill-in |

## Improvement claims per canonical change category

The implementation is configured to support the target claim threshold (>=20% median improvement) for the following categories once sampling windows are filled:

- `infrastructure_or_workflow`: CI wall-clock drop from parallel schema checks + uv cache reuse.
- `dependency_or_lockfile`: CI wall-clock drop from uv cache keyed on `backend/uv.lock` + `backend/pyproject.toml`.
- `application_code_typical` (Render build): build-phase drop from tighter backend context (`backend/.dockerignore`) and lockfile-aware dependency layer invalidation.

Until sample medians are populated, these are predicted claims only (not final pass/fail).

## Process follow-ups

- **SC-004 owner**: Platform Eng (CI/Release) — collect >=3 responses using `engineer-retro-template.md` within 14 calendar days.
- **Due date**: 2026-05-13 (14 calendar days from this artifact update).
- **T019 note**: No new build-time env vars or Docker build args introduced in US2; `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` unchanged by design.
- **T021 note**: No new contract or Pact test file paths added; registry update not required.

## T020 CI gate timing

- `make ci` final run duration: **413.5s** (6m 54s) on 2026-04-29.

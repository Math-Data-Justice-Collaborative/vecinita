# Branch protection checklist (019 CI attestation gate)

Human steps on GitHub after the workflow lands (see `research.md` R-007).

## Required status check name

- Workflow: `.github/workflows/ci-attestation-gate.yml` (`CI attestation gate`)
- Job id: `attestation-gate` (display name: **attestation-gate**)
- In GitHub **Settings → Branches → Branch protection** for `main` / `develop`, set **Status checks that are required** to include the check reported for this job (typically `attestation-gate` or `CI attestation gate / attestation-gate`, depending on GitHub UI version).

## Demote prior merge-blocking jobs

- Remove **required** status from hosted workflows that only re-ran the same substantive checks as the manifest (per **FR-010** / Option A). They may stay as **optional** signal.
- **Advisory:** You may keep `.github/workflows/test.yml` (or similar) running on pull requests **without** requiring it for merge, for triage and parity signal—no deletion required unless maintainers choose to simplify.

## Verification

1. Open a test PR that deletes `.ci/ci-attestation.json` → required gate fails (`missing_file`).
2. Restore a valid pair → gate passes.

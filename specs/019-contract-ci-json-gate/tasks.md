# Tasks: Contract-based CI via local test attestation

**Input**: Design documents from `/specs/019-contract-ci-json-gate/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Optional contract coverage for the validator in the Polish phase (validator behavior is specified in FR-005–FR-009 and category strings in FR-009).

**Organization**: Phases follow user story priority (US1 & US2 are P1; US3 is P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no ordering dependency within the same checkpoint)
- **[Story]**: `[US1]`, `[US2]`, `[US3]` for user-story phases only

## Phase 1: Setup (shared infrastructure)

**Purpose**: Directories, fixtures, and contributor-facing pointers before manifest and scripts land.

- [x] T001 [P] Add `.ci/README.md` describing committed `.ci/required-checks.json` and `.ci/ci-attestation.json`, trust boundary (Option A), and link to `specs/019-contract-ci-json-gate/spec.md`
- [x] T002 [P] Add validator fixtures under `specs/019-contract-ci-json-gate/fixtures/`: **Attestation** golden files (`attestation-valid.json`, `attestation-stale.json`, `attestation-incomplete.json`, `attestation-failed-check.json`) aligned with `contracts/ci-attestation.schema.json`—pair **`attestation-valid.json`** with **`manifest-valid-minimal.json`** for the happy path; **`attestation-incomplete.json`** omits manifest `id` `make-ci` when validated against that same manifest. **Manifest** golden files per `contracts/required-checks-manifest.md`: `manifest-valid-minimal.json` (single `make-ci` check), `manifest-invalid-duplicate-ids.json` (duplicate `id`), `manifest-invalid-empty-checks.json` (`checks: []`). **T013** copies these paths to temp files as needed; tests MUST cover at least one manifest-parse/shape failure using the manifest fixtures without hand-editing JSON in test code.

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Canonical manifest and validator **must** exist before user stories; no story work before this checkpoint.

**⚠️ CRITICAL**: User Story phases must not start until this phase completes.

- [x] T003 Add initial committed manifest at `.ci/required-checks.json` per `specs/019-contract-ci-json-gate/contracts/required-checks-manifest.md` including stable id `make-ci` with command `make ci` (constitution / research R-008 / spec FR-011)
- [x] T004 Implement `scripts/ci/ci_attestation_validate.py` to load `.ci/required-checks.json` and `.ci/ci-attestation.json` (CLI flags `--manifest`, `--attestation`, `--max-age-hours` default 48): validate **manifest** first per **FR-005** manifest clauses and `specs/019-contract-ci-json-gate/contracts/required-checks-manifest.md` (UTF-8, parse, duplicate `id`, non-empty `checks`, required fields), then **attestation** per `specs/019-contract-ci-json-gate/contracts/ci-attestation.schema.json` (research R-002) including **FR-003 v1 strict shape** (`additionalProperties: false`), then freshness (FR-006), then manifest id coverage in `checks` (FR-007); stderr MUST use **FR-009** categories and prefix or substrings indicating **manifest** vs **attestation** per spec FR-005
- [x] T005 Add `ci-attestation-validate` target to root `Makefile` invoking `python3 scripts/ci/ci_attestation_validate.py` with default paths `.ci/ci-attestation.json` and `.ci/required-checks.json`

**Checkpoint**: Foundation ready — manifest + validator + local validate target exist.

---

## Phase 3: User Story 1 — Developer produces a fresh attestation (Priority: P1) 🎯 MVP (part 1)

**Goal**: Local workflow writes `.ci/ci-attestation.json` with `run_id`, `generated_at`, and per-manifest check outcomes; failures do not claim full success.

**Independent Test**: Run `make ci-attestation` on a branch where all manifest commands pass; confirm `.ci/ci-attestation.json` lists every manifest `id` as `passed` with UUID `run_id` and ISO `generated_at`. Run with a forced failing command and confirm non-success behavior per spec acceptance scenario 2.

### Implementation for User Story 1

- [x] T006 [US1] Implement `scripts/ci/ci_attestation_generate.py` to read `.ci/required-checks.json`, execute each `command` from repository root with `subprocess` using `set -euo pipefail`-equivalent failure semantics, build `checks[]` with `passed`/`failed`, write `.ci/ci-attestation.json` with `format_version: 1`, UUID `run_id`, ISO-8601 UTC `generated_at`, optional `git_head` from `git rev-parse --short HEAD`, exit nonzero if any check failed
- [x] T007 [US1] Add `ci-attestation` target to root `Makefile` that runs `python3 scripts/ci/ci_attestation_generate.py` with default manifest/attestation paths under `.ci/`
- [x] T008 [US1] Generate and commit a fresh `.ci/ci-attestation.json` at repository root (run `make ci` then `make ci-attestation` on a clean tree) so the first PR enabling the gate includes valid seed evidence

**Checkpoint**: Contributors can refresh the attestation locally and commit it.

---

## Phase 4: User Story 2 — Central integration rejects invalid, stale, or incomplete gate files (manifest + attestation) (Priority: P1) 🎯 MVP (part 2)

**Goal**: Exactly **one** GitHub Actions job validates the **committed manifest and attestation** at `.ci/required-checks.json` and `.ci/ci-attestation.json` (no hosted re-run of manifest commands).

**Independent Test**: Push branches where `.ci/required-checks.json`, `.ci/ci-attestation.json`, or both are varied (missing, invalid shape, stale, incomplete `checks`, failed status, or valid pair) to confirm the job fails for each negative case and passes only when **both** files satisfy the spec—aligned with `spec.md` User Story 2 acceptance scenarios 1–7.

### Implementation for User Story 2

- [x] T009 [US2] Create `.github/workflows/ci-attestation-gate.yml` with a **single** job on `ubuntu-22.04`, triggers `pull_request` and `push` to `main`/`develop`, checks out default depth sufficient to read `.ci/*`, runs `python3 scripts/ci/ci_attestation_validate.py` with `CI_ATTESTATION_MAX_AGE_HOURS` env (default 48), no matrix, no secondary jobs in that workflow file
- [x] T010 [US2] *(Optional maintainer ergonomics, not required by spec FRs.)* Add `workflow_dispatch` inputs to `.github/workflows/ci-attestation-gate.yml` for optional `max_age_hours` override (maps to validator flag) for manual debugging

**Checkpoint**: CI enforces **manifest and attestation** presence, shape/schema, freshness, and completeness (FR-005–FR-007).

---

## Phase 5: User Story 3 — Maintainers evolve the required-check contract safely (Priority: P2)

**Goal**: Changing `.ci/required-checks.json` forces new attestations; validator and generator stay aligned.

**Independent Test**: Add a dummy second check to manifest in a scratch branch; confirm `make ci-attestation-validate` fails until `make ci-attestation` is rerun and attestation lists the new `id` as `passed`.

### Implementation for User Story 3

- [x] T011 [US3] Extend `CONTRIBUTING.md` or `TESTING_DOCUMENTATION.md` with a “CI attestation gate” section: how to run `make ci-attestation`, Option A risks (forks, drift), and steps to add/rename/remove manifest checks with link to `specs/019-contract-ci-json-gate/quickstart.md`
- [x] T012 [US3] Update `specs/019-contract-ci-json-gate/quickstart.md` so command names and paths match landed `Makefile` targets and workflow filename in `.github/workflows/ci-attestation-gate.yml`

**Checkpoint**: Maintainer workflow for manifest evolution is documented and consistent with code.

---

## Phase 6: Polish & cross-cutting concerns

**Purpose**: Automated regression for validator, registry alignment, operational migration notes.

- [x] T013 [P] Add `apis/gateway/tests/contracts/test_ci_attestation_validate_contract.py` subprocess-invoking `scripts/ci/ci_attestation_validate.py` using **`specs/019-contract-ci-json-gate/fixtures/manifest-*.json`** and **`attestation-*.json`** (copy to temp paths when the CLI requires writable pairs), asserting exit codes and stderr contain FR-009 **primary category** substrings for both manifest-side and attestation-side failures
- [x] T014 [P] Append registry entry to `.cursor/hooks/registry-contract-pact-tests.json` for `apis/gateway/tests/contracts/test_ci_attestation_validate_contract.py` with the repo-standard `uv run pytest …` command
- [x] T015 Add `specs/019-contract-ci-json-gate/artifacts/branch-protection-checklist.md` listing exact GitHub **required status check** name from `.github/workflows/ci-attestation-gate.yml` job id and steps to remove prior merge-blocking checks (per `specs/019-contract-ci-json-gate/research.md` R-007; human action on GitHub settings)
- [x] T016 [P] Add advisory note in `specs/019-contract-ci-json-gate/plan.md` or `artifacts/branch-protection-checklist.md` describing optional retention of `.github/workflows/test.yml` as non-required workflow for triage (no code deletion required in this feature unless maintainers explicitly choose)

---

## Phase 7: Success-criteria evidence (SC-001, SC-002, SC-003, SC-004)

**Purpose**: Close measurable success criteria from `spec.md` that require documented trials and review artifacts (including **SC-004** manifest-change detection; **SC-003** via **T019**).

- [x] T017 Add `specs/019-contract-ci-json-gate/artifacts/sc-controlled-trial-runbook.md` containing: (1) **SC-001** procedure for **seven** synthetic cases matching `spec.md` SC-001 letters **(a)–(g)** (missing attestation, missing manifest, invalid manifest, invalid attestation parse/schema, stale, incomplete/failed check, valid pair) with a results table template; (2) **SC-002** log template for ≥20 maintainer-certified regeneration attempts with first-attempt pass/fail column; (3) **SC-004** procedure row: add a new manifest `id`, push commit **without** regenerating attestation, record that the **next completed run** of the attestation validation job fails until a fresh attestation exists
- [x] T018 Maintain `specs/019-contract-ci-json-gate/artifacts/sc-success-criteria-evidence.md` with an **implementation / automation baseline**, explicit **Pending** rows for human SC-001 / SC-002 / SC-004 trials (use `sc-controlled-trial-runbook.md`) and SC-003 reviews; paste completed tables or links when trials finish (post–branch-protection rollout)
- [x] T019 [US3] Add the **SC-003** five-question documentation-only review checklist and reviewer rules (30 minutes, three independent reviewers who did not author the gate docs, ≥4 of 5 correct per reviewer) to the same contributor doc as `T011` (`CONTRIBUTING.md` or `TESTING_DOCUMENTATION.md`), with answer key maintained in-repo

---

## Dependencies & execution order

### Phase dependencies

- **Phase 1 (Setup)**: No prerequisites.
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks all user stories**.
- **Phase 3 (US1)**: Depends on Phase 2 (needs manifest `T003` and validate script for local sanity optional; strictly needs `T003` before generator).
- **Phase 4 (US2)**: Depends on Phase 2 (`T004` validator) and should follow `T008` so default branch has a valid attestation when workflow enables (or coordinate: enable workflow same PR as seed attestation — `T008` before `T009` recommended).
- **Phase 5 (US3)**: Depends on Phases 3–4 (stable command names).
- **Phase 6 (Polish)**: Depends on validator and fixtures (`T002`, `T004`). Complete **T015** before parallel polish work that needs the final workflow job id; land **T013** before declaring the feature production-complete (constitution / automated test expectation for validator risk).
- **Phase 7 (SC evidence)**: Depends on **T011**/`T012` for accurate doc cross-references; **T019** extends the contributor section from **T011**. **T017** may start after **T004**; **T018** after **T017** and a working gate on a test branch.

### User story dependencies

- **US1**: After Foundational; no dependency on US2/US3.
- **US2**: After Foundational; logically after US1 seed attestation `T008` to avoid first-run red CI on `main`.
- **US3**: After US1/US2 for accurate docs.

### Parallel opportunities

- **Phase 1**: `T001` and `T002` in parallel.
- **Phase 2**: Sequential: `T003` → `T004` → `T005` (same script evolves).
- **Phase 6**: **Order:** complete **T015** first (exact required check name). Then run **T013** (requires `T002`, `T004`), then **T014** (registry; after `T013` file exists). **T016** may run in parallel with **T013** once **T015** is done (different paths). Do not skip **T013** for production sign-off.
- **Phase 7**: **T017** then **T018** sequentially; **T019** after **T011** (can parallel **T017** with Phase 6 after `T004` if staffed).

### Within each user story

- US1: Implement `scripts/ci/ci_attestation_generate.py` (`T006`) before Makefile target (`T007`); `T008` last.
- US2: Workflow (`T009`) then dispatch ergonomics (`T010`).

---

## Parallel example: Phase 1

```bash
# Run together:
# T001 — write .ci/README.md
# T002 — add fixtures under specs/019-contract-ci-json-gate/fixtures/
```

---

## Parallel example: User Story 1 + validator hardening (after T003)

If `T004` already parses manifest: optional parallel work is limited because both touch validation semantics; keep generator (`T006`) immediately after manifest stable.

---

## Implementation strategy

### MVP (merge-blocking path)

1. Complete Phase 1 and Phase 2 (`T001`–`T005`).
2. Complete US1 (`T006`–`T008`) so `.ci/ci-attestation.json` exists on the branch.
3. Complete US2 (`T009`–`T010`) and validate on a test PR.
4. **Stop and validate** independently: missing, stale, invalid, or incomplete **manifest or attestation** combinations fail per FR-005–FR-007; a **valid manifest + attestation** pair passes.

### Incremental delivery

1. Add US3 docs (`T011`–`T012`) before flipping branch protection.
2. Add Polish contract test + registry (`T013`–`T014`) so schema drift is caught.
3. Execute human checklist `T015` (and optional advisory `T016`) before declaring rollout complete.
4. Complete Phase 7 (`T017`–`T019`) to satisfy **SC-001, SC-002, SC-003, and SC-004** evidence requirements in `spec.md` (SC-003 checklist in **T019**).

### Parallel team strategy

- Developer A: Phase 2 validator (`T004`–`T005`) + US2 workflow (`T009`–`T010`).
- Developer B: Phase 1 + US1 generator (`T006`–`T007`) + seed `T008`.
- Developer C: US3 docs (`T011`–`T012`) + Polish tests (`T013`–`T014`) after `T004` lands.
- Phase 7 / evidence: **T017**–**T018** (runbook + filled evidence) after working gate on a test branch; **T019** after **T011** (can parallel **T017** with Phase 6 once **T004** and **T015** are clear).

---

## Notes

- Do not flip GitHub **required checks** until `T015` is filled with the exact job/check name from the landed workflow.
- `make ci` in the manifest may be long-running; document machine requirements in `T011`.
- Seed attestation `T008` must be regenerated whenever manifest changes before merge.
- **SC-002 scale:** one successful `make ci` + `make ci-attestation` cycle seeds **one** certified attempt; the SC-002 trial uses the **T017** log template across many PRs or a dedicated batch process—do not conflate `T008` alone with the full 20-attempt requirement.

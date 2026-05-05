# Plan Consistency Checklist: Canonical Postgres Corpus Sync

**Purpose**: Validate consistency, validity, and traceability across `spec.md`, `plan.md`, and `tasks.md` before implementation.  
**Created**: 2026-04-29  
**Feature**: [spec.md](../spec.md)

**Note**: This checklist validates requirement quality in planning artifacts, not runtime behavior.

## Requirement Completeness

- [x] CHK001 Are all mandatory constraints from `spec.md` (canonical `DATABASE_URL`, no production placeholders, read-only documents tab) explicitly represented in `plan.md`? [Completeness, Spec §FR-001/FR-002b/FR-003]
- [x] CHK002 Does `plan.md` fully cover both integration boundaries defined in the spec without omitting ownership or verification expectations? [Completeness, Spec §FR-004/FR-005]
- [x] CHK003 Are all required test layers (pact, contract, integration, system) defined as first-class planning obligations rather than implicit assumptions? [Completeness, Spec §FR-007/FR-008]
- [x] CHK004 Does `tasks.md` include tasks for each declared artifact in `plan.md` Phase 1 outputs (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) where follow-through is required? [Completeness, Plan §Phase 1]

## Requirement Clarity

- [x] CHK005 Is the “canonical source” requirement worded unambiguously so there is no alternate interpretation of allowed production data sources? [Clarity, Spec §FR-001/FR-003]
- [x] CHK006 Is read vs write ownership between the two frontends clearly specified in both plan summary and story tasks without vague terms? [Clarity, Spec §FR-002a/FR-002b, Plan §Summary]
- [x] CHK007 Are CI gate expectations in `tasks.md` expressed with concrete outcomes (required suites, blocking behavior) rather than broad “run tests” language? [Clarity, Tasks §Phase 5/Phase 6]
- [x] CHK008 Is the 30-second divergence requirement stated as a measurable release criterion consistently across spec, plan, and tasks? [Clarity, Spec §FR-006b/SC-004]

## Requirement Consistency

- [x] CHK009 Do the boundaries and allowed operations in `data-model.md` match the boundary ownership statements in `contracts/corpus-sync-boundary-contract.md`? [Consistency, Data Model §Boundary Contract, Contract §Boundary Ownership]
- [x] CHK010 Are suite gating statements in `contracts/testing-gates-matrix.md` consistent with `tasks.md` CI enforcement tasks and with `spec.md` FR-008/FR-008a/FR-008b? [Consistency, Spec §FR-008]
- [x] CHK011 Do task phases preserve the same priority ordering and independence intent as user stories in `spec.md`? [Consistency, Spec §User Stories, Tasks §Phase 3-5]
- [x] CHK012 Are “fail-closed” outage requirements described consistently in spec acceptance scenarios, contract language, and story tasks? [Consistency, Spec §US2, Contract §Failure Behavior, Tasks §US2]

## Acceptance Criteria Quality

- [x] CHK013 Are acceptance criteria for each user story stated in ways that can be objectively evaluated from requirements language alone? [Measurability, Spec §User Stories]
- [x] CHK014 Do planning artifacts define what constitutes “release-blocking” in a way reviewers can evaluate without implementation guesses? [Acceptance Criteria, Spec §FR-006c/FR-008, Plan §Technical Context]
- [x] CHK015 Is the required pass condition (`make ci` from repository root) consistently treated as mandatory readiness criteria across plan, tasks, and quickstart? [Consistency, Plan §Technical Context, Tasks §Notes, Quickstart §6]

## Scenario Coverage

- [x] CHK016 Are primary, alternate, exception, and outage scenarios all represented in requirements artifacts for both boundaries? [Coverage, Spec §US1/US2/Edge Cases]
- [x] CHK017 Are recovery-path requirements defined for partial cross-service failure (write succeeds but projection/read path lags or fails)? [Gap, Spec §Edge Cases]
- [x] CHK018 Are non-functional test scenarios (freshness SLO, suite coverage gates) treated as explicit requirements and not implied constraints? [Coverage, Spec §FR-006b/FR-008a]

## Edge Case Coverage

- [x] CHK019 Does the plan define requirement-level handling for stale cache/display risk during upstream outage events? [Edge Case, Spec §FR-003a]
- [x] CHK020 Are concurrency and timing edge requirements (simultaneous updates, delayed visibility) explicitly captured or intentionally excluded? [Gap, Spec §Edge Cases]
- [x] CHK021 Are requirement expectations defined for contract-compatible but semantically divergent responses across services? [Edge Case, Spec §Edge Cases]

## Dependencies & Assumptions

- [x] CHK022 Are assumptions in `spec.md` (auth unchanged, existing filtering semantics, provisioned `DATABASE_URL`) validated or linked to verification tasks? [Assumption, Spec §Assumptions]
- [x] CHK023 Are external dependency requirements (DM API, gateway API, Postgres availability) explicitly mapped to impacted-suite test gates? [Dependency, Contracts §Testing Gates Matrix]
- [x] CHK024 Is any requirement relying on undocumented environmental behavior (e.g., hidden fallback data source) surfaced as a gap? [Gap, Plan §Constraints]

## Ambiguities & Conflicts

- [x] CHK025 Do any plan or tasks statements conflict with “no mocks/placeholders in production” by using ambiguous terms like “fallback,” “cached,” or “fixture” without scope qualifiers? [Ambiguity, Conflict, Spec §FR-003]
- [x] CHK026 Is there any mismatch between “independent story validation” claims and cross-story dependencies that would block isolated delivery? [Conflict, Tasks §Dependencies]
- [x] CHK027 Are per-suite threshold requirements defined with enough specificity to avoid inconsistent reviewer interpretation? [Ambiguity, Spec §FR-008a]
- [x] CHK028 Is a clear traceability path present from each high-risk requirement to at least one concrete task and one planned validation artifact? [Traceability, Spec §FR-001..FR-009, Tasks §Phase 3-6]

## Notes

- Items are quality checks for requirement artifacts and planning consistency.
- Mark complete with `[x]` and capture findings inline under each item as needed.

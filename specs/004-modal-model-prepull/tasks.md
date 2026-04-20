# Tasks: Startup Model Pre-Pull and Lifecycle Extensibility for Modal Model Service

**Input**: Design documents from `/specs/004-modal-model-prepull/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Unit and integration tests are required by the plan and contracts for lifecycle/connection reliability.  
**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on unfinished tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`)
- Exact file paths are included in every task

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared scaffolding and documentation anchors for lifecycle extensibility work.

- [X] T001 Create lifecycle runtime module skeleton in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T002 Add lifecycle configuration placeholders and defaults in `services/model-modal/src/vecinita/config.py`
- [X] T003 [P] Add internal lifecycle event payload schema helpers in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T004 [P] Add lifecycle design summary section in `services/model-modal/README.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared building blocks required by all stories.

**⚠️ CRITICAL**: No user story implementation starts until this phase is complete.

- [X] T005 Implement lifecycle plugin/registry data structures and phase ordering in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T006 Implement lifecycle plugin registration validation (required, duplicate order, invalid phase) in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T007 Implement structured lifecycle event helpers with correlation IDs in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T008 Wire lifecycle settings (`retry_limit`, `retry_backoff_ms`, registry id/default strategy) in `services/model-modal/src/vecinita/config.py`
- [X] T009 Refactor shared startup/shutdown helpers to call lifecycle primitives in `services/model-modal/src/vecinita/app.py`
- [X] T010 Add foundational unit tests for registry validation and event helpers in `services/model-modal/tests/test_app_runtime.py`

**Checkpoint**: Lifecycle framework is ready for story-specific behavior.

---

## Phase 3: User Story 1 - Ensure default model is ready before traffic (Priority: P1) 🎯 MVP

**Goal**: Service preloads default model before readiness and avoids redundant full download on warm startup.

**Independent Test**: Cold-start startup flow reaches ready state only after successful preload; warm-start flow skips full re-download when cache is valid.

### Tests for User Story 1

- [X] T011 [P] [US1] Add unit tests for preload-required readiness gating in `services/model-modal/tests/test_app_runtime.py`
- [X] T012 [P] [US1] Add unit tests for cache-hit skip-pull behavior in `services/model-modal/tests/test_models_runtime.py`
- [X] T013 [US1] Add integration test for cold-start preload-before-ready path in `services/model-modal/tests/test_container_setup.py`
- [X] T014 [US1] Add integration test for warm-start no-full-redownload path in `services/model-modal/tests/test_container_setup.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement startup phase hook execution and readiness gating in `services/model-modal/src/vecinita/app.py`
- [X] T016 [US1] Implement cache artifact presence/integrity checks for startup path in `services/model-modal/src/vecinita/app.py`
- [X] T017 [US1] Implement default startup strategy mapping to cache-preserving behavior in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T018 [US1] Emit preload start/success/failure events with correlation metadata in `services/model-modal/src/vecinita/app.py`

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Allow model selection per deployment (Priority: P2)

**Goal**: Operators can configure which model is preloaded on startup without code edits.

**Independent Test**: Two configurations with different model IDs preload the selected model and serve with startup-ready semantics.

### Tests for User Story 2

- [X] T019 [P] [US2] Add unit tests for model-id resolution from deployment config in `services/model-modal/tests/test_models_runtime.py`
- [X] T020 [P] [US2] Add unit tests for invalid/unsupported configured model IDs in `services/model-modal/tests/test_app_runtime.py`
- [X] T021 [US2] Add integration test for environment-specific model selection behavior in `services/model-modal/tests/test_container_setup.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement startup model selection from configuration with validation in `services/model-modal/src/vecinita/config.py`
- [X] T023 [US2] Update preload flow to use configured startup model consistently across lifecycle hooks in `services/model-modal/src/vecinita/app.py`
- [X] T024 [US2] Update health/reporting output to expose active startup model context in `services/model-modal/src/vecinita/api/routes.py`
- [X] T025 [US2] Document deployment model-selection configuration in `services/model-modal/README.md`

**Checkpoint**: US2 is independently functional and testable with US1 intact.

---

## Phase 5: User Story 3 - Fail fast on invalid model configuration (Priority: P3)

**Goal**: Startup applies bounded retries and fails deterministically with actionable errors; teardown runs in deterministic order with explicit failure reporting.

**Independent Test**: Invalid model/source failures exhaust retry budget and fail startup clearly; shutdown executes teardown hooks in configured order and preserves reusable cache.

### Tests for User Story 3

- [X] T026 [P] [US3] Add unit tests for bounded retry and fail-fast behavior in `services/model-modal/tests/test_app_runtime.py`
- [X] T027 [P] [US3] Add unit tests for deterministic teardown hook order in `services/model-modal/tests/test_models_runtime.py`
- [X] T028 [P] [US3] Add unit tests for teardown failure observability and non-silent reporting in `services/model-modal/tests/test_app_runtime.py`
- [X] T029 [US3] Add integration test for transient connection failure then retry exhaustion in `services/model-modal/tests/test_container_setup.py`
- [X] T030 [US3] Add integration test for shutdown preserving cache and cleaning temp artifacts in `services/model-modal/tests/test_container_setup.py`
- [X] T031 [US3] Add integration test for storage-capacity exhaustion during model pull and deterministic failure classification in `services/model-modal/tests/test_container_setup.py`
- [X] T032 [US3] Add integration test for omitted startup model configuration fallback or deterministic failure behavior in `services/model-modal/tests/test_container_setup.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement bounded retry with backoff and fail-fast transition to failed startup state in `services/model-modal/src/vecinita/app.py`
- [X] T034 [US3] Implement teardown phase execution with deterministic ordering and explicit error surfacing in `services/model-modal/src/vecinita/lifecycle.py`
- [X] T035 [US3] Integrate teardown lifecycle invocation into runtime shutdown path in `services/model-modal/src/vecinita/app.py`
- [X] T036 [US3] Add failure classification helpers for transient vs permanent startup connection errors in `services/model-modal/src/vecinita/models/ollama.py`
- [X] T037 [US3] Emit retry/teardown/plugin-validation lifecycle events in `services/model-modal/src/vecinita/app.py`
- [X] T038 [US3] Enforce lifecycle error payload fields (`error_code`, `failure_phase`, `attempt_count`, `recommended_operator_action`) in startup failure paths in `services/model-modal/src/vecinita/app.py`
- [X] T039 [US3] Implement explicit retry-window computation (`retry_limit * retry_backoff_ms`) and termination guard in `services/model-modal/src/vecinita/app.py`

**Checkpoint**: US3 is independently functional and testable with US1/US2 preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, contracts alignment, and full validation.

- [X] T040 [P] Align implementation notes with lifecycle and connection contracts in `specs/004-modal-model-prepull/contracts/lifecycle-plugin-contract.md`
- [X] T041 [P] Align implementation notes with connection testing contract in `specs/004-modal-model-prepull/contracts/connection-testing-contract.md`
- [X] T042 Update verification and operator runbook steps in `specs/004-modal-model-prepull/quickstart.md`
- [X] T043 Run and document full model-modal test suite results in `services/model-modal/README.md`
- [X] T044 Run repository CI gate and capture pass confirmation in `specs/004-modal-model-prepull/quickstart.md`
- [X] T045 Add lifecycle event schema completeness tests (required fields across all event types/phases) in `services/model-modal/tests/test_app_runtime.py`
- [X] T046 Add startup-to-ready latency measurement validation task and acceptance evidence capture in `services/model-modal/tests/test_container_setup.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all stories.
- **Phase 3 (US1)**: Depends on Phase 2; MVP.
- **Phase 4 (US2)**: Depends on Phase 2 and integrates with US1 startup flow.
- **Phase 5 (US3)**: Depends on Phase 2; validates failure and teardown flows across US1/US2 behavior.
- **Phase 6 (Polish)**: Depends on completion of all selected user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after foundational phase.
- **US2 (P2)**: Independent verification path, but reuses US1 startup lifecycle components.
- **US3 (P3)**: Independent verification path for retries/shutdown, but exercises US1/US2 runtime paths.

### Within Each User Story

- Tests should be added before or alongside implementation and must fail first where applicable.
- Runtime lifecycle core changes should land before API/reporting and docs updates.
- Story checkpoint must pass before moving to next priority.

### Parallel Opportunities

- Phase 1 tasks marked `[P]` can run concurrently.
- In Phase 2, event helper and config updates can run parallel after lifecycle module exists.
- In each story, `[P]` unit tests can run concurrently on distinct test files.
- Polish contract/doc updates marked `[P]` can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel test additions:
Task: "T011 [US1] Add unit tests for preload-required readiness gating in services/model-modal/tests/test_app_runtime.py"
Task: "T012 [US1] Add unit tests for cache-hit skip-pull behavior in services/model-modal/tests/test_models_runtime.py"

# Then parallel implementation on separate concerns:
Task: "T016 [US1] Implement cache artifact presence/integrity checks in services/model-modal/src/vecinita/app.py"
Task: "T017 [US1] Implement default startup strategy mapping in services/model-modal/src/vecinita/lifecycle.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1) and validate cold/warm startup acceptance.
3. Demo stable startup-readiness behavior before expanding scope.

### Incremental Delivery

1. Add US1 for startup reliability baseline.
2. Add US2 for operator model-selection flexibility.
3. Add US3 for deterministic failure handling and teardown guarantees.
4. Execute Phase 6 for cross-cutting validation and documentation parity.

### Team Parallel Strategy

1. Pair on foundational lifecycle framework (Phase 2).
2. Split US2 config/reporting and US3 retry/teardown work once US1 baseline is stable.
3. Rejoin for final integration and CI verification.

---

## Notes

- All tasks use required checklist format with task ID, optional `[P]`, optional `[US#]`, and exact path.
- User story tasks are independently testable with explicit checkpoints.
- Test coverage is intentionally explicit because plan/contracts require unit and integration tests for connection paths.

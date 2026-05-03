# Tasks: Canonical Postgres Corpus Sync

**Input**: Design documents from `specs/017-canonical-postgres-sync/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Tests are explicitly required by the specification (pact, contract, integration, system, and per-suite coverage gates).

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no blocking dependency)
- **[Story]**: User story label (`US1`, `US2`, `US3`)
- Every task includes an explicit file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared scaffolding for canonical DB checks and multi-suite test orchestration.

- [X] T001 Create feature documentation index and test-run mapping in `specs/017-canonical-postgres-sync/README.md`
- [X] T002 Add feature-specific test suite commands to `Makefile`
- [X] T003 [P] Add pact/contract test registry entries for new or renamed tests in `.cursor/hooks/registry-contract-pact-tests.json`
- [X] T004 [P] Add CI impacted-suite routing skeleton for this feature in `.github/workflows/test.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish cross-cutting invariants that all stories depend on.

**CRITICAL**: No story implementation starts until this phase is complete.

- [X] T005 Implement canonical `DATABASE_URL` guard utility for corpus services in `backend/src/utils/corpus_db_guard.py`
- [X] T006 [P] Integrate canonical DB guard into gateway startup/config path in `backend/src/config.py`
- [X] T007 [P] Integrate canonical DB guard into data-management API startup/config path in `apis/data-management-api/apps/backend/vecinita_dm_api/app.py`
- [X] T008 Add foundational canonical-source policy contract scaffold in `backend/tests/contracts/test_corpus_source_policy_contract.py`
- [X] T009 Add test data seeding helper for deterministic corpus sync scenarios in `backend/tests/integration/helpers/corpus_seed.py`
- [X] T010 Add suite-impact classification utility used by CI gating in `scripts/ci/impacted_corpus_test_suites.py`

**Checkpoint**: Foundational guards, seed utilities, and CI impact mapping are in place.

---

## Phase 3: User Story 1 - Canonical corpus parity across experiences (Priority: P1) 🎯 MVP

**Goal**: Ensure both DM frontend and frontend documents tab show synchronized canonical corpus data with correct write/read ownership.

**Independent Test**: Seed canonical corpus data, mutate via DM path, and verify parity + read-only behavior in frontend documents tab.

### Tests for User Story 1

- [X] T011 [P] [US1] Add DM frontend consumer pact coverage for canonical corpus list/read models in `apps/data-management-frontend/tests/pact/dm-api.pact.test.ts`
- [X] T012 [P] [US1] Add gateway consumer pact coverage for documents tab corpus reads in `frontend/tests/pact/chat-gateway.pact.test.ts`
- [X] T013 [P] [US1] Add provider-side contract assertion for gateway corpus projection consistency in `backend/tests/contracts/test_gateway_corpus_projection_contract.py`
- [X] T014 [P] [US1] Add integration test for persisted write-to-read parity across DM API and gateway in `backend/tests/integration/test_corpus_dm_gateway_parity.py`
- [X] T015 [US1] Add Playwright system test for corpus parity across DM UI and documents tab in `frontend/tests/e2e/corpus-parity.spec.ts`
- [X] T016 [US1] Add Playwright system test asserting documents tab cannot issue writes in `frontend/tests/e2e/documents-readonly.spec.ts`

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement DM frontend API client usage for canonical corpus view in `apps/data-management-frontend/src/services/corpusApi.ts`
- [X] T018 [P] [US1] Implement frontend documents tab canonical read adapter in `frontend/src/services/documentsCorpusClient.ts`
- [X] T019 [US1] Enforce read-only corpus operations in documents tab action handlers in `frontend/src/features/documents/actions.ts`
- [X] T020 [US1] Normalize gateway corpus response projection for parity with DM view in `backend/src/api/routers/documents.py`
- [X] T021 [US1] Ensure DM API mutation endpoints update canonical visibility metadata in `apis/data-management-api/apps/backend/vecinita_dm_api/routers/ingest.py`

**Checkpoint**: US1 is independently functional and verifies canonical parity + read-only constraints.

---

## Phase 4: User Story 2 - Production behavior without mocks/placeholders (Priority: P1)

**Goal**: Guarantee production deployments cannot serve corpus data from non-canonical/mock sources and fail closed during canonical-path outages.

**Independent Test**: Run production-profile validation checks and verify outage behavior shows explicit failure state with no stale corpus list.

### Tests for User Story 2

- [X] T022 [P] [US2] Extend source-policy contract tests with production-profile rejection matrix in `backend/tests/contracts/test_corpus_source_policy_contract.py`
- [X] T023 [P] [US2] Add DM API contract test for canonical DB requirement in `apis/data-management-api/tests/test_dm_api_app.py`
- [X] T024 [US2] Add Playwright outage test for fail-closed documents tab behavior in `frontend/tests/e2e/documents-fail-closed.spec.ts`
- [X] T025 [US2] Add integration test validating no stale corpus response on canonical path failure in `backend/tests/integration/test_corpus_fail_closed_behavior.py`

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement frontend outage-state rendering for canonical-path failures in `frontend/src/features/documents/components/DocumentsOutageState.tsx`
- [X] T027 [US2] Wire fail-closed documents tab fallback flow in `frontend/src/features/documents/pages/DocumentsTab.tsx`
- [X] T028 [P] [US2] Add DM API startup/runtime checks to reject placeholder providers in `apis/data-management-api/apps/backend/vecinita_dm_api/routers/health.py`
- [X] T029 [US2] Add gateway-side stale-response suppression guard in `backend/src/services/corpus/corpus_projection_service.py`
- [X] T030 [US2] Document production no-mock/no-placeholder policy in `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`

**Checkpoint**: US2 independently enforces production-safe data source policy and fail-closed UX behavior.

---

## Phase 5: User Story 3 - Contract confidence across system boundaries (Priority: P2)

**Goal**: Enforce bidirectional pact verification, contract/integration/system gates, and impacted-suite coverage policy.

**Independent Test**: Simulate boundary-impacting changes and verify CI requires/passes all affected suite gates (pact, contract, integration, system).

### Tests for User Story 3

- [X] T031 [P] [US3] Add DM API provider pact verification for DM frontend consumer contracts in `apis/data-management-api/tests/pact/test_dm_frontend_provider_verify.py`
- [X] T032 [P] [US3] Add gateway provider pact verification for frontend documents consumer contracts in `backend/tests/pact/test_frontend_documents_provider_verify.py`
- [X] T033 [P] [US3] Add integration test for 30-second write-to-visibility SLO measurement in `backend/tests/integration/test_corpus_visibility_slo.py`
- [X] T034 [US3] Add CI-level test for impacted-suite enforcement logic in `backend/tests/contracts/test_impacted_suite_gate_contract.py`
- [X] T046 [P] [US3] Add integration test for partial-failure recovery/reconciliation behavior in `backend/tests/integration/test_corpus_partial_failure_recovery.py`
- [X] T047 [P] [US3] Add integration test for concurrent corpus update conflict handling in `backend/tests/integration/test_corpus_concurrency_resolution.py`

### Implementation for User Story 3

- [X] T035 [P] [US3] Add suite-specific coverage threshold configuration for pact/contract/integration/system in `.github/workflows/test.yml`
- [X] T036 [US3] Implement impacted-suite gate invocation in `scripts/ci/impacted_corpus_test_suites.py`
- [X] T037 [P] [US3] Add feature coverage/runbook section in `TESTING_DOCUMENTATION.md`
- [X] T038 [US3] Add Playwright command integration for system gate in `frontend/package.json`
- [X] T039 [US3] Add DM frontend pact command integration for CI impacted runs in `apps/data-management-frontend/package.json`
- [X] T040 [US3] Add CI contract-drift enforcement step for schema/contract change synchronization in `.github/workflows/test.yml`
- [X] T048 [US3] Implement projection reconciliation hook for partial-failure recovery path in `backend/src/services/corpus/corpus_projection_service.py`
- [X] T049 [US3] Implement deterministic conflict-resolution policy for near-simultaneous corpus writes in `apis/data-management-api/apps/backend/vecinita_dm_api/routers/ingest.py`

**Checkpoint**: US3 independently validates contract rigor and per-suite CI gating policy.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency, documentation, and end-to-end validation across all stories.

- [X] T041 [P] Update feature quickstart commands with actual task outputs and threshold values from spec in `specs/017-canonical-postgres-sync/quickstart.md`
- [X] T042 Reconcile and finalize contract docs with implemented file paths and CI drift step in `specs/017-canonical-postgres-sync/contracts/testing-gates-matrix.md`
- [X] T043 [P] Add regression notes and known-risk checklist tied to FR-008/FR-009 in `specs/017-canonical-postgres-sync/artifacts/final-validation-notes.md`
- [X] T044 Execute full validation command set and capture SC-001/SC-003 evidence, including 30-day rolling pact/contract pass-rate computation, in `specs/017-canonical-postgres-sync/artifacts/ci-evidence.md`
- [X] T045 Run `make ci` from repo root and resolve any failures before handoff in `Makefile`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all story work.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2; can proceed in parallel with US1 after shared files settle.
- **Phase 5 (US3)**: Depends on Phase 2 and should consume outputs from US1/US2 tests and commands.
- **Phase 6 (Polish)**: Depends on completion of targeted stories.

### User Story Dependencies

- **US1**: Primary MVP, no dependency on other stories after foundation.
- **US2**: Independent of US1 for core policy/outage behavior, but benefits from shared canonical utilities.
- **US3**: Depends on boundary tests and commands introduced in US1/US2.

### Within Each Story

- Add/adjust tests first, confirm they fail for missing behavior.
- Implement service/UI/API changes.
- Re-run relevant suite gates.
- Confirm independent story acceptance criteria.

### Parallel Opportunities

- Setup tasks marked `[P]` can run together (`T003`, `T004`).
- Foundational tasks marked `[P]` can run together (`T006`, `T007`).
- In US1, pact/contract/integration tests (`T011`-`T014`) can run in parallel.
- In US2, policy tests (`T022`, `T023`) can run in parallel.
- In US3, provider pact and recovery/concurrency test tasks (`T031`, `T032`, `T046`, `T047`) can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel test authoring for US1:
Task: "T011 [US1] apps/data-management-frontend/tests/pact/dm-api.pact.test.ts"
Task: "T012 [US1] frontend/tests/pact/chat-gateway.pact.test.ts"
Task: "T013 [US1] backend/tests/contracts/test_gateway_corpus_projection_contract.py"
Task: "T014 [US1] backend/tests/integration/test_corpus_dm_gateway_parity.py"

# Parallel implementation surfaces for US1:
Task: "T017 [US1] apps/data-management-frontend/src/services/corpusApi.ts"
Task: "T018 [US1] frontend/src/services/documentsCorpusClient.ts"
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Setup + Foundational.
2. Deliver US1 parity + read-only ownership.
3. Validate US1 independently before moving on.

### Incremental Delivery

1. Add US2 production-safety and fail-closed guarantees.
2. Add US3 CI/testing gate rigor.
3. Finish polish artifacts and run full root CI.

### Team Parallel Strategy

1. One engineer handles shared foundational guards and CI scaffolding.
2. One engineer handles DM boundary (US1/US3 DM pact/provider paths).
3. One engineer handles frontend documents + Playwright system behavior (US1/US2).

---

## Notes

- Keep backend/frontend contract updates synchronized in the same task.
- Register any new pact/contract test paths in `.cursor/hooks/registry-contract-pact-tests.json`.
- Avoid introducing new committed env example files; use `.env.local.example` only when env examples must change.
- Task completion is not final until root `make ci` succeeds.

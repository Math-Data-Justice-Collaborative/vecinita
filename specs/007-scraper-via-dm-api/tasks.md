# Tasks: Modal function calls + API routing (DM stack & gateway/agent)

**Input**: Design documents from `/specs/007-scraper-via-dm-api/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Included — [spec.md](./spec.md) FR-004–FR-009 / SC-005 and [plan.md](./plan.md) testing table require automated coverage (unit mocks, parity envelopes, gateway/agent policy).

**Organization**: Phases follow user story priorities (two P1 stories, then P2). `apis/data-management-api/apps/backend/` lives in the **data-management-api submodule**; initialize with `git submodule update --init apis/data-management-api` before backend-app tasks.

**Remediation (speckit-analyze)**: Phase 1 tasks **T002→T003** are sequential to avoid conflicting edits to the same inventory file. **FR-004** backend work: **T017** / **T018** implemented in `apis/data-management-api/apps/backend/vecinita_dm_api/` (scraper job proxy + `/embed` / `/predict` via service-clients). **SC-001/SC-005** for the DM SPA: **T013** (Vitest diagnostics). **T012** Schemathesis + public OpenAPI path guard in `backend/tests/integration/test_data_management_api_schema_schemathesis.py`. Edge-case UX (**T033**): DM SPA operator-safe upstream errors (`operatorUpstreamErrors` + `rag-api`); optional tighter alignment with DM API error JSON when handlers evolve. **T038** / **T039** / **T034**–**T036** landed in implementation pass. Final CI is **T040**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies within the same phase)
- **[Story]**: `[US1]` data-management operator path; `[US2]` main frontend→gateway; `[US3]` Modal orchestration + agent + docs

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inventory and alignment before code changes.

**Note**: Complete **T002** before **T003** so two agents do not append to `modal-migration-inventory.md` concurrently.

- [X] T001 Create Modal/HTTP migration inventory (call sites and env vars) in `apis/data-management-api/docs/modal-migration-inventory.md`
- [X] T002 Scan `apps/data-management-frontend/src/app/api/` for direct scraper or Modal hosts and append findings to `apis/data-management-api/docs/modal-migration-inventory.md`
- [X] T003 Scan `frontend/src/` for non-gateway backend hosts used at runtime and append findings to `apis/data-management-api/docs/modal-migration-inventory.md` (run after **T002**)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modal invocation plumbing in DM API **service-clients**; blocks all user stories.

**⚠️ CRITICAL**: No user story work until Modal adapter + client refactors compile and existing package tests pass.

- [X] T004 Extend Modal-related settings in `apis/data-management-api/packages/shared-config/shared_config/__init__.py` (`MODAL_FUNCTION_INVOCATION`, token pair, app/function name fields aligned with `backend/src/services/modal/invoker.py` semantics)
- [X] T005 Implement `apis/data-management-api/packages/service-clients/service_clients/modal_invoker.py` (`Function.from_name`, `remote`/`spawn`, optional `FunctionCall.get`) per `specs/007-scraper-via-dm-api/contracts/dm-api-modal-functions.md`
- [X] T006 [P] Add shared Modal fakes/fixtures for pytest in `apis/data-management-api/packages/service-clients/tests/conftest.py` (create file if absent)
- [X] T007 Refactor `apis/data-management-api/packages/service-clients/service_clients/scraper_client.py` to use `modal_invoker` when Modal invocation is enabled, retaining documented HTTP path for non-production only (`spec.md` FR-009)
- [X] T008 Refactor `apis/data-management-api/packages/service-clients/service_clients/embedding_client.py` with the same Modal-vs-HTTP policy
- [X] T009 Refactor `apis/data-management-api/packages/service-clients/service_clients/model_client.py` with the same Modal-vs-HTTP policy
- [X] T010 Add the `modal` dependency to `apis/data-management-api/packages/service-clients/pyproject.toml` (primary); if `apis/data-management-api/apps/backend/pyproject.toml` exists after submodule init, add `modal` there too or depend on the updated `service-clients` package per submodule layout

**Checkpoint**: `uv run pytest` on `apis/data-management-api/packages/service-clients/tests/` and `apis/data-management-api/tests/parity/` passes (existing tests green).

---

## Phase 3: User Story 1 — Operators manage scraping via DM API only (Priority: P1) 🎯 MVP

**Goal**: Data-management UI talks only to the data-management backend for scraping; backend reaches scraper via Modal functions in prod/staging (`spec.md` FR-001, FR-003, FR-004).

**Independent Test**: From DM UI, run initiate + status scrape flow; network trace shows requests only to DM API host, not scraper `*.modal.run` web entrypoint.

### Tests for User Story 1

- [X] T011 [P] [US1] Extend `apis/data-management-api/packages/service-clients/tests/test_scraper_client.py` to cover Modal invocation branch with mocked `modal.Function` / `from_name`
- [X] T012 [P] [US1] Extend **`backend/tests/integration/test_data_management_api_schema_schemathesis.py`** (primary Schemathesis owner per `Makefile` / CI) for DM OpenAPI scrape/job routes affected by this feature; add tests under `apis/data-management-api/tests/` **only** when the backend harness cannot reach a route (document the split in `apis/data-management-api/docs/modal-migration-inventory.md`)
- [X] T013 [US1] Satisfy **SC-001** / **SC-005** for the DM client: (1) extend Vitest under `apps/data-management-frontend/tests/` and/or `src/app/api/*.test.ts` so API base URL resolves only to the data-management API origin in production-like fixtures and `VITE_*` / env does not embed `modal.run` hosts or `MODAL_TOKEN` patterns; (2) **optionally** extend `apps/data-management-frontend/tests/e2e/*.spec.ts` (e.g. `scraper-journey.spec.ts`) to assert browser requests for primary flows hit the DM API host only when Playwright is in use

### Implementation for User Story 1

- [X] T014 [US1] Update `apps/data-management-frontend/src/app/api/rag-api.ts` so all backend calls use the data-management API base only (no direct scraper or Modal HTTP hosts)
- [X] T015 [P] [US1] Update `apps/data-management-frontend/src/app/api/scraper-config.ts` and `apps/data-management-frontend/src/app/api/scraper-config.test.ts` to remove or redirect direct upstream scraper/Modal hosts toward DM API–backed configuration
- [X] T016 [US1] Update `apps/data-management-frontend/src/app/api/rag-api.test.ts` and `apps/data-management-frontend/tests/pact/dm-api.pact.test.ts` for new routing assumptions
- [X] T017 [US1] Wire DM API **backend app** scraper routes in `apis/data-management-api/apps/backend/vecinita_dm_api/` (`/health` via `ScraperClient.health`, `/jobs` via `ScraperClient.forward_jobs`) using refactored `ScraperClient` / `modal_invoker` for operator scraping endpoints
- [X] T018 [US1] Wire DM API **backend app** embedding and model ingest paths (`POST /embed`, `POST /predict`) in `apis/data-management-api/apps/backend/vecinita_dm_api/` using `EmbeddingClient` and `ModelClient` with the same Modal invocation policy (**FR-004**); workers continue to import these clients from `packages/service-clients` (inventory documents DM HTTP surface); no `*.modal.run` in browser bundles (**SC-005**)

**Checkpoint**: US1 independently testable; SC-001 satisfied for scraping flows; **SC-005** addressed for DM client via **T013**.

---

## Phase 4: User Story 2 — Main app uses gateway only (Priority: P1)

**Goal**: Main SPA backend traffic targets gateway hostname only (`spec.md` FR-002, SC-002, SC-005 for main client).

**Independent Test**: Run primary `frontend/` flows against configured gateway; no requests to internal DM/scraper/model hosts from the browser.

### Tests for User Story 2

- [X] T019 [P] [US2] Add or extend `frontend/tests/` (Vitest) to assert API base resolution uses gateway origin in production-like env fixtures
- [X] T020 [P] [US2] Extend `frontend/tests/e2e/` smoke (if present) to assert gateway hostname for API calls on critical journeys

### Implementation for User Story 2

- [X] T021 [US2] Audit and fix `frontend/src/app/lib/apiBaseResolution.ts` (and related modules) so no code path defaults to non-gateway internal services for prod/staging
- [X] T022 [US2] Add build-time or test-time guard rejecting `import.meta.env` / `VITE_*` patterns that embed `modal.run` hosts or `MODAL_TOKEN` keys in `frontend/` (support `spec.md` SC-005)
- [X] T023 [US2] Update `frontend/README.md` and root `.env.local.example` to document gateway-only client configuration and forbid Modal secrets in frontend bundles

**Checkpoint**: US2 independently testable alongside US1.

---

## Phase 5: User Story 3 — Server-side Modal orchestration + agent (Priority: P2)

**Goal**: DM API orchestrates embedding/model ingest via Modal functions; agent uses function invocation for Modal-hosted model/embedding; docs match (`spec.md` FR-004, FR-006–FR-008; `contracts/gateway-agent-modal-policy.md`).

**Independent Test**: Staging: DM API ingest + agent chat path completes without relying on deprecated Modal **web** entrypoints for those responsibilities; logs include correlation IDs.

### Tests for User Story 3

- [X] T024 [P] [US3] Extend `apis/data-management-api/packages/service-clients/tests/test_embedding_client.py` for Modal invocation branch
- [X] T025 [P] [US3] Extend `apis/data-management-api/packages/service-clients/tests/test_model_client.py` for Modal invocation branch
- [X] T026 [P] [US3] Extend `apis/data-management-api/tests/parity/test_remote_clients_parity.py` for Modal RPC result envelopes vs HTTP fixtures
- [X] T027 [P] [US3] Extend `backend/tests/` (e.g. `backend/tests/test_services/` or `backend/tests/test_api/`) for `enforce_modal_function_policy_for_urls` and agent startup with Modal URLs (`spec.md` FR-008)

### Implementation for User Story 3

- [X] T028 [US3] Verify and complete `backend/src/agent/main.py` startup enforcement so Modal-hosted embedding/model URLs require function invocation (`enforce_modal_function_policy_for_urls`)
- [X] T029 [US3] Align `backend/src/service_endpoints.py` and comments in `backend/src/services/modal/invoker.py` with functions-first production policy (no accidental `*.modal.run` HTTP without invocation)
- [X] T030 [US3] Rewrite `apis/data-management-api/docs/architecture.md` diagrams and bullets to show DM API → Modal Functions (not browser → Modal)
- [X] T031 [US3] Update Render/deployment env documentation (`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` and/or `render.yaml` comments) for DM API `MODAL_*` and `MODAL_FUNCTION_INVOCATION`; include a short **partial rollout** note naming the **authoritative** environment (which base URL / which Modal app env is live) when old scraper web entrypoints may still exist elsewhere
- [X] T032 [P] [US3] Document optional gated live Modal smoke in `specs/007-scraper-via-dm-api/contracts/testing-contracts-matrix.md` and, if approved, add `.github/workflows/` entry
- [X] T033 [US3] Map **embedding/model unavailable** and **hosted platform throttling or cold start** outcomes to operator-safe messages and structured errors in the DM API surface and DM frontend (`spec.md` Edge Cases): adjust API handlers in `apis/data-management-api/apps/backend/` (or shared error helpers) and user-visible copy in `apps/data-management-frontend/` as needed—no raw upstream dumps in UI (**FR-006** alignment)

**Checkpoint**: US3 complete; FR-006 observability preserved in touched paths.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Docs, CI matrix, checklist, runbooks, logging, final verification.

- [X] T034 [P] Validate operator steps in `specs/007-scraper-via-dm-api/quickstart.md` against landed env names and update the doc; **define and link the primary-flow release matrix** for **both** apps (data-management SPA and main SPA): each row = one primary flow with evidence type (Vitest / Playwright / manual) and pointer to test file or checklist ID—this artifact is the **SC-001** / **SC-002** `sampled` / **100%** gate (**spec.md**)
- [X] T035 [P] Update `TESTING_DOCUMENTATION.md` Schemathesis / CI matrix for DM API Modal-related routes; **cross-link or embed** the same **primary-flow release matrix** (or its canonical URL/path under `specs/007-scraper-via-dm-api/quickstart.md`) so CI and release reviewers share one source of truth
- [X] T036 [P] Refresh `specs/007-scraper-via-dm-api/checklists/requirements.md` validation notes after implementation; confirm checklist items cover **publication** of the matrix and its alignment with **SC-001** / **SC-002** / **SC-003**
- [X] T037 Reconcile `specs/007-scraper-via-dm-api/plan.md` “Source code” section with actual module paths chosen during implementation
- [X] T038 Audit operator-facing docs under `docs/` (and any `**/runbook*.md`) to remove mandatory direct scraper web URLs for supported workflows (**SC-004**); add **partial rollout** guidance so operators know which deployment is **authoritative** when legacy entrypoints remain temporarily visible, and file follow-up issues where external links must remain
- [X] T039 Add or tighten **structured logging** with **correlation IDs** on DM API → Modal invocation paths (`apis/data-management-api/apps/backend/` and/or `service_clients/modal_invoker.py`) so ingest/scrape jobs remain traceable across services (**FR-006**, constitution data stewardship)
- [X] T040 Run `make ci` from repository root and resolve failures before merge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** → **Phase 2** → **Phases 3–5** (user stories) → **Phase 6**
- **Phase 2** blocks all user stories (shared clients)

### User Story Dependencies

- **US1** and **US2** can start in parallel after Phase 2 (different apps: `apps/data-management-frontend/` vs `frontend/`). Both are P1.
- **US3** depends on Phase 2 client refactors (embedding/model); can overlap **US1** after T008–T009 land, but should not skip agent/backend alignment (T028–T029). **T033** DM SPA messaging is done; optional backend alignment when **T017–T018** land.

### Submodule

- **T017** / **T018** ship in `apis/data-management-api/apps/backend/vecinita_dm_api/` (see root `Makefile` `check-data-management-api-layout`). **T033** optional backend error JSON alignment remains if handlers add shared helpers.

### Parallel Opportunities

- **Phase 2**: T006 in parallel with T004–T005 once settings shape is agreed (coordinate on `shared_config` first — run T004 before T006 if conflicts).
- **US1 tests**: T011 and T012 in parallel.
- **US2 tests**: T019 and T020 in parallel.
- **US3 tests**: T024–T027 in parallel after T008–T009 complete.

---

## Parallel Example: User Story 1 (tests)

```bash
# After Phase 2 complete:
# Parallel: T011, T012 (T013 may run after env fixture patterns exist)
```

---

## Parallel Example: User Story 3 (tests)

```bash
# After T007–T009 complete:
# Parallel: T024, T025, T026, T027
```

---

## Implementation Strategy

### MVP First (User Story 1 + Foundational)

1. Complete Phase 1–2 (inventory + Modal clients).
2. Complete Phase 3 (US1): DM operator scraping without browser→scraper HTTP.
3. **STOP and VALIDATE**: `make ci` subset for DM packages + DM frontend tests; manual network check for SC-001.

### Incremental Delivery

1. Add Phase 4 (US2): gateway-only main frontend + SC-005 guards.
2. Add Phase 5 (US3): embedding/model Modal + agent policy + architecture/docs + edge-case UX (**T033**).
3. Phase 6 polish, runbooks (**T038**), logging (**T039**), full `make ci` (**T040**).

### Parallel Team Strategy

- Developer A: Phase 2 + US1 (DM API + DM frontend).
- Developer B: US2 (`frontend/` only) after Phase 2 if no coupling, else after T007.
- Developer C: US3 (`backend/` agent/policy + docs) after T008–T009.

---

## Notes

- Do not commit secrets; use env templates only.
- When submodule is missing, complete T007–T016 package-level work and document blocker for T017–T018 in the inventory doc.
- Prefer small PRs: Phase 2 alone, then US1, then US2, then US3.

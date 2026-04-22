# Tasks: Wire chat frontend to gateway/agent and align data-management stack

**Input**: Design documents from `/specs/005-wire-services-dm-front/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: **Included** — specification mandates Pact (**FR-007**, **FR-008**), Schemathesis (**FR-005**), Playwright (**FR-009**), typed DTO sharing (**FR-010**), and OpenAPI alignment (**FR-004**).

**Organization**: Phases follow user stories P1 → P1 → P2; setup and foundational work precedes all stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallel when different files and no ordering dependency on other incomplete tasks in the same batch
- **[USn]**: User story label from [spec.md](./spec.md)

## Path conventions

Monorepo: `frontend/`, `apps/data-management-frontend/`, `backend/`, `services/data-management-api/`, root `TESTING_DOCUMENTATION.md`, `.github/workflows/`, `.env.local.example`.

---

## Phase 1: Setup (shared infrastructure)

**Purpose**: Env documentation, tooling decisions, and CI skeleton so both product lines can add tests consistently.

- [x] T001 Audit and align placeholder URLs and ports across `.env.local.example`, `frontend/.env.example`, and `apps/data-management-frontend/.env.example` for gateway (8004), agent, and DM API (8005) per **FR-001**; ensure values stay consistent with the **ServiceEndpointConfig** catalog in `specs/005-wire-services-dm-front/contracts/env-wiring-chat-gateway-agent.md` §ServiceEndpointConfig catalog (**Key Entities** in **spec.md**)
- [x] T002 **(draft)** Document Pact broker vs checked-in pactfiles and **two-consumer** naming (`chat-frontend` vs `dm-frontend`) in `TESTING_DOCUMENTATION.md` and `specs/005-wire-services-dm-front/contracts/pact-schemathesis-playwright-pyramid.md` per spec **Edge Cases** — **T034** performs the final non-conflicting matrix edit on the same files
- [x] T003 [P] Add or extend GitHub Actions workflow file(s) under `.github/workflows/` for PR-scoped jobs (Pact consumer, unit) separate from post-merge real-stack workflow per **FR-006** / **SC-003**
- [x] T004 [P] Add `@pact-foundation/pact` and `@playwright/test` (and types) to **`frontend/package.json`** and **`apps/data-management-frontend/package.json`** with **stub** npm scripts `test:pact` / `test:e2e` that run real suites once T013/T018 and T019 exist (avoid empty scripts blocking PR wiring per **SC-004**/**SC-005**) per [plan.md](./plan.md) **Technical Context** — **DM** `@playwright/test` semver is **reconciled against `frontend`** in **T033** after **T021** lands (**D1** Playwright dedupe)

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Shared typed modules and testing documentation so **FR-010** and provider/consumer wiring do not diverge.

**Checkpoint**: No user-story implementation until T005–T012 complete (**O1**): for **T008**, “complete” in Phase 2 means **`rag-api.ts` imports interim types** from `apps/data-management-frontend/src/app/api/types/index.ts` only; **switching imports to codegen exports and deleting hand-written duplicates** is **US3 follow-through** immediately after **T029** (same task ID **T008**, second acceptance slice—do not block Phases 3–4 on it).

- [x] T005 Create typed contracts module directory `frontend/src/app/types/contracts/` with `index.ts` exporting **interim scaffold** DTO types for `frontend/src/app/services/agentService.ts` per **FR-010** and [data-model.md](./data-model.md) (**chat line only**—not replaced by DM **T029**; supersede or re-export when a future feature adds chat-side codegen per **spec.md** Clarifications §2026-04-22 **U1**)
- [x] T006 [P] Create typed contracts module `apps/data-management-frontend/src/app/api/types/index.ts` for scrape job DTOs consumed by `apps/data-management-frontend/src/app/api/rag-api.ts` per **FR-010** — **interim until T029** replaces bodies with OpenAPI-generated types per **spec.md** Clarifications §2026-04-22
- [x] T007 Refactor `frontend/src/app/services/agentService.ts` to import shared types from `frontend/src/app/types/contracts/index.ts` without changing runtime URL behavior per **FR-002** / **FR-010** (depends on T005)
- [x] T008 Refactor `apps/data-management-frontend/src/app/api/rag-api.ts` to import DTO types from `apps/data-management-frontend/src/app/api/types/index.ts` per **FR-003** / **FR-010** (depends on T006). **Phase 2 slice**: wire `rag-api.ts` to **interim** `types/index.ts` exports only so US1/US2 can ship. **US3 slice (after T029)** on the same files: switch imports to **generated** exports, remove duplicate hand-written bodies from **T006**, and satisfy **FR-010** single-source—this second slice does **not** gate Phases 3–4 (**O1**).
- [x] T009 [P] Document DM OpenAPI URL and gateway modal-jobs OpenAPI scope for Schemathesis in `TESTING_DOCUMENTATION.md` referencing `backend/schemathesis.toml` per [plan.md](./plan.md) **Testing strategy**
- [x] T010 Document chat **Pact provider verification** command(s) and merge-blocking policy for gateway/agent under `backend/` in `TESTING_DOCUMENTATION.md` per **FR-007** / **FR-005**
- [x] T011 Document DM **Pact provider verification** command(s) for `services/data-management-api/` in `TESTING_DOCUMENTATION.md` per **FR-008**
- [x] T012 Extend `specs/005-wire-services-dm-front/quickstart.md` with headings for Pact, Schemathesis, and Playwright env vars per **SC-001**; add a short pointer to the **ServiceEndpointConfig** catalog in `specs/005-wire-services-dm-front/contracts/env-wiring-chat-gateway-agent.md` §ServiceEndpointConfig catalog

---

## Phase 3: User Story 1 — Chat app reaches gateway and agent (Priority: P1) — MVP

**Goal**: Chat SPA resolves gateway base and completes agent flows through documented env and proxy.

**Independent Test**: Matches [spec.md](./spec.md) User Story 1: **non-stream** path + Pact/integration evidence for `/api/v1`; **streaming** path via Playwright (**T015**) or real-stack/DevTools per **spec.md** Clarifications §2026-04-22.

### Tests for User Story 1

- [x] T013 [P] [US1] Add Pact consumer tests under `frontend/tests/pact/chat-gateway.pact.test.ts` covering agent config fetch and **one non-streaming HTTP** chat interaction only per **FR-007** (streaming/SSE out of Pact scope per **spec.md** Clarifications §2026-04-22)
- [x] T014 [P] [US1] Extend `frontend/src/app/services/__tests__/agentService.test.ts` for local vs absolute `VITE_GATEWAY_URL` cases per User Story 1 acceptance scenarios (Vitest colocated with `agentService.ts`; **create this file** at that path if the repo does not yet have it)
- [x] T015 [US1] Add Playwright spec `frontend/tests/e2e/chat-gateway-smoke.spec.ts` using env `E2E_BASE_URL` / documented vars per **FR-009**: include **(1)** one **streaming/SSE** chat turn, **(2)** **SHOULD**-level checks for `html[lang]` and keyboard focus reaching the main chat input per **spec.md** **FR-009**; isolate tests; stub only non-Vecinita third parties per Playwright guidance

### Implementation for User Story 1

- [x] T016 [US1] Align `frontend/vite.config.ts` server proxy with `.env.local.example` and `frontend/.env.example` for `VITE_GATEWAY_PROXY_TARGET` per **FR-001** / **FR-002**
- [x] T017 [P] [US1] Update `frontend/.env.example` with explicit `VITE_AGENT_*` timeout comments referencing gateway `AGENT_TIMEOUT` ordering per **FR-002** and [plan.md](./plan.md) **Performance Goals**
- [x] T018 [US1] Add Pact consumer runtime setup `frontend/tests/pact/pactSetup.ts` (mock provider / broker publish) so `pnpm --dir frontend test:pact` passes on PR without live gateway per **FR-007**

**Checkpoint**: User Story 1 independently testable.

---

## Phase 4: User Story 2 — Data management UI talks to bundled API (Priority: P1)

**Goal**: DM dashboard uses `VITE_VECINITA_SCRAPER_API_URL` and optional gateway modal-jobs base; `/health` and `/jobs` succeed with CORS.

**Independent Test**: Run DM API on configured port; set `apps/data-management-frontend/.env`; dashboard diagnostics + job list per [spec.md](./spec.md) User Story 2.

### Tests for User Story 2

- [x] T019 [P] [US2] Add Pact consumer tests under `apps/data-management-frontend/tests/pact/dm-api.pact.test.ts` for `GET /health` and `GET /jobs` (and gateway modal-jobs variant when flag on) per **FR-008**
- [x] T020 [P] [US2] Extend `apps/data-management-frontend/src/app/api/rag-api.test.ts` for `scraperJobsApiRoot()` when `VITE_USE_GATEWAY_MODAL_JOBS` is enabled per User Story 2
- [x] T021 [US2] Add or extend Playwright spec under `apps/data-management-frontend/tests/e2e/` for dashboard diagnostics and scrape job list smoke per **FR-009**; add **SHOULD**-level assertion that primary navigation / job controls are keyboard-reachable (and `html[lang]` or locale hook if present) per **spec.md** **FR-009**

### Implementation for User Story 2

- [x] T022 [US2] Align `apps/data-management-frontend/.env.example` with root `.env.local.example` for DM ports and `VITE_VECINITA_GATEWAY_URL` per **FR-001** / **FR-003**
- [x] T023 [P] [US2] Document CORS dev origins (`http://localhost:5174`, etc.) primarily in `services/data-management-api/README.md` (create **CORS subsection** if missing); fallback to root `.env.local.example` comments — do **not** require `packages/shared-config/README.md` unless that file already exists in the submodule

**Checkpoint**: User Stories 1 and 2 independently testable.

---

## Phase 5: User Story 3 — Models and contracts stay aligned (Priority: P2)

**Goal**: OpenAPI alignment, Schemathesis coverage, Pact provider verification, and typed DTO parity for chat + DM.

**Independent Test**: CI or local: **FR-004** alignment, **FR-007**/**FR-008** consumer+provider, Schemathesis per **FR-005** — as in [spec.md](./spec.md) User Story 3.

### Tests / automation for User Story 3

- [x] T024 [P] [US3] Add script under `scripts/` or package script to export and diff DM OpenAPI (e.g. against `specs/005-wire-services-dm-front/artifacts/dm-openapi.snapshot.json`) per **FR-004** / **SC-002**
- [x] T025 [P] [US3] Add CI step on default branch to run OpenAPI diff script from T024 per **SC-002**
- [x] T026 [US3] Implement gateway Pact provider verification harness under `backend/tests/pact/` (or documented `Makefile` target) consuming pactfiles published by T013 per **FR-007** (depends on T013)
- [x] T027 [US3] Implement agent Pact provider verification harness co-located with agent routes under `backend/` per **FR-007** (depends on T013)
- [x] T028 [US3] Extend post-merge CI workflow in `.github/workflows/` to run Schemathesis against DM `openapi.json` and gateway modal-jobs paths when applicable per **FR-005** / [plan.md](./plan.md) **without removing or skipping** existing gateway+agent Schemathesis jobs (**FR-005** regression clause in **spec.md**); detailed regression guard for baseline gateway+agent jobs is **T032** (**C1**)
- [x] T029 [P] [US3] Add `openapi-typescript` (or Zod schema) codegen feeding `apps/data-management-frontend/src/app/api/types/` with npm script `pnpm --dir apps/data-management-frontend codegen:api` per **FR-004** / **FR-010** — run **before** deleting interim types from **T006**; then complete **T008** import switch per Notes
- [x] T030 [P] [US3] Wire PR CI workflows to call the **existing** `test:pact` npm scripts in `frontend/package.json` and `apps/data-management-frontend/package.json` (stubs from **T004** land in Phase 1 and **must** run real consumer suites after **T018**/**T019**—**B1**) so **SC-004**/**SC-005** run consumers on every PR without waiting for new script names
- [x] T031 [US3] Review `backend/src/api/` OpenAPI for modal-jobs scraper routes and ensure `backend/schemathesis.toml` includes them when env-gated features are on per **FR-005**; document which CI matrix / env toggles exercise those paths (align narrative with **T034** `TESTING_DOCUMENTATION.md` matrix)
- [x] T032 [P] [US3] **C1 / FR-005 regression**: Prefer an **assertable** default-branch CI step (job name + command) that runs existing **gateway + agent** Schemathesis targets already documented in `TESTING_DOCUMENTATION.md` / `backend/schemathesis.toml`; if CI cannot change in this feature, add an explicit **`Makefile` target** (or documented `make …` invocation) plus merge-blocking policy text in **T034** so the baseline is not “assumed green” without a runnable command

**Checkpoint**: Contract and E2E gates documented and executable.

---

## Phase 6: Polish and cross-cutting

**Purpose**: Repo-wide consistency, constitution CI, and final documentation.

- [x] T033 [P] **D1 — authoritative DM Playwright semver lock**: After **T021**, align `apps/data-management-frontend/package.json` `@playwright/test` (and types) with **`frontend/package.json`**; **T004** adds initial deps for both apps—**T033** is the **single dedupe/version pass** so CI does not drift across packages (**FR-009**)
- [x] T034 [P] Finalize `TESTING_DOCUMENTATION.md` matrix for **SC-003**–**SC-006** (merge-blocking vs informational); **reconcile** with **T002** draft so one coherent narrative remains (**D1-docs**: **T002** is exploratory draft only—**T034** **owns** the final `TESTING_DOCUMENTATION.md` and `contracts/pact-schemathesis-playwright-pyramid.md` narrative; remove duplicate or conflicting sections instead of stacking)
- [x] T035 Run `make ci` from repository root (`Makefile`) and resolve failures from new scripts/workflows per `.specify/memory/constitution.md` **Safety & quality**
- [x] T036 [P] Add `workflow_dispatch` real-stack workflow file `.github/workflows/real-stack-wiring.yml` (or extend T003) starting gateway+agent+optional DM for integration smoke per **FR-006**

---

## Dependencies and execution order

### Phase dependencies

- **Phase 1** → no prerequisites.
- **Phase 2** → after Phase 1; **blocks** all user stories.
- **Phase 3 (US1)** → after Phase 2.
- **Phase 4 (US2)** → after Phase 2 (can run in parallel with Phase 3 if staffed).
- **Phase 5 (US3)** → after Pact consumers exist (**T013**, **T019**) and typed modules (**T005–T008** interim slice per **O1**) for meaningful provider/codegen work.
- **Phase 6** → after desired user stories complete.

### User story dependencies

- **US1** and **US2** are independent after Phase 2.
- **US3** depends on artifacts from US1/US2 (pactfiles, types) but must not break independent demos of US1 or US2.

### Parallel opportunities

- **T003** and **T004** in Phase 1.
- **T006**, **T009** in Phase 2 (while T005 proceeds).
- **T013** and **T014** in Phase 3.
- **T019**, **T020** in Phase 4.
- **T024**, **T025**, **T029**, **T030**, **T032** in Phase 5 once prerequisites satisfied.

### Parallel example: User Story 1

```text
T013 [P] [US1]  frontend/tests/pact/chat-gateway.pact.test.ts
T014 [P] [US1]  frontend/src/app/services/__tests__/agentService.test.ts
```

### Parallel example: User Story 2

```text
T019 [P] [US2]  apps/data-management-frontend/tests/pact/dm-api.pact.test.ts
T020 [P] [US2]  apps/data-management-frontend/src/app/api/rag-api.test.ts
```

---

## Implementation strategy

### MVP (User Story 1 only)

1. Complete Phase 1 and Phase 2.  
2. Complete Phase 3 (chat wiring + Pact consumer + Vitest + Playwright smoke + proxy/docs).  
3. Stop and validate Independent Test for User Story 1.

### Incremental delivery

1. Add Phase 4 (DM wiring + Pact + tests).  
2. Add Phase 5 (OpenAPI alignment, provider verification, Schemathesis, codegen).  
3. Phase 6 for CI matrix and `make ci` hardening.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total tasks | **36** |
| Phase 1 | 4 |
| Phase 2 | 8 |
| Phase 3 (US1) | 6 |
| Phase 4 (US2) | 5 |
| Phase 5 (US3) | 9 |
| Phase 6 | 4 |

---

## Notes

- Provider tasks **T026**/**T027** require consumer pact output; run consumers in CI before provider verify in the same pipeline or use stored pactfiles.
- Do not commit secrets; use GitHub Actions secrets for broker tokens only.
- Adjust file paths if the repo already uses different `tests/` layouts—keep one convention per package after T005.
- **U1 (types)**: Run **T029** (codegen) before deleting interim types from **T006**; complete the **US3 slice** of **T008** (generated imports) immediately after codegen lands so Pact and `rag-api` share one module.
- **O1 (T008)**: Phase 2 checkpoint “T008 complete” = interim `rag-api` → `types` wiring only; post-**T029** cleanup is the **T008** US3 slice, not a Phase 2 gate.
- **D1 (Playwright)**: **T004** bootstraps both apps; **T033** owns final **DM** `@playwright/test` alignment with **chat** after **T021**.
- **D1-docs**: **T002** is an intentional **draft**; **T034** must merge its content into a single authoritative `TESTING_DOCUMENTATION.md` matrix without contradictory duplicate sections.
- **F1 (catalog)**: **ServiceEndpointConfig** table lives under §ServiceEndpointConfig catalog in `specs/005-wire-services-dm-front/contracts/env-wiring-chat-gateway-agent.md`; **T001** / **T012** keep templates and **quickstart.md** aligned with it.
- **B1 (scripts)**: **`test:pact` / `test:e2e` stubs** ship in **T004** for **both** frontends; Phases 3–4 must replace stubs with real commands so PR jobs wired in **T030** never depend on Phase 5 alone.
- **E1 (a11y / locale)**: **FR-009** **SHOULD**-level coverage is implemented in **T015** (chat) and **T021** (DM), per **spec.md** Constitution alignment.

---
description: "Task list for gateway live reliability, schema coverage, Render-owned persistence"
---

# Tasks: Gateway live reliability, schema coverage, and Render-owned persistence

**Input**: Design documents from `/specs/001-gateway-live-schema/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/gateway-persistence-boundary.md](./contracts/gateway-persistence-boundary.md)

**Tests**: Spec does not mandate TDD; contract verification uses existing `make test-schemathesis-*` targets.

**Organization**: Phases follow user-story priority (US1 → US2 → US3), then polish. Constitution: data stewardship, service boundaries, quality gates per `.specify/memory/constitution.md`.

## Format

`- [ ] Tnnn [P?] [USn?] Description with file path`

---

## Phase 1: Setup (shared artifacts)

**Purpose**: Baseline and waiver templates before code changes.

- [x] T001 Create `specs/001-gateway-live-schema/baseline-notes.md` summarizing last failing `make test-schemathesis-cli` (4 server errors, TraceCov %, host `dpg-*` DNS) with date
- [x] T002 [P] Create `specs/001-gateway-live-schema/exception-register.md` as FR-004 waiver template (operation id, dimension, rationale, owner, date)
- [x] T003 [P] Create stub `specs/001-gateway-live-schema/inventory-db-usage.md` with sections for Modal vs Render DB callers

---

## Phase 2: Foundational (blocking)

**Purpose**: Inventory and persistence seam so US1 implementation does not thrash.

**⚠️ CRITICAL**: Complete before parallelizing US1/US2 file edits that assume the new boundary.

- [x] T004 Complete `specs/001-gateway-live-schema/inventory-db-usage.md`: grep/document `psycopg` / `DATABASE_URL` / `MODAL_DATABASE_URL` in `services/scraper/`, `backend/src/services/modal/`, and Modal entrypoints tied to gateway `invoke_modal_*`
- [x] T005 Add Render-side persistence module `backend/src/services/ingestion/modal_scraper_persist.py` (or adjacent package) to upsert chunk batches from Modal DTOs per [data-model.md](./data-model.md), using existing `backend` DB pool / connection patterns (no new Modal DSN reads)
- [x] T006 Document env flag or rollout strategy in `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` for “Modal returns payload → gateway persists” (and removal of `MODAL_DATABASE_URL` from Modal secrets when scraper no longer connects)

**Checkpoint**: Inventory + persist API sketched; gateway team can implement US1 against T005.

---

## Phase 3: User Story 1 — Reliable job operations (Priority: P1) 🎯 MVP

**Goal**: Modal-backed scraper job routes stop returning **500** from unreachable Postgres inside Modal; Render persists.

**Independent Test**: `make test-schemathesis-cli` shows no `not_a_server_error` failures on `POST/GET/POST cancel` under `/api/v1/modal-jobs/scraper` (same gateway host); or documented waiver.

### Implementation

- [x] T007 [US1] Refactor `services/scraper/src/vecinita_scraper/` so Modal-invoked paths used by the gateway return **JSON chunk/job payloads** without opening `vecinita_scraper/core/db.py` for uploads (split “compute only” vs legacy ASGI path if needed)
- [x] T008 [US1] Wire `backend/src/api/router_modal_jobs.py` to call `backend/src/services/ingestion/modal_scraper_persist.py` (T005) after successful `invoke_modal_scrape_job_submit` / `get` / `cancel` where batch or status persistence applies per [contracts/gateway-persistence-boundary.md](./contracts/gateway-persistence-boundary.md)
- [x] T009 [US1] Adjust `backend/src/services/modal/invoker.py` and Modal function signatures only if payload shapes change; keep OpenAPI-aligned types
- [x] T010 [US1] Draft SC-004 operator steps in `specs/001-gateway-live-schema/runbook-draft.md` (gateway env vs worker DSN escalation) for later promotion to `docs/deployment/`

**Checkpoint**: US1 behavior testable against staging; MVP scope for first merge.

---

## Phase 4: User Story 2 — 100% schema coverage gate (Priority: P2)

**Goal**: TraceCov dimensions (especially **responses**) meet **100%** for operations **included** in the live pass per FR-006 / Clarifications **A**.

**Independent Test**: `make test-schemathesis-cli` TraceCov summary shows 100% on responses (and other dimensions) or `exception-register.md` lists signed waivers.

### Implementation

- [x] T011 [P] [US2] Add complete FastAPI `responses=` (2xx/4xx/5xx JSON error schema) for all routes in `backend/src/api/router_modal_jobs.py` per FR-006
- [x] T012 [P] [US2] Add or extend `responses=` on `backend/src/api/router_scrape.py` and any other gateway routers still missing coverage for **included** live-pass operations
- [x] T013 [US2] Run `make test-schemathesis-gateway` then `make test-schemathesis-cli`; update `specs/001-gateway-live-schema/exception-register.md` if any dimension cannot reach 100%

**Checkpoint**: Contract gate green or explicit waivers.

---

## Phase 5: User Story 3 — Fewer contract warnings (Priority: P3)

**Goal**: Reduce repeated 404 / validation-mismatch noise via hooks and env seeds (SC-003).

**Independent Test**: Compare warning counts before/after with same `SCHEMATHESIS_*` env.

- [x] T014 [P] [US3] Extend `backend/tests/schemathesis_hooks.py` to pin `SCHEMATHESIS_MODAL_GATEWAY_JOB_ID`, `SCHEMATHESIS_SOURCE_URL`, and path params for registry/documents per spec acceptance
- [x] T015 [US3] Document new/updated env knobs in header comments of `backend/scripts/run_schemathesis_live.sh`

---

## Phase 6: Polish & cross-cutting

- [x] T016 Promote `runbook-draft.md` to operator doc: add `docs/deployment/GATEWAY_LIVE_OPERATIONS.md` (or section in `TESTING_DOCUMENTATION.md`) with **≤10** steps for SC-004 sign-off
- [x] T017 [P] Align `render.yaml` / `render.staging.yaml` comments if gateway env vars for external DB URL need dashboard callouts
- [x] T018 Run `make ci` (see `Makefile` and `.github/workflows/`) from repository root and fix any regressions

---

## Dependencies (story order)

```text
Phase 1 → Phase 2 → US1 (P1) → US2 (P2) → US3 (P3) → Polish
```

US2 can start **documentation-only** OpenAPI work in parallel with late US1 only after router files are stable—default **sequential** US1 then US2 to reduce merge conflicts.

## Parallel execution examples

- **After Phase 2**: T011 and T012 in parallel (different files) if US1 router edits are merged.
- **US3**: T014 and T015 can run in parallel once hooks contract is agreed.

## Implementation strategy

1. **MVP**: Finish **Phase 2** + **US1** (T007–T010) to stop live **500**s on modal-jobs scraper paths.  
2. **Increment 2**: **US2** OpenAPI **responses** (FR-006) + TraceCov proof.  
3. **Increment 3**: **US3** hooks + script docs.  
4. **Close**: Runbook + CI.

**Suggested MVP scope**: Phases 1–3 (through T010).

---

## Task summary

| Metric | Value |
|--------|-------|
| Total tasks | 18 |
| US1 | 4 (T007–T010) |
| US2 | 3 (T011–T013) |
| US3 | 2 (T014–T015) |
| Setup + Foundational + Polish | 9 (T001–T006, T016–T018) |

All tasks use checkbox + `Tnnn` + file paths; story labels on US1–US3 phases only.

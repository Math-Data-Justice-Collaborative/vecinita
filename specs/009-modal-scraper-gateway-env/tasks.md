---
description: "Task list for Modal scraper gateway persistence (009)"
---

# Tasks: Modal scraper gateway persistence alignment

**Input**: Design documents from `/specs/009-modal-scraper-gateway-env/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: **Required** per [spec.md](./spec.md) FR-009 and SC-005 (automated regression for persistence matrix and chained `ConfigError`).

**Organization**: Phases follow user story priority (P1 → P2 → P3), then polish.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no ordering dependency on incomplete sibling)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` for user-story phases only

## Path Conventions

Monorepo: primary code under `services/scraper/src/vecinita_scraper/`, tests under `services/scraper/tests/`, operator SSOT under `docs/deployment/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align on contracts and current code paths before edits.

- [x] T001 Review `specs/009-modal-scraper-gateway-env/contracts/modal-get-db-persistence-matrix.md` and `specs/009-modal-scraper-gateway-env/contracts/modal-worker-failure-handling.md` against `services/scraper/src/vecinita_scraper/core/db.py` and Modal worker entrypoints in `services/scraper/src/vecinita_scraper/workers/scraper.py`, `services/scraper/src/vecinita_scraper/workers/processor.py`, `services/scraper/src/vecinita_scraper/workers/chunker.py`, and `services/scraper/src/vecinita_scraper/workers/embedder.py`; skim existing gateway regression tests `backend/tests/test_api/test_router_modal_jobs.py` (gateway persist + `job_id` inject) and `backend/tests/test_api/test_router_scraper_pipeline_ingest.py` (any listed ingest token) to confirm **FR-004** / **FR-005** remain satisfied for this release slice; **baseline** the Modal persistence-policy `ConfigError` text in `services/scraper/src/vecinita_scraper/core/db.py` against **FR-002** (contract path + remediation categories)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helper for “mark job FAILED only when a persistence client exists; never mask `ConfigError` with a second `get_db()`”. **Blocks** all worker refactors in Phase 3.

- [x] T002 Implement shared async helper (e.g. `report_worker_job_failure`) in `services/scraper/src/vecinita_scraper/workers/job_failure.py` that accepts `job_id`, exception, optional `database` handle, logs structured context with `job_id` (no secrets), updates `FAILED` via `database` when safe, and **re-raises** `ConfigError` from persistence policy without calling `services/scraper/src/vecinita_scraper/core/db.py` `get_db()` again

**Checkpoint**: Helper merged and importable — User Story 1 implementation can proceed.

---

## Phase 3: User Story 1 — Restore scraper pipeline execution (Priority: P1) 🎯 MVP

**Goal**: Misconfiguration surfaces once; operators can fix env per contract; jobs proceed when gateway HTTP pair is valid.

**Independent Test**: Monkeypatch Modal cloud + env in pytest per [quickstart.md](./quickstart.md); confirm `get_db()` matrix and worker handlers match [contracts/modal-get-db-persistence-matrix.md](./contracts/modal-get-db-persistence-matrix.md) and [contracts/modal-worker-failure-handling.md](./contracts/modal-worker-failure-handling.md).

### Tests for User Story 1 (write first; expect red until worker wiring lands)

- [x] T003 [P] [US1] Extend persistence-matrix coverage in `services/scraper/tests/unit/test_get_db_modal_gateway.py` (partial pair: `SCRAPER_GATEWAY_BASE_URL` without usable first `SCRAPER_API_KEYS` segment; keys without URL; optional whitespace edge cases per `services/scraper/src/vecinita_scraper/core/db.py` `_use_gateway_http_pipeline()`)
- [x] T004 [P] [US1] Add `services/scraper/tests/unit/test_worker_failure_paths.py` that asserts **no second `get_db()`** during failure handling when persistence policy raises `services/scraper/src/vecinita_scraper/core/errors.py` `ConfigError` **before** a DB handle exists: prefer testing **`run_scrape_job` / `run_processing_job` / `run_chunking_job`** with `pytest.MonkeyPatch` on `services/scraper/src/vecinita_scraper/core/db.py` `get_db` (call counter) and patched `_modal_function_running_in_cloud`, **or** a small **test-only async wrapper** next to workers that mirrors the `try`/`except` structure—avoid depending on Modal `@app.function` decorators unless the repo already provides a harness

### Implementation for User Story 1

- [x] T005 [US1] Refactor `services/scraper/src/vecinita_scraper/workers/scraper.py` `scraper_worker` exception path to use `services/scraper/src/vecinita_scraper/workers/job_failure.py` (depends on T002; complete after T004 tests exist)
- [x] T006 [P] [US1] Refactor `services/scraper/src/vecinita_scraper/workers/processor.py` `processor_worker` exception path to use `services/scraper/src/vecinita_scraper/workers/job_failure.py` (depends on T002)
- [x] T007 [P] [US1] Refactor `services/scraper/src/vecinita_scraper/workers/chunker.py` `chunker_worker` exception path to use `services/scraper/src/vecinita_scraper/workers/job_failure.py` (depends on T002)
- [x] T008 [US1] Audit `services/scraper/src/vecinita_scraper/workers/embedder.py` for `ConfigError` / `get_db()` batch behavior; add minimal fix or structured log + comment per `specs/009-modal-scraper-gateway-env/contracts/modal-worker-failure-handling.md` if gap vs FR-008

**Checkpoint**: US1 code + tests green locally for scraper package; Modal cloud policy unchanged except safer failure paths.

---

## Phase 4: User Story 2 — Verify parity without guesswork (Priority: P2)

**Goal**: Operators can use SSOT doc + checklist without drift from code behavior.

**Independent Test**: Staging or doc review: each go/no-go row maps to env names in `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`.

### Implementation for User Story 2

- [x] T009 [US2] Update `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` (Modal scraper + gateway HTTP pipeline / checklist rows) so failure modes (single trace, partial pair, first-segment ingest token) match implemented behavior after T003–T008 (**FR-002** / `db.py` message text is verified in **T011** after any `ConfigError` copy change, not here)
- [x] T010 [P] [US2] Refresh operator commands in `specs/009-modal-scraper-gateway-env/quickstart.md` to reference final test module paths and any new env-validation notes

**Checkpoint**: Doc parity with code; quickstart matches repo layout.

---

## Phase 5: User Story 3 — Controlled exception path (Priority: P3)

**Goal**: Bypass remains explicit, time-bounded, non-production; matches FR-007.

**Independent Test**: Doc states production must not rely on `SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL`; cross-link from error message path optional.

### Implementation for User Story 3

- [x] T011 [US3] Strengthen `SCRAPER_ALLOW_DIRECT_POSTGRES_ON_MODAL` / exceptional-debugging language in `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` (and link from `services/scraper/src/vecinita_scraper/core/db.py` `ConfigError` text only if wording still accurate) per **FR-007**; **after** any edit to `services/scraper/src/vecinita_scraper/core/db.py` `ConfigError` message in this task, re-read the string against **FR-002** (contract doc path + remediation categories still present and accurate)

**Checkpoint**: Bypass semantics explicit for operators.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: CI gate and checklist sync.

- [x] T012 Run `make ci` from the vecinita monorepo root and fix any failures touching `services/scraper/` or docs changed above; if **T011** did **not** edit `services/scraper/src/vecinita_scraper/core/db.py`, re-skim the same persistence-policy `ConfigError` string against **FR-002** (unchanged copy is acceptable; **T001** baseline + no edit closes the loop)
- [x] T013 [P] Update validation notes in `specs/009-modal-scraper-gateway-env/checklists/requirements.md` if spec/tasks completion criteria changed; if **T011** modified `services/scraper/src/vecinita_scraper/core/db.py`, record that **FR-002** was re-checked post-edit
- [x] T014 [P] Add a short **Regression coverage** note to `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` (within T009’s edit pass) or to `specs/009-modal-scraper-gateway-env/quickstart.md` linking **FR-004** / **FR-005** to `backend/tests/test_api/test_router_modal_jobs.py` and `backend/tests/test_api/test_router_scraper_pipeline_ingest.py` so operators and implementers see gateway obligations are locked by CI; skip duplicate prose if T009 already includes equivalent cross-links

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (T001)**: No dependencies.
- **Phase 2 (T002)**: Depends on T001 — **blocks** T005–T008.
- **Phase 3 (US1)**: T003–T004 can start after T001 (prefer early); **T005–T008 depend on T002**; T005 should follow T004 for TDD signal; T006–T007 parallel after T005 once `job_failure.py` API is stable.
- **Phase 4–5**: Start after US1 core behavior merged (recommend after T008) — docs depend on final behavior.
- **Phase 6**: After desired story phases complete; **T014** depends on **T009** (same doc) or land T014 text in `quickstart.md` instead to avoid merge friction.

### User Story Dependencies

- **US1 (P1)**: No dependency on US2/US3 for code correctness.
- **US2 (P2)**: Doc accuracy depends on US1 behavior being final or near-final.
- **US3 (P3)**: Independent copy-edit in same doc file as US2 — **serialize T009 → T011** or merge doc edits in one PR to avoid merge conflicts on `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`.

### Parallel Opportunities

- **T003 ∥ T004** after T001 (both test files, different paths).
- **T006 ∥ T007** after T002 and `job_failure.py` API stable (different worker files).
- **T010 ∥ T013** while doc PR open (different files).
- **T014** with **T010** only if T014 targets `quickstart.md`; else **serialize T009 → T014** on `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`.

---

## Parallel Example: User Story 1

```bash
# After T001, run test authoring in parallel:
# T003 — extend services/scraper/tests/unit/test_get_db_modal_gateway.py
# T004 — add services/scraper/tests/unit/test_worker_failure_paths.py

# After T002 + T005 land, parallel worker refactors:
# T006 — services/scraper/src/vecinita_scraper/workers/processor.py
# T007 — services/scraper/src/vecinita_scraper/workers/chunker.py
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete T001 → T002 (foundation).  
2. Land T003–T004 (failing/red until workers fixed).  
3. Land T005–T008 (green tests).  
4. **STOP**: Run scraper-focused pytest + `make ci` (see Phase 6).

### Incremental Delivery

1. **MVP**: Phases 1–3 (US1) — fixes production confusion and CI regression gaps.  
2. **US2**: Phase 4 — operator SSOT.  
3. **US3**: Phase 5 — bypass clarity.  
4. **Polish**: Phase 6.

### Parallel Team Strategy

- Developer A: T002, T005, T008 (sequential chain).  
- Developer B: T003, T004 in parallel after T001.  
- Developer C: T006–T007 after `job_failure.py` merged.

---

## Notes

- **Total tasks**: 14 (T001–T014).  
- **Per story**: US1 → T003–T008 (6 tasks); US2 → T009–T010 (2); US3 → T011 (1); Setup 1; Foundational 1; Polish 3 (T012–T014).  
- **Constitution**: Ingestion pipeline changes require tests (`make ci`) before merge-ready.  
- **FR-004 / FR-005 (post–`/speckit.analyze`)**: Gateway-owned submit + multi-segment ingest are **already covered** by backend tests (`test_router_modal_jobs.py`, `test_router_scraper_pipeline_ingest.py`). Feature **009** does not add new gateway product work unless CI or review finds a gap; **T001** confirms alignment, **T014** documents the link for traceability.  
- **FR-002 when `db.py` is untouched in T011**: **T001** baselines `ConfigError` vs **FR-002**; **T012** re-skims if **T011** skipped `db.py` (**T011** still owns **FR-002** after any `db.py` edit).  
- **T014 placement (default)**: Prefer `specs/009-modal-scraper-gateway-env/quickstart.md` for the **Regression coverage** blurb when `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` is already heavily edited in T009/T011; otherwise fold **T014** into the contract doc in the same commit as **T009**/**T011** to avoid churn.  
- Avoid merge conflicts: batch edits to `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` in one commit covering T009, T011, and T014 when T014 uses that file.

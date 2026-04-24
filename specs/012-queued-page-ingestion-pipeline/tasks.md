# Tasks: Queued page ingestion pipeline

**Input**: Design documents from `/specs/012-queued-page-ingestion-pipeline/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: **Included** — [plan.md](./plan.md) mandates **TDD** (red tests before implementation) plus spec **SC-005–SC-007** / **FR-011–FR-015** contract guarantees.

**Organization**: Phases follow user stories **US1 (P1) → US2 (P2) → US3 (P3)** after shared setup and foundation. **40 tasks** (**T001–T040**), including **post-`/speckit-analyze` remediation** (**T035–T040**).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies)
- **[Story]**: `US1` / `US2` / `US3` for user-story phases only

---

## Phase 1: Setup (shared documentation & gates)

**Purpose**: Align deployment docs and CI surfaces before code changes.

- [x] T001 Add a **See also** box in `docs/deployment/MODAL_DEPLOYMENT.md` linking to `specs/012-queued-page-ingestion-pipeline/contracts/render-modal-pipeline-wiring.md` — place it adjacent to the **Gateway / scraper pipeline** narrative (sections mentioning **`SCRAPER_GATEWAY_BASE_URL`**, **`SCRAPER_API_KEYS`**, or **internal scraper-pipeline** HTTP), or at the document’s **See also** footer if no single anchor fits
- [x] T002 [P] Add a **See also** box in `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` linking to `specs/012-queued-page-ingestion-pipeline/contracts/gateway-ingestion-http-surface.md` — place it after the **env group / CORE legend** (top of file) or beside **gateway (`GW`)** variable rows so reviewers see HTTP contract expectations next to env ownership
- [x] T003 [P] Review `render.yaml` for `vecinita-gateway` (and related workers): confirm `healthCheckPath` and `autoDeployTrigger: checksPass` remain appropriate; document any required delta in `specs/012-queued-page-ingestion-pipeline/plan.md` if you change service definitions

---

## Phase 2: Foundational (blocking — contracts, stages, correlation)

**Purpose**: **FR-011–FR-015**, durable job semantics, and pipeline stage discipline **before** story slices.

**⚠️ CRITICAL**: No user-story implementation until transition rules and ingest security tests exist.

### Tests (TDD — write first, expect RED)

- [x] T004 [P] [TDD] Extend `backend/tests/test_api/test_router_scraper_pipeline_ingest.py` with cases for **401** on bad/missing `X-Scraper-Pipeline-Ingest-Token` and **503** when `SCRAPER_API_KEYS` is unset on the gateway
- [x] T005 [P] [TDD] Add `backend/tests/services/ingestion/test_pipeline_stage_transitions.py` asserting allowed/forbidden transitions from `specs/012-queued-page-ingestion-pipeline/data-model.md` (expects RED until `pipeline_stage` exists in **T007**)
- [x] T006 [P] [TDD] Add `backend/tests/test_api/test_modal_jobs_gateway_errors.py` covering stable **FR-014** JSON keys and **FR-015** correlation presence on selected `modal-jobs` scrape failure/timeout paths (new file; mock Modal invoker)

### Implementation

- [x] T007 Implement `backend/src/services/ingestion/pipeline_stage.py` with transition validation + error categories consumed by gateway and (optionally) workers; module docstring MUST reference **Postgres-backed durable queue** (`research.md` Decision 5) so implementers do not introduce a broker in v1 by accident (**analyze U1**)
- [x] T008 Wire `pipeline_stage` / `error_category` through `backend/src/services/ingestion/modal_scraper_pipeline_persist.py` and `backend/src/api/router_scraper_pipeline_ingest.py` using **structured fields in existing rows first** (`metadata` jsonb and/or documented `error_message` prefix) per `contracts/render-modal-pipeline-wiring.md` § Pipeline stage persistence; **do not** add new DDL until **T018** explicitly adds a migration and updates the same contract section
- [x] T009 Propagate **correlation id** from gateway request context into Modal job metadata and structured logs in `backend/src/api/router_modal_jobs.py` and `backend/src/services/modal/invoker.py` (where payloads are assembled)
- [x] T010 [P] Ensure Modal worker HTTP client attaches `X-Request-Id` (or agreed header) on outbound calls in `services/scraper/src/vecinita_scraper/persistence/gateway_http.py` when the value is available in worker context
- [x] T011 Align public gateway **OpenAPI** export for touched routes under `backend/src/api/` so **FR-011** stays canonical (update route `response_model` / `responses=` metadata as needed)
- [x] T012 Extend `backend/schemathesis.toml` (tags/examples) if new `modal-jobs` or pipeline-adjacent public behaviors are added for **SC-006** coverage
- [x] T035 [P] [TDD] Add `backend/tests/services/ingestion/test_pipeline_queue_fairness.py` asserting **global FIFO** claim order by `created_at` for queued jobs at equal priority (see `data-model.md` § Queue fairness); wire ordering into drain/claim logic when touching `services/scraper/src/vecinita_scraper/workers/` in **T015**/**T022** (**FR-002**). **Test boundary:** use **in-memory or faked job rows / queue port** (protocol) so this test does **not** import scraper worker modules into `backend/`—only assert ordering contract the workers must honor; integration proof lives under **T015**/**T022** in `services/scraper/tests/`

**Checkpoint**: Pipeline ingest secured; stage machine + correlation story **test-backed**; **FR-002** ordering test exists; ready for US1 orchestration work.

---

## Phase 3: User Story 1 — End-to-end page processing (Priority: P1) 🎯 MVP

**Goal**: **Queued → scrape → chunk → LLM → embed → persist** for in-scope URLs with traceable chunks (**FR-001–FR-007**).

**Independent Test**: Ingest a small allowlisted URL set in staging; each page ends **succeeded** with ≥1 chunk+embedding **or** a **classified** terminal failure; **SC-001** traceability holds.

### Tests (TDD — write first, expect RED)

- [x] T013 [P] [US1] [TDD] Add `services/scraper/tests/integration/test_queued_page_pipeline_happy_path.py` driving worker stages with **Modal + HTTP gateway mocked** until green (asserts chunk rows + embeddings linkage)
- [x] T014 [P] [US1] [TDD] Add `backend/tests/services/ingestion/test_modal_scraper_pipeline_idempotency.py` for duplicate stage POSTs (same logical chunk key) not creating duplicate embeddings per **data-model.md** idempotency note
- [x] T036 [P] [US1] [TDD] Add `services/scraper/tests/integration/test_queued_page_pipeline_edge_content.py` (new) for **empty body** and **CSR shell** pages: expect terminal **`no_indexable_content`** or **`scrape_failed`** (no LLM/embed path) and assert **SC-002** (no embedding rows) for those jobs

### Implementation

- [x] T037 [P] [US1] Add `services/scraper/src/vecinita_scraper/workers/chunking_defaults.py` exporting constants aligned with `specs/012-queued-page-ingestion-pipeline/data-model.md` § Chunking parameters; add `services/scraper/tests/unit/test_chunking_defaults.py` locking bounds/overlap (**FR-004**)
- [x] T015 [US1] Orchestrate **post-scrape** pipeline in `services/scraper/src/vecinita_scraper/workers/scraper.py` (or a new `services/scraper/src/vecinita_scraper/workers/ingestion_pipeline.py`): **chunk → enrich → embed → persist** using existing Modal/gateway clients and **T037** defaults (**FR-003–FR-006**); branch early for edge outcomes covered by **T036**
- [x] T016 [P] [US1] Extend `backend/src/services/ingestion/modal_scraper_pipeline_persist.py` to persist **raw** and **enriched** text fields required for **FR-005** / traceability (match actual table/column names in repo)
- [x] T017 [US1] Ensure `_kick_scraper_pipeline_after_submit` flow in `backend/src/api/router_modal_jobs.py` still drains work after submit and respects new stage updates (**FR-001** queue semantics)
- [x] T018 [P] [US1] Add SQL migration file under `services/scraper/migrations/` **only if** new persisted columns are required (else encode stage in existing json/metadata without migration)
- [x] T019 [US1] Update `frontend/pacts/` and/or provider verification under `backend/tests/pact/` if any **browser-visible** JSON shape changes for ingestion-related gateway routes (**SC-005**)

**Checkpoint**: **US1** demonstrable end-to-end in staging with **make ci** green for touched packages. For **SC-001** scale, run a **manual or tagged staging** pass with **≥20** distinct in-scope URLs (see spec **SC-001**) once core automation is green—no merge-blocking CI obligation unless you add an optional live job later.

---

## Phase 4: User Story 2 — Overload & failure handling (Priority: P2)

**Goal**: Retries, backoff, bounded concurrency, terminal failure categories; **FR-010** partial consistency; **SC-003** burst behavior.

**Independent Test**: Inject transient Modal failure → job succeeds after bounded retries; permanent policy failure → terminal state without embeddings (**SC-002**); burst enqueue does not wedge the queue.

### Tests (TDD — write first, expect RED)

- [x] T020 [P] [US2] [TDD] Add `services/scraper/tests/unit/test_pipeline_retry_policy.py` for exponential/backoff + max attempts on transient errors
- [x] T021 [P] [US2] [TDD] Add `services/scraper/tests/unit/test_pipeline_concurrency_cap.py` (or worker test) asserting bounded parallel page processing under configured limits

### Implementation

- [x] T022 [US2] Implement retry/backoff + max-attempt policy in `services/scraper/src/vecinita_scraper/workers/` coordinated with `pipeline_persist.update_job_status` writes
- [x] T023 [US2] Encode **permanent vs transient** failure classes mapped to **FR-014** `error` codes for any new browser-visible routes introduced in **US1**
- [x] T024 [US2] Implement **FR-010** reconciliation: on terminal failure after partial chunk writes, either delete orphan rows for that `job_id` stage or set explicit `partial` + reprocess flag (document behavior in `specs/012-queued-page-ingestion-pipeline/data-model.md` when chosen)
- [x] T025 [US2] Guard **FR-009**: skip enrich/embed persistence when crawl outcome is policy-blocked (extend classification handling in `services/scraper/src/vecinita_scraper/workers/scraper.py` or adjacent module)
- [x] T038 [P] [US2] [TDD] Add `backend/tests/services/ingestion/test_pipeline_canonical_dedup.py` (or scraper-side equivalent) for **duplicate_skipped** / idempotent no-op when `canonical_url` matches a **terminal succeeded** job per `data-model.md` § Dedup
- [x] T039 [US2] Implement short-circuit in `services/scraper/src/vecinita_scraper/workers/` (or persist layer) for **T038** behavior without duplicate embeddings

**Checkpoint**: **US2** behaviors independently testable without breaking **US1** happy path.

---

## Phase 5: User Story 3 — Operator visibility & audit (Priority: P3)

**Goal**: Operators see stage, timestamps, failure category, and can join **correlation id** across gateway + Modal logs (**FR-008**, **FR-015**, **SC-007**).

**Independent Test**: Given a `job_id` or URL, status API + logs answer “where did it fail?” within one support workflow.

### Tests (TDD — write first, expect RED)

- [x] T026 [P] [US3] [TDD] Extend `backend/tests/test_api/test_router_modal_jobs.py` (or create focused file) asserting `GET /api/v1/modal-jobs/scraper/{job_id}` includes **pipeline_stage** / **error_category** / timestamps when persisted
- [x] T027 [P] [US3] [TDD] Add log assertion test (structured log capture) proving the same correlation id appears for gateway request + simulated worker handoff in `backend/tests/test_api/test_correlation_logging.py` (new)

### Implementation

- [x] T028 [US3] Enrich `GatewayModalScrapeJobBody` (or companion model) in `backend/src/api/router_modal_jobs.py` with operator-facing stage metadata; update OpenAPI responses
- [x] T029 [US3] Ensure structured logging includes **request_id** / correlation on **modal-jobs** handlers and internal pipeline routes in `backend/src/api/router_modal_jobs.py` and `backend/src/api/router_scraper_pipeline_ingest.py`
- [x] T030 [US3] Extend `specs/012-queued-page-ingestion-pipeline/quickstart.md` with a **SC-007** drillbook (copy/paste `curl` + log query steps)

**Checkpoint**: **US3** complete; operators can triage without code checkout.

---

## Phase 6: Polish & cross-cutting

**Purpose**: Docs, Modal tuning notes, final verification.

- [x] T040 [P] Extend `frontend/src/app/lib/apiBaseResolution.test.ts` to cover **FR-012**: ingestion/chat client config resolves to a **single** gateway base (no secondary Modal `*.modal.run` host for those operations when env is set per prod contract)
- [x] T031 [P] Document Modal **timeout** / resource hints adopted for pipeline functions in `docs/deployment/MODAL_DEPLOYMENT.md` (summarize `specs/012-queued-page-ingestion-pipeline/research.md` Decision 1–2)
- [x] T032 [P] Run `npm run test:pact` in `frontend/` after any consumer contract updates
- [x] T033 Run `make pact-verify-providers` from repo root before release per `TESTING_DOCUMENTATION.md` policy
- [x] T034 Run `make ci` from repo root and fix drift until green

---

## Dependencies & execution order

### Phase dependencies

- **Phase 1** → no deps.
- **Phase 2** → depends on **Phase 1** doc pointers (light); **blocks all user stories**.
- **Phase 3 (US1)** → after **Phase 2** checkpoint.
- **Phase 4 (US2)** → after **US1** MVP or in parallel **only if** stage persist API from **Phase 2** is stable (recommended: sequential **US1 → US2** to reduce merge risk).
- **Phase 5 (US3)** → after **US1** exposes stable job identifiers in DB/API.
- **Phase 6** → after desired stories complete.

### User story dependencies

- **US1**: No dependency on US2/US3.
- **US2**: Builds on US1 orchestration; keep interfaces backward compatible.
- **US3**: Builds on persisted stage metadata from **Phase 2**/**US1**.

### Parallel opportunities

- **T002**, **T003** in parallel.
- **Phase 2 — tests vs impl (TDD):** **T004**, **T005**, **T006**, **T035** can be **authored in parallel** (different files); **T005** stays RED until **T007** (`pipeline_stage`); **T035** may stay RED until **T015**/**T022** dequeue wiring. **T007**→**T008**→…→**T012** implement afterward (same phase).
- **US1 — tests vs impl:** **T013**, **T014**, **T036** in parallel before **T037** / **T015**; **T037** before **T015**; then **T015**–**T019**.
- **T020**, **T021** in parallel before **T022**–**T025**.
- **T026**, **T027** in parallel before **T028**–**T030**.
- **T038** before **T039**.
- **T040** ∥ **T031** ∥ **T032** before **T033**–**T034**.

### Parallel example: User Story 1

```bash
# After Phase 2 completes, launch US1 tests together:
# - services/scraper/tests/integration/test_queued_page_pipeline_happy_path.py
# - services/scraper/tests/integration/test_queued_page_pipeline_edge_content.py (T036)
# - backend/tests/services/ingestion/test_modal_scraper_pipeline_idempotency.py
```

---

## Implementation strategy

### MVP first (User Story 1 only)

1. Complete **Phase 1–2** (foundation + contracts).  
2. Complete **Phase 3 (US1)**; run **Independent Test** + **`make ci`**.  
3. Stop for demo / staging validation.

### Incremental delivery

1. Ship **US1** (corpus growth).  
2. Add **US2** (production hardening).  
3. Add **US3** (operator UX / support).  
4. **Phase 6** always last.

### Parallel team strategy

- Developer A: **Phase 2** gateway/tests.  
- Developer B: **Phase 2** scraper HTTP + worker logging.  
- After checkpoint: A takes **US1** backend persist; B takes **US1** worker orchestration; merge daily.

---

## Notes

- Prefer **small PRs** per phase; keep **OpenAPI + Pact** in lockstep (**FR-011** / **SC-005**).  
- Never place Modal tokens in `frontend/` env.  
- If schema work stalls, prefer **structured `error_message` / metadata json** over blocking SQL migrations for early slices.  
- **Scope boundary ([spec.md](./spec.md) Assumptions):** This feature implements **post-discovery** pipeline behavior (queue → scrape → chunk → enrich → embed → persist). **Crawl frontier**, discovery UI, and net-new URL harvesting are **out of scope** here unless a follow-on spec expands them.

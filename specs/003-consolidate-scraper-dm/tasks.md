# Tasks: Consolidate scraper, remote-only DM API integration, and gateway job stability

**Input**: Design documents from `/specs/003-consolidate-scraper-dm/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Spec **FR-005** / **SC-004** require automated contract regression; include explicit test and live-gate tasks tied to `backend/tests/` and `make test-schemathesis-cli`.

**Organization**: Phases follow user story priority (P1→P4); DM API submodule removal follows remote-client readiness (**plan** R2→R3→R4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no ordering dependency within the same phase)
- **[Story]**: `[US1]`…`[US4]` only on user-story phase tasks

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline and inventory before code changes.

- [X] T001 Create `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md` capturing current live gateway host, failing operations (`/api/v1/modal-jobs/scraper*`, `GET /api/v1/ask`), and warning classes (404, schema mismatch, coverage) from the latest `make test-schemathesis-cli` run
- [X] T002 [P] Create `specs/003-consolidate-scraper-dm/inventory-dm-api-submodule-imports.md` listing every Python import path under `apis/data-management-api/` that references `apps/backend/scraper-service/`, `apps/backend/embedding-service/`, or `apps/backend/model-service/`
- [X] T003 [P] Audit `apis/data-management-api/packages/service-clients/service_clients/{scraper_client,embedding_client,model_client}.py` against `inventory-dm-api-submodule-imports.md` and note missing RPCs or routes to implement in later tasks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared error-handling and deployment contract alignment **before** user-story delivery.

**⚠️ CRITICAL**: Complete this phase before starting US1–US4 implementation that assumes safe errors and stable env contracts.

- [X] T004 Add a small helper module `backend/src/utils/gateway_dependency_errors.py` that maps `psycopg2`/DNS-style failures to operator-safe messages (no raw `dpg-*` substrings in outward JSON) for use by gateway persistence paths
- [X] T005 Wrap DB exceptions from `backend/src/services/ingestion/modal_scraper_persist.py` public entrypoints using `backend/src/utils/gateway_dependency_errors.py` so `HTTPException` / `ErrorResponse` bodies satisfy **FR-002**
- [X] T006 Extend `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` with a short **go/no-go checklist** for `MODAL_SCRAPER_PERSIST_VIA_GATEWAY`, gateway `DATABASE_URL`, and Modal `MODAL_DATABASE_URL` (external) tied to the DNS failure class
- [X] T007 Add unit tests in `backend/tests/test_utils/test_gateway_dependency_errors.py` covering sanitization of sample psycopg2 OperationalError messages
- [X] T008 Verify `backend/src/api/router_modal_jobs.py` OpenAPI `responses` for scraper job routes include `503` with `ErrorResponse` wherever persistence can be misconfigured (align decorator metadata with runtime behavior)

**Checkpoint**: Foundation for safe scraper-job errors and operator docs is in place.

---

## Phase 3: User Story 1 — Scraping jobs work end-to-end (Priority: P1) 🎯 MVP

**Goal**: `POST/GET /api/v1/modal-jobs/scraper` and `{job_id}` / `cancel` return contract-correct outcomes when dependencies are healthy; no undocumented `5xx` from recoverable misconfig.

**Independent Test**: Staging or production-like env: create → list → get → cancel without server-error class failures; **SC-001** smoke (100 iterations) and `make test-schemathesis-cli` pass for those operations on the gated deployment.

### Tests for User Story 1

- [X] T009 [P] [US1] Expand `backend/tests/test_api/test_router_modal_jobs.py` with cases for gateway-owned persistence (mock `modal_scraper_persist` / DB) asserting **404** for unknown `job_id` and **non-5xx** for disabled Modal when contract says **503**
- [X] T010 [P] [US1] Add regression test in `backend/tests/test_services/test_modal_scraper_persist.py` (create if missing) asserting DB DNS / connection errors surface sanitized messages via `gateway_dependency_errors`

### Implementation for User Story 1

- [X] T011 [US1] Implement **FR-006** end-to-end: (a) ensure every `POST/GET /api/v1/modal-jobs/scraper` and `{job_id}` / `cancel` response (2xx/4xx/5xx) includes a stable correlation identifier (header and/or JSON field consistent with gateway `ErrorResponse`); update `backend/src/api/router_modal_jobs.py` and, if needed, request middleware in `backend/src/main.py`; (b) propagate that same identifier into the `payload` dict passed to `invoke_modal_scrape_job_submit` (`backend/src/services/modal/invoker.py` and its call sites) using a field the scraper accepts (e.g. nested under `metadata` or a documented top-level key); extend `backend/tests/test_api/test_router_modal_jobs.py` and add or extend tests under `backend/tests/test_services/` or `backend/tests/test_api/` asserting the identifier appears on sample HTTP responses and inside the constructed submit payload
- [X] T012 [US1] Trace all exception paths in `backend/src/api/router_modal_jobs.py` that turn DB/Modal failures into responses; ensure each uses sanitized messages from `backend/src/utils/gateway_dependency_errors.py` and preserves the same correlation identifiers as **T011**
- [X] T013 [US1] Confirm `backend/src/services/ingestion/modal_scraper_persist.py` uses `get_resolved_database_url()` consistently and document any required env in `specs/003-consolidate-scraper-dm/quickstart.md` **section 1** (Verify gateway / Modal DB split)
- [ ] T014 [US1] Execute `specs/003-consolidate-scraper-dm/quickstart.md` **section 1** curl checks against staging; append outcomes to `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md`
- [X] T015 [US1] Add `backend/scripts/smoke_modal_scraper_jobs.py` that runs **100** valid create/list/get/cancel sequences against a configurable gateway base URL and auth; exit non-zero if **SC-001** is unmet (<99% non-5xx); document CLI flags in `specs/003-consolidate-scraper-dm/quickstart.md` **section 4** (SC-001 smoke)
- [ ] T016 [US1] Run `make test-schemathesis-cli` from repo root; iterate on `backend/src/api/router_modal_jobs.py`, `backend/src/services/ingestion/modal_scraper_persist.py`, or **Render/Modal env** until **zero** server-error class failures on `/api/v1/modal-jobs/scraper*` (document any env-only waiver with owner sign-off in `baseline-notes-schemathesis.md`)

**Checkpoint**: US1 satisfies **SC-001** (via **T015**), **SC-004** (via **T016**), and **FR-006** (via **T011**).

---

## Phase 4: User Story 2 — One clear home for scraper capability (Priority: P2)

**Goal**: Single canonical scraper source under `services/scraper/`; DM API never embeds duplicate scraper **business logic** (remote HTTP only per clarification **B**).

**Independent Test**: Repo-wide search shows no second `vecinita_scraper` package used for DM API behavior; contributor doc points to `services/scraper/`.

- [X] T017 [P] [US2] Update root `README.md` or `CONTRIBUTING.md` with an explicit **“Canonical scraper”** subsection linking to `services/scraper/` and `specs/003-consolidate-scraper-dm/contracts/dm-api-remote-service-integration.md`
- [X] T018 [P] [US2] Update `services/scraper/README.md` (create if absent) stating it is the only scraper implementation tree and listing how DM API should call it (HTTP base URL)
- [X] T019 [US2] Migrate **consumer modules outside** `apis/data-management-api/apps/backend/scraper-service/` that still import the submodule path or duplicate scraper orchestration so they use `apis/data-management-api/packages/service-clients/service_clients/scraper_client.py` only (no parallel business logic); avoid relying on long-lived feature work **inside** the submodule tree before **T027** deletes it
- [X] T020 [US2] Add focused pytest under `apis/data-management-api/packages/service-clients/tests/` (create folder if needed) mocking `httpx` for `ScraperClient` success and upstream **5xx** mapping to stable client errors

**Checkpoint**: Maintainer story **SC-002** documentation path is real; clients route through `service_clients`.

---

## Phase 5: User Story 3 — Simpler data-management API footprint (Priority: P2)

**Goal**: Remove `scraper-service`, `embedding-service`, and `model-service` **git submodules**; DM API relies on env-configured remote URLs and `packages/service-clients`.

**Independent Test**: `apis/data-management-api/.gitmodules` has no entries for those three backends; `git clone --recurse-submodules` no longer pulls them; parity suite passes.

### Tests for User Story 3

- [X] T021 [P] [US3] Create `apis/data-management-api/tests/parity/test_remote_clients_parity.py` (or `tests/parity/` per plan) with JSON-normalized fixtures comparing mocked legacy submodule responses vs `ScraperClient`/`EmbeddingClient`/`ModelClient` behavior for the same logical operations
- [X] T022 [P] [US3] Add CI-friendly unit tests with `respx` or `httpx.MockTransport` in `apis/data-management-api/packages/service-clients/tests/test_embedding_client.py` and `test_model_client.py` mirroring patterns used for scraper client

### Implementation for User Story 3

- [X] T023 [US3] Extend `apis/data-management-api/packages/shared-config/` (or the existing settings module used by DM API entrypoints) to load `SCRAPER_SERVICE_BASE_URL`, `EMBEDDING_SERVICE_BASE_URL`, `MODEL_SERVICE_BASE_URL` per `specs/003-consolidate-scraper-dm/contracts/dm-api-remote-service-integration.md`
- [X] T024 [US3] Fill in missing methods on `apis/data-management-api/packages/service-clients/service_clients/embedding_client.py` and `model_client.py` required by consumers found in `inventory-dm-api-submodule-imports.md`
- [X] T025 [US3] Replace imports from submodule paths in DM API consumer modules (paths listed in `inventory-dm-api-submodule-imports.md`) with calls into `packages/service-clients`; confirm **no regression** to ingestion safeguards (robots, rate limits, retention defaults) by running existing scrape-related tests in `services/scraper/` / DM API suites touched by the change, or document “no logic change” in the PR with reviewer sign-off (constitution **III**)
- [X] T026 [US3] Run parity tests (`apis/data-management-api/tests/parity/…`) until diffs are empty or documented deltas are approved in `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md`
- [X] T027 [US3] Remove submodule directories `apis/data-management-api/apps/backend/scraper-service/`, `embedding-service/`, and `model-service/` from the tracked tree per git submodule removal procedure
- [X] T028 [US3] Edit `apis/data-management-api/.gitmodules` to delete the three submodule sections and update root `.github/workflows/*.yml` (and `Makefile` targets if any) that run `git submodule update` for DM API
- [X] T029 [US3] Update `render.yaml` and any DM API Docker build docs so images/build contexts do not assume submodule checkout of those three services
- [X] T030 [US3] Refresh `apis/data-management-api/README.md` setup steps: remote base URLs, sample `.env`, and removal of submodule init instructions

**Checkpoint**: **SC-003** binary satisfied; US3 acceptance scenarios hold.

---

## Phase 6: User Story 4 — Ask answers within tolerable time (Priority: P3)

**Goal**: Reduce live `504` / timeout failures on `GET /api/v1/ask` for representative questions (**FR-007** / **SC-005**).

**Independent Test**: Benchmark shows ≥18/20 successes per day over three consecutive days in staging, or documented mitigation ships (**T035**).

- [X] T031 [P] [US4] Measure current gateway → agent timeout chain in `backend/src/` (search `timeout`, `ask`, agent client) and document findings in `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md`; add an **“Ask SLO agreement”** subsection there with any numeric tail-latency or success-rate targets **beyond SC-005** (per spec Assumption on FR-007), including owner and date
- [X] T032 [US4] Adjust gateway/agent HTTP client timeouts or async behavior in the identified module(s) under `backend/src/` without weakening **FR-002** error safety
- [X] T033 [US4] If needed, align `GET /api/v1/ask` OpenAPI parameter constraints in `backend/src/api/models.py` (and route definitions) with runtime validation to reduce Schemathesis schema mismatch rejections for ask
- [X] T034 [US4] Re-run `make test-schemathesis-cli` focusing on ask operation; record pass rate in `baseline-notes-schemathesis.md`
- [X] T035 [US4] Add `backend/scripts/benchmark_ask_three_day.sh` (or `benchmark_ask_three_day.py`) plus a short runbook in `specs/003-consolidate-scraper-dm/quickstart.md` **section 5** (SC-005 benchmark): invokes the **20-question** set from **SC-005** on **three consecutive calendar days**, logs daily success counts, exits non-zero if any day falls below **18** successes unless a signed waiver is recorded in `baseline-notes-schemathesis.md`

**Checkpoint**: US4 demonstrably improved or limits documented with client mitigation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Schemathesis **warnings**, TraceCov thresholds, and repo-wide consistency after primary stories.

**Prerequisite**: **T001** MUST be completed before **T037** so `baseline-notes-schemathesis.md` contains the anchored schema-mismatch operation list.

- [X] T036 [P] Extend `backend/tests/schemathesis_hooks.py` to supply valid `gateway_job_id`, document preview/download identifiers, and scrape job IDs via env vars documented in `backend/scripts/run_schemathesis_live.sh`
- [X] T037 [P] Align OpenAPI/FastAPI models for the seven “schema mismatch” operations listed in `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md` (populated by **T001**) — primary files `backend/src/api/models.py` and routers under `backend/src/api/`
- [X] T038 Resolve TraceCov / `SCHEMATHESIS_COVERAGE_FAIL_UNDER` policy: either raise coverage for `POST /api/v1/scrape/reindex` or document an intentional threshold override path in `TESTING_DOCUMENTATION.md` and `backend/schemathesis.toml`
- [X] T039 Update `specs/003-consolidate-scraper-dm/quickstart.md` with final operator commands and links to Render dashboard env groups
- [X] T040 Run `make ci` from repository root and fix any regressions introduced by the above tasks
- [X] T041 Update `specs/003-consolidate-scraper-dm/spec.md` header **Status** to `Complete` (or `Ready for review`) **only when all** of the following are satisfied: **FR-001**–**FR-007**; **SC-002** (docs links live); **SC-003** (submodules removed); **SC-001** (**T015** green); **SC-004** / **FR-005** (live Schemathesis gate green or documented waiver); **SC-005** (**T035** green or documented signed waiver in `baseline-notes-schemathesis.md`); **FR-006** verified via **T011** (HTTP surface **and** Modal submit payload propagation). Otherwise set **Status** to a partial milestone agreed in `baseline-notes-schemathesis.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** → **Phase 2** → **US1 (Phase 3)** can proceed before DM submodule removal work, but **US3** must not delete submodules until **US2**/**US3** parity/client tasks (**T021–T026**) pass.
- **US4** can proceed in parallel engineering tracks once **Phase 2** is done (soft dependency on gateway code familiarity).
- **Polish (Phase 7)** depends on US1 baseline being stable; partial polish (**T036**–**T037**) can start after US1.

### User Story Dependencies

| Story | Depends on |
|-------|------------|
| **US1** | Phase 2 |
| **US2** | Phase 2; benefits from US1 env stability but not strictly blocking |
| **US3** | US2 client packaging + parity tasks **T021–T026** before **T027–T030** |
| **US4** | Phase 2 |

### Parallel Opportunities

- **T002**, **T003**, **T009**, **T010**, **T017**, **T018**, **T021**, **T022**, **T031**, **T036**, **T037** can run in parallel when staffed (distinct artifacts).
- After Phase 2: one developer on **US1**, another on **service_clients** tests (**T020**, **T022**) while parity fixtures (**T021**) are authored.

### Parallel Example: User Story 3 (early)

```bash
# After T023 starts (settings), parallelize client tests:
# Task T021 — parity fixtures
# Task T022 — embedding/model client unit tests
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1–2.  
2. Complete Phase 3 (**T009–T016**).  
3. STOP: verify **T015** (SC-001) and `make test-schemathesis-cli` (**T016**) for `/api/v1/modal-jobs/scraper*`.

### Incremental Delivery

1. US1 → deploy env fixes + gateway code.  
2. US2 + US3 → remote clients + submodule removal + CI.  
3. US4 + Polish → ask latency + contract hygiene.

### Task counts

| Area | Count |
|------|------|
| Phase 1 | 3 |
| Phase 2 | 5 |
| US1 | 8 |
| US2 | 4 |
| US3 | 10 |
| US4 | 5 |
| Polish | 6 |
| **Total** | **41** |

---

## Notes

- Submodule removal (**T027–T028**) is destructive; ensure **T026** parity sign-off exists.  
- If a task discovers `apps/backend/scraper-service` is the only runtime entrypoint today, split **T025** into smaller PR-sized commits per consumer module listed in the inventory file.  
- Keep **FR-002** in mind for any new `HTTPException(detail=...)` strings.

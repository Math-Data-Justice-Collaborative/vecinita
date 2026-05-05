# Tasks: OpenAPI SDK clients and standardized service URLs

**Input**: Design documents from `/specs/015-openapi-sdk-clients/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md), [contracts/modal-http-ban-sc005.md](./contracts/modal-http-ban-sc005.md), [quickstart.md](./quickstart.md)

**Tests**: Included where spec mandates verification (**SC-005**, **FR-007**, contract drift, `make ci`).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Parallel-safe (different files, no ordering dependency within the same sub-bullet group)
- **[USn]**: Maps to **User Story n** in [spec.md](./spec.md)

## Phase 1: Setup (shared infrastructure)

**Purpose**: Repository layout, pattern list, and generator pin so later phases do not thrash paths.

- [X] T001 Create `packages/openapi-clients/` layout (`python/gateway`, `python/data_management`, `python/agent`, `typescript-axios/gateway`, `typescript-axios/data_management`, `typescript-axios/agent`, optional `typescript-node/…`) and `packages/openapi-clients/README.md` describing ownership per [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md)
- [X] T002 [P] Add `config/modal_http_ban_patterns.txt` (one pattern per line) per [contracts/modal-http-ban-sc005.md](./contracts/modal-http-ban-sc005.md) and link it from that contract if the path differs
- [X] T003 [P] Add pinned OpenAPI Generator version file at `scripts/openapi-generator-version.txt` (or `openapitools.json` at repo root) per [research.md](./research.md) Decision 1
- [X] T004 [P] Add `scripts/openapi_codegen.sh` (or `scripts/openapi_codegen.py`) that reads `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, `AGENT_SCHEMA_URL`, invokes generator with `-g python-pydantic-v1`, `typescript-axios`, and optional `typescript-node`, writes under `packages/openapi-clients/` per contract
- [X] T005 [P] Add `.openapi-generator-ignore` files beside each generated tree (or root ignore rules) so manual files are not clobbered, per [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md)

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: **SC-005** gate, **FR-003** automation hooks, and `make ci` wiring. **No user-story implementation should merge without this phase complete** (except coordinated WIP behind feature flags agreed in PR).

**Checkpoint**: `make check-modal-http` and `make openapi-codegen-verify` exist locally; scripts are executable from repo root.

- [X] T006 Implement `scripts/check_modal_http_ban.py` per [contracts/modal-http-ban-sc005.md](./contracts/modal-http-ban-sc005.md) (read `config/modal_http_ban_patterns.txt`, respect `node_modules/`, `.venv/`, `venv/`, `dist/`, build artifacts; exit non-zero when any **FR-001**-listed HTTP client targets a blocked host: Python **`httpx`**, **`requests`**, **`urllib.request`/`urllib` URL openers**, plus **`fetch`** / **Axios** in `frontend/` and `apps/data-management-frontend/` where static analysis is feasible—document any intentional gap in the script header)
- [X] T007 Add `Makefile` targets `openapi-codegen`, `openapi-codegen-verify`, and `check-modal-http` at repository root `Makefile` delegating to `scripts/openapi_codegen.sh` and `scripts/check_modal_http_ban.py`
- [X] T008 Add `backend/tests/scripts/test_modal_http_ban.py` asserting `scripts/check_modal_http_ban.py` exits **0** on a clean tree once US3 removals land (start with `@pytest.mark.skip` until baseline fixed, then enable—document in test docstring; do **not** use a misleading “codegen_layout” filename). **T029 extends this same module** with fixture-based violation cases—implement **T008** first so the file exists before **T029**.
- [X] T009 Add a **`make check-modal-http`** step in `.github/workflows/quality-gate.yml` (near end of `backend-quality` or a lightweight job) **during Phase 2** so wiring exists early, but the step **MUST NOT fail the workflow** until US3 is green: use `continue-on-error: true`, an explicit `if:` guard (e.g. only on this feature branch or after a repo variable flip), or equivalent—**T036** removes the soft gate and makes the step a **required** merge check once `make check-modal-http` passes on the branch (**T035**). (Resolves phase-vs-wording ambiguity: “after US3” means **green tree / hard gate timing**, not “defer editing the YAML until Phase 5.”)
- [X] T010 [P] Add CI job or step to run `make openapi-codegen-verify` **only when** repository/organization variables `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, and `AGENT_SCHEMA_URL` are all non-empty (otherwise **skip** the step with a clear log line) in `.github/workflows/quality-gate.yml` or `.github/workflows/test.yml`; on full env, fail on diff if committed generated trees drift
- [X] T011 Document generator and `check-modal-http` commands in root `README.md` and add a short “OpenAPI clients & env” subsection in root `CONTRIBUTING.md` linking to `README.md` and [quickstart.md](./quickstart.md) (both files exist—keep **README** as the canonical command reference)

---

## Phase 3: User Story 1 — Operators deploy with one clear connection surface (Priority: P1)

**Goal**: **FR-004–FR-006**, **SC-001**: only approved URL env vars for connectivity; deprecated vars gone from manifests and examples.

**Independent Test**: Grep `render.yaml`, `docs/deployment/`, `.env*.example`, and `frontend`/`apps` env templates—no deprecated keys; staging smoke still passes when set per [quickstart.md](./quickstart.md).

### Implementation for User Story 1

- [X] T012 [US1] Audit and remove `MODAL_OLLAMA_ENDPOINT`, `MODAL_EMBEDDING_ENDPOINT`, `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, `EMBEDDING_SERVICE_URL` from committed **example** env files (e.g. `.env.local.example`, `backend/.env.example` if present) without re-adding secrets—use placeholders only in `docs/deployment/`
- [X] T013 [US1] Update `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` so connectivity URLs match **FR-004** only; mark deprecated vars as removed with migration pointer to this spec; add an explicit **FR-006** note that operators must not introduce parallel “shadow” base-URL variables for the same logical destination as `RENDER_GATEWAY_URL` / `RENDER_AGENT_URL` / `DATA_MANAGEMENT_API_URL` (list legacy names to delete)
- [X] T014 [US1] Update `render.yaml` (and any `render.*.yaml` fragments) so no service sets the five forbidden vars; align gateway/agent/DM env groups with `DATABASE_URL`, `RENDER_GATEWAY_URL`, `RENDER_AGENT_URL`, `DATA_MANAGEMENT_API_URL`, schema URL vars
- [X] T015 [P] [US1] Update `docs/deployment/MODAL_DEPLOYMENT.md` to state **SDK-only** to Modal compute (per clarification B) and list Modal **token** vars separately from **HTTP base** vars
- [X] T016 [US1] Grep and fix Python settings modules that still read forbidden names (e.g. `backend/src/config/`, `backend/src/settings.py`, `apis/data-management-api/**/settings*`) replacing resolution with `RENDER_GATEWAY_URL` / `RENDER_AGENT_URL` / `DATA_MANAGEMENT_API_URL` + generated clients (stub behind feature flag only if unavoidable—prefer direct cut)
- [X] T017 [P] [US1] Grep and fix `frontend/` and `apps/data-management-frontend/` Vite env templates (`*.example`, `vite.config.ts` docs) for forbidden vars
- [X] T018 [US1] Run staging smoke checklist from [quickstart.md](./quickstart.md) section 1–3 and record results in PR description; for **SC-004**, when **`docs/deployment/SC004_STAGING_RELEASE_CHECKLIST.md`** exists (**T045**), link it and note baseline date; **until T045 merges**, state that the operator checklist is **pending**, link [quickstart.md](./quickstart.md) §7 (Staging release), and point to **T045** in this `tasks.md` so early US1 PRs stay honest

**Checkpoint**: US1 satisfied when deprecated vars are absent from committed templates and docs describe only approved URL set.

---

## Phase 4: User Story 2 — Developers use generated OpenAPI clients (Priority: P1)

**Goal**: **FR-002**, **FR-003**, **FR-007**, **SC-002**, **SC-003** — OpenAPI Generator outputs consumed by Python and TS; drift fails CI; hand-written paths migrated.

**Independent Test**: `make openapi-codegen-verify` green; grep shows no non-generated `"/api/v1/` string construction for gateway/DM/agent in app layers listed in [plan.md](./plan.md); Schemathesis still passes per `TESTING_DOCUMENTATION.md`.

### Tests for User Story 2

- [X] T019 [P] [US2] Add regression test `backend/tests/test_generated_gateway_client_import.py` that imports the generated gateway client package and performs a trivial model round-trip; use **`pytest.skip`** **only** under the **same “all three schema URL vars unset”** condition as **T010** (document in test module)—if any schema URL is set in CI, the test **must run** so **FR-002** regressions fail the job; avoid a vague “minimal CI” skip that always skips
- [X] T020 [P] [US2] Add `frontend/src/app/lib/openapi-generated-client-basepath.test.ts` (Vitest) asserting the generated gateway or agent axios client receives the same resolved base URL as existing helpers in `frontend/src/app/lib/apiBaseResolution.test.ts` (update import paths after `packages/openapi-clients/typescript-axios/` is wired)

### Implementation for User Story 2

- [ ] T021 [US2] Run `make openapi-codegen` once with valid schema URLs; commit generated trees under `packages/openapi-clients/` **or** commit checksum manifest per [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md)—pick one approach in PR and align T010
- [ ] T022 [US2] Add thin Python wrapper module `backend/src/services/http_clients/gateway_client.py` (or extend existing package) that configures generated gateway client with `RENDER_GATEWAY_URL` + auth from existing middleware patterns
- [ ] T023 [P] [US2] Migrate high-traffic gateway call sites in `backend/src/services/` from hand `httpx` URLs to generated client (incremental PRs per subdirectory: `llm/`, `embedding_service/`, `scraper/` as applicable)
- [ ] T024 [P] [US2] Migrate `apis/data-management-api/packages/service-clients/` HTTP helpers to generated **DM** Python client from `packages/openapi-clients/python/data_management/`
- [ ] T025 [US2] Replace `apps/data-management-frontend/package.json` script `codegen:api` path away from **only** `openapi-typescript` snapshot: add `openapi-codegen` npm script calling OpenAPI Generator `typescript-axios` into `apps/data-management-frontend/src/app/api/generated/` (or shared package) per [research.md](./research.md) Decision 4
- [ ] T026 [P] [US2] Update `frontend/` services that call gateway/agent to consume `typescript-axios` generated clients from `packages/openapi-clients/typescript-axios/` with `VITE_*` base URL wiring
- [ ] T027 [US2] Ensure **FR-007**: add or extend live/smoke test in `backend/tests/live/` or documented `make` target using generated clients against `RENDER_GATEWAY_URL` / `DATA_MANAGEMENT_API_URL` / `RENDER_AGENT_URL` when env present
- [ ] T028 [US2] Track migration coverage: add `specs/015-openapi-sdk-clients/artifacts/handwritten-http-inventory.md` listing remaining non-generated call sites until **SC-002** ≥95% (update each PR). **SC-002 baseline:** the **first committed revision** of that inventory on branch `015-openapi-sdk-clients` (or its superseding PR note) defines the denominator “previous hand-written” count unless the PR explicitly revises baseline with rationale. Optionally add `scripts/openapi_migration_metrics.py` (see **T046** for a packaged variant) printing counts to speed reviews

**Checkpoint**: US2 satisfied when CI enforces codegen drift and inventory shows ≤5% exceptions documented.

---

## Phase 5: User Story 3 — Modal SDK only, no HTTP to Modal hosts (Priority: P1)

**Goal**: **FR-001**, **FR-005** behavioral half, **SC-001**, **SC-005** — remove `httpx`/`requests` to `*.modal.run` everywhere including `modal-apps/scraper/`.

**Independent Test**: `make check-modal-http` exits 0; Modal flows use `modal.Function.from_name` / `.remote()` in `backend/src/services/modal/invoker.py`, `packages/service-clients/service_clients/modal_invoker.py`, and scraper Modal modules.

### Tests for User Story 3

- [ ] T029 [P] [US3] Extend **`backend/tests/scripts/test_modal_http_ban.py`** (created in **T008**) with unit tests that invoke `scripts/check_modal_http_ban.py` against synthetic violation fixtures under `backend/tests/fixtures/modal_http_ban/` (depends on **T008** landing first)

### Implementation for User Story 3

- [ ] T030 [US3] Inventory all Python `httpx`/`requests` calls to hosts matching `config/modal_http_ban_patterns.txt` under `backend/`, `modal-apps/scraper/`, `apis/data-management-api/`; list in `specs/015-openapi-sdk-clients/artifacts/modal-http-inventory.md`
- [ ] T031 [P] [US3] Refactor `backend/src/services/modal/invoker.py` and `apis/data-management-api/packages/service-clients/service_clients/modal_invoker.py` so **no** code path issues HTTP to Modal hosts (SDK-only per spec)
- [ ] T032 [P] [US3] Refactor `backend/src/embedding_service/modal_embeddings.py` and `backend/src/services/llm/client_manager.py` to remove Modal HTTP URLs; route via Modal SDK or Gateway/DM generated clients
- [ ] T033 [P] [US3] Refactor `modal-apps/scraper/` Modal entry modules (`modal-apps/scraper/modal_api_entry.py`, `modal_workers_entry.py`, `backend/src/services/scraper/modal_app.py`) to eliminate HTTP client calls to Modal deployment hosts
- [ ] T034 [US3] Remove any remaining reads of `MODAL_OLLAMA_ENDPOINT`, `MODAL_EMBEDDING_ENDPOINT`, `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, `EMBEDDING_SERVICE_URL` from Python/TS runtime code (`rg` across repo; exclude `specs/` prose)
- [ ] T035 [US3] Enable `backend/tests/scripts/test_modal_http_ban.py` (from T008) fully—remove skips once `make check-modal-http` is green on branch
- [ ] T036 [US3] Flip CI (T009) from optional to **required** merge gate once green on `015-openapi-sdk-clients`

**Checkpoint**: US3 satisfied when SC-005 and SC-001 grep gates pass on CI.

---

## Phase 6: User Story 4 — Documentation and GitHub Pages (Priority: P2)

**Goal**: **FR-008**, **SC-003** — docs and workflows describe codegen + approved env only.

**Independent Test**: `docs-gh-pages` build job succeeds; published env tables contain no deprecated Modal URL vars.

### Implementation for User Story 4

- [ ] T037 [US4] Update `.github/workflows/docs-gh-pages.yml` (and any mkdocs/docusaurus config under `docs/`) to document `openapi-codegen` / `check-modal-http` and the seven approved URL env vars per [quickstart.md](./quickstart.md)
- [ ] T038 [P] [US4] Update `TESTING_DOCUMENTATION.md` with subsection linking `make openapi-codegen-verify`, `make check-modal-http`, and schema URL variables for contract testing
- [ ] T039 [P] [US4] Add cross-links from `docs/deployment/GATEWAY_LIVE_OPERATIONS.md` (if present) to this feature’s contracts for operator runbooks
- [ ] T040 [US4] Validate contributor time for [quickstart.md](./quickstart.md) flow (SC-003); trim or script steps if >30 minutes on clean laptop—edit `quickstart.md` accordingly

**Checkpoint**: US4 satisfied when docs PR preview shows correct env + regen story.

---

## Phase 7: Polish and cross-cutting

**Purpose**: Exceptions register (**SC-002**), final `make ci`, and spec/plan drift control.

- [ ] T041 [P] Finalize `specs/015-openapi-sdk-clients/artifacts/sc-002-exceptions.md` documenting any allowed handwritten HTTP exceptions with owner + removal date (**SC-002**); reference the inventory baseline from **T028** when claiming the ≥95% migration ratio
- [ ] T042 [P] Align [plan.md](./plan.md) **Source code** tree with actual package names chosen during T021–T026 if paths diverged
- [ ] T043 Run `make ci` from repository root and fix failures until green
- [ ] T044 [P] Update `specs/015-openapi-sdk-clients/checklists/requirements.md` if spec/plan changed during implementation (keep checklist honest)
- [ ] T045 [P] Create `docs/deployment/SC004_STAGING_RELEASE_CHECKLIST.md` for **SC-004**: capture pre-deploy baseline (date, commit), metrics source (e.g. Render dashboard / gateway logs), end-to-end journey script, one-week calendar reminder, rollback owner—link from `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` or release runbook; add a “See also” link to [quickstart.md](./quickstart.md) §7 (Staging release)
- [ ] T046 [P] Add optional `scripts/openapi_migration_metrics.py` that reports counts/ratios of handwritten vs generated Gateway/DM/Agent HTTP usage (feeds **SC-002**); align with **`specs/015-openapi-sdk-clients/artifacts/handwritten-http-inventory.md`** from **T028** so metrics and manual inventory do not diverge
- [ ] T047 [P] Add a PR template checkbox or `docs/deployment/` “Release” note referencing **T045** so **SC-004** is not dropped at ship time: check in order and edit the first that exists—`.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md`, or root `pull_request_template.md`; if none exist, add a short **Release** subsection to `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` instead

---

## Dependencies and execution order

### Phase dependencies

| Phase | Depends on | Notes |
|-------|------------|--------|
| 1 Setup | — | Start immediately |
| 2 Foundational | Phase 1 | **T009** lands the `check-modal-http` step as **non-blocking** until **T036**; strict gate follows US3 (**T035** green) |
| 3 US1 | Phase 1 | Can overlap with Phase 2 documentation tasks [P] |
| 4 US2 | Phase 1 + partial Phase 2 (T007 required for verify target) | Codegen needs scripts from Phase 1–2 |
| 5 US3 | Phase 2 script T006–T007 (local ban); **should complete before T036** | Removes violations SC-005 detects |
| 6 US4 | US1–US3 substantive progress | Docs reflect final behavior |
| 7 Polish | US1–US4 | Final gate; **T045–T047** close **SC-004** / release process gaps |

### User story dependencies

- **US1** stands alone for operator/env surfaces.
- **US2** depends on codegen scaffolding (Phase 1–2) and benefits from US1 env cleanup.
- **US3** must finish before SC-005 is merge-blocking (T036); interacts with US2 when replacing HTTP with generated clients to gateway/DM.
- **US4** documents outcomes from US1–US3.

### Parallel opportunities

- T002, T003, T004, T005 in Phase 1 can run in parallel.
- T012–T017 US1 tasks marked [P] can run in parallel after split by file family.
- T023–T024 vs T026 different top-level trees in parallel once T022 wrapper exists.
- T031, T032, T033 parallel Modal refactors if merge conflicts avoided per directory.

### MVP suggestion

Deliver **US1 + US3 + SC-005 gate** first (operator clarity + Modal safety), then **US2** (broader migration), then **US4** docs.

---

## Parallel example (User Story 2)

```bash
# After T022 lands, in parallel:
# Developer A: T023 backend/src/services/llm/
# Developer B: T024 apis/data-management-api/packages/service-clients/
# Developer C: T026 frontend/ axios client wiring
```

---

## Implementation strategy

1. Complete **Phase 1–2** so tooling exists.
2. **US1** + **US3** for compliance and CI safety (Modal ban green).
3. **US2** for OpenAPI client migration and drift CI.
4. **US4** for contributor/onboarding polish.
5. **Phase 7** + `make ci` (**T043**).

---

## Notes

- Do not commit real secrets from `.env`; use docs placeholders only.
- If `make check-modal-http` fails mid-branch, keep **T036** disabled until US3 complete (explicit PR state); **T009**’s workflow step should remain **`continue-on-error`** (or skipped) until then.
- Total tasks: **47** (T001–T047). **FR-006** shadow-URL prohibition is folded into **T013**.

# Tasks: Strict Canonical Monorepo Layout

**Input**: Design documents from `/specs/018-strict-monorepo-layout/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/monorepo-layout-boundary.md](./contracts/monorepo-layout-boundary.md), [quickstart.md](./quickstart.md)

**Tests**: Not requested as TDD in the feature spec; each slice MUST end with `make ci` from repository root per plan and constitution.

**Organization**: Phases follow user-story priorities from [spec.md](./spec.md). Structural work MUST cite `row_id` from [artifacts/path-mapping.md](./artifacts/path-mapping.md) (FR-013).

**Path-map policy (spec edge case)**: Any PR that changes directory layout or Render/Modal paths MUST update `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` (`status`, `notes`, or new rows) **in the same PR** as those edits—no merge with drifting plan/tasks vs map.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no ordering dependency within the same checkpoint)
- **[Story]**: `[US1]` … `[US5]` for user-story phases only
- Every description includes at least one concrete repo-relative path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inventory, path-map hygiene, and contributor-facing layout docs before moves.

- [x] T001 Ensure **`specs/`** is recorded as **PM-012** in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` (FR-006 traceability; identity mapping). Add `Makefile`, `.github/workflows/`, and root `docker-compose*.yml` path rows (**PM-013+** as needed) so CI and Render references are traceable
- [x] T002 [P] Add monorepo **target** tree and links to `specs/018-strict-monorepo-layout/plan.md` and `artifacts/path-mapping.md` in `README.md`
- [x] T003 [P] Create `docs/monorepo-layout.md` with a one-page canonical tree (target-only) for onboarding (SC-001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Canonical skeleton at repo root and Render path audit. **No user story work starts until this phase completes.**

- [x] T004 Add placeholder `README.md` files under new roots `apis/`, `modal-apps/`, `frontends/`, `clients/apis/`, and `packages/python/db/` describing ownership rules per `contracts/monorepo-layout-boundary.md` (empty packages are OK until moves land)
- [x] T005 Reconcile `specs/018-strict-monorepo-layout/plan.md` “Target (canonical)” tree with the directories created in T004 if any naming differs
- [x] T006 Audit `render.yaml` for every `dockerfilePath` / `dockerContext` pair affecting PM-001–PM-008 and record findings in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` `notes` column (include `vecinita-data-management-api-v1` → `services/scraper` today, PM-003)

**Checkpoint**: Foundation ready — physical `git mv` phases may begin.

---

## Phase 3: User Story 1 — Find the right home for a change (Priority: P1)

**Accountability**: **US1 = documentation and navigation only** (no production tree moves). **US2 (Phase 4) owns all filesystem / Render / Modal relocations.** Overlap is intentional: docs may describe paths before moves land; they must stay consistent with `artifacts/path-mapping.md`.

**Goal**: Contributors resolve legacy vs canonical locations using one map and short docs.

**Independent Test**: Given `artifacts/path-mapping.md` and `docs/monorepo-layout.md`, a reviewer answers “where does gateway HTTP live?” / “where is scraper Modal?” without contradiction (spec acceptance scenarios 1–4).

- [x] T007 [US1] Wire `docs/monorepo-layout.md` to explicitly instruct: resolve any path via `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` `row_id` first, then `plan.md` / this `tasks.md` (FR-013)
- [x] T008 [US1] Add “Where does X live?” table to `docs/monorepo-layout.md` for gateway, agent, data-management-api, scraper, embedding-modal, model-modal, chat UI, data-management frontend (pre- and post-move column or “see row PM-xxx”)

**Checkpoint**: US1 documentation sufficient for SC-001 dry-runs.

---

## Phase 4: User Story 2 — One folder, one deployable (Priority: P1)

**Accountability**: **US2 owns canonical directory moves, Dockerfiles, `render.yaml`, Makefile, and CI path updates.** See Phase 3 for doc-only ownership.

**Goal**: Each Render or Modal deployable has a single canonical folder; `render.yaml` and `Makefile` match moved paths.

**Independent Test**: `make ci` green after each row group; Render service `name:` in `render.yaml` still points at existing Dockerfiles (updated relative paths).

### Modal apps (lower coupling first)

- [x] T009 [P] [US2] `git mv` `services/embedding-modal/` → `modal-apps/embedding-modal/`; update `Makefile`, `.github/workflows/`, and any Modal/CI references; run `make ci`; set PM-004 to `done` in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` (PM-004)
- [x] T010 [P] [US2] `git mv` `services/model-modal/` → `modal-apps/model-modal/`; update `Makefile`, `.github/workflows/`, and docs; run `make ci`; set PM-005 to `done` in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` (PM-005)
- [x] T011 [US2] `git mv` `services/scraper/` → `modal-apps/scraper/`; update `render.yaml` paths for scraper **and** `vecinita-data-management-api-v1`, `Makefile`, `docker-compose*.yml`, CI; run `make ci`; set PM-003 to `done` with `notes` if DM API image still temporarily scraper-based (PM-003)

### Frontends

- [x] T012 [P] [US2] `git mv` `frontend/` → `frontends/chat/`; update `render.yaml` (`vecinita-frontend` Dockerfile/context), `Makefile` (`lint-frontend`, `dev-chat-frontend`, etc.), root scripts referencing `frontend/`; run `make ci`; set PM-001 `done` in `artifacts/path-mapping.md` (PM-001)
- [x] T013 [P] [US2] `git mv` `apps/data-management-frontend/` → `frontends/data-management/`; update `render.yaml`, `Makefile`, and workspace references; run `make ci`; set PM-002 `done` in `artifacts/path-mapping.md` (PM-002)

### Data-management API submodule

- [x] T014 [US2] Relocate `services/data-management-api/` git submodule to `apis/data-management-api/` (preserve submodule metadata per `research.md`); **prefer running after T011** (see `plan.md` ordering coherence) to reduce concurrent edits under `services/`; update `Makefile` PYTHONPATH blocks, CI, and docs pointing at old path; run `make ci`; set PM-006 `done` in `artifacts/path-mapping.md` (PM-006)

### Backend split (gateway + agent)

- [x] T015 [US2] Produce `specs/018-strict-monorepo-layout/artifacts/backend-split-inventory.md` listing `backend/src/` packages/files as **gateway-only**, **agent-only**, or **shared** with rationale (feeds PM-007, PM-008)
- [x] T016 [US2] Execute physical split: move agent tree to `apis/agent/` and gateway tree to `apis/gateway/` per inventory; relocate `backend/Dockerfile`, `backend/Dockerfile.gateway`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/src/`, `backend/tests/` as appropriate; update `render.yaml` (`vecinita-agent`, `vecinita-gateway`), `Makefile`, `.github/workflows/`; run `make ci`; set PM-007 and PM-008 `done` in `artifacts/path-mapping.md` (PM-007, PM-008)

**Checkpoint**: US2 satisfied — each deployable folder owns its Render/Modal entrypoints per spec.

---

## Phase 5: User Story 3 — Reuse without tangles (Priority: P2)

**Hard gate**: **Blocked until Phase 4 (US2) is complete** — `apis/agent/`, `apis/gateway/`, and `apis/data-management-api/` must exist as the canonical API roots before **FR-005** client work and before **PM-010** extraction targets are meaningful.

**Goal**: Shared API DB/session code lives under `packages/python/db/` without Modal coupling unless documented.

**Independent Test**: No duplicate DB session modules under `apis/agent/` and `apis/data-management-api/` after extraction; `make ci` green.

- [ ] T017 [US3] Inventory SQLAlchemy/session and migration glue under `apis/agent/` and `apis/data-management-api/`; append concrete source globs to PM-010 `notes` in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` (PM-010)
- [ ] T018 [US3] Move shared helpers into `packages/python/db/`; point `apis/agent/pyproject.toml` and `apis/data-management-api/` packages at the shared package (uv path or workspace per repo norms); remove duplicated modules; run `make ci`; set PM-010 `done` in `artifacts/path-mapping.md` (PM-010)
- [ ] T019 [US3] **FR-012 (conditional)**: Run **after T018** unless `artifacts/backend-split-inventory.md` (from **T015**) shows only schema-only modules that belong solely in **T018**. If cross-API request/response shapes are genuinely shared and extracted during this refactor, add `packages/python/shared-schemas/` (or the agreed equivalent), wire consumers, and add a **PM-** row; **else** append to `artifacts/path-mapping.md` `notes` (or a short row) that **FR-012 not exercised** for this refactor scope so reviewers do not assume an omission (PM-010 notes or new `row_id`)

---

## Phase 6: User Story 4 — Contract-first consumers (Priority: P2)

**Hard gate**: **Blocked until Phase 4 (US2) is complete** — first-party APIs must live under `apis/gateway/`, `apis/agent/`, and `apis/data-management-api/` so `clients/apis/<same-name>/` can mirror them per **FR-005**.

**Goal**: Generated or hand-maintained HTTP clients live under `clients/apis/<api-name>/` mirroring `apis/`.

**Independent Test**: `make openapi-codegen-verify` and `make ci` pass; imports resolve from `clients/apis/gateway/`, `clients/apis/agent/`, `clients/apis/data-management-api/`.

- [ ] T020 [US4] After PM-006–PM-008 are `done`, relocate outputs from `packages/openapi-clients/` into `clients/apis/gateway/`, `clients/apis/agent/`, and `clients/apis/data-management-api/`; update `openapitools.json`, `Makefile` `openapi-codegen` targets, and all TypeScript/Python imports across `frontends/chat/`, `frontends/data-management/`, `apis/*`; run `make openapi-codegen-verify` and `make ci`; set PM-009 `done` in `artifacts/path-mapping.md` (PM-009)

---

## Phase 7: User Story 5 — Supporting material stays discoverable (Priority: P3)

**Hard gate**: **Blocked until Phase 4 (US2) is complete** for any move that reads from relocated deployable paths; early `contracts/README.md` scaffolding may follow Phase 2 if it does not import moved paths. **T021** (moving HTTP snapshot / Pact **documentation** out of legacy paths): run **after** the Phase 4 checkpoint when those docs still reference old `backend/`, `services/`, or `frontend/` trees—otherwise update paths in the same PR as the doc move so links match the current tree.

**Goal**: Optional `contracts/` and `infra/` house snapshots and glue without duplicating deployable logic; `scripts/` owns repo automation.

**Independent Test**: Single canonical `render.yaml` story preserved (PM-011 / FR-008); pointers documented in `README.md` or `quickstart.md`.

- [ ] T021 [P] [US5] Create or extend top-level `contracts/README.md` and move applicable HTTP snapshot / Pact documentation from legacy doc locations into `contracts/` per `contracts/monorepo-layout-boundary.md` (list moved paths in `artifacts/path-mapping.md` with new `row_id`s); **if nothing moves**, record **N/A** and rationale in `contracts/README.md` for **FR-009** traceability
- [ ] T022 [P] [US5] If introducing `infra/` fragments, add files under `infra/` and a single pointer line in `README.md` while keeping root `render.yaml` primary (PM-011, FR-008)
- [ ] T023 [US5] Normalize repo-root automation: relocate **eligible** scripts into `scripts/` — e.g. root `dev-session.sh`, `scripts/github/*.sh`, and other **repo-wide** helpers that are not a service’s runtime entrypoint—and update `Makefile` / workflow references; **do not** move `apis/*/scripts/` or Modal app local utilities that belong with their deployable; add `artifacts/path-mapping.md` rows for each move (**PM-016+**; **PM-012–PM-015** reserved for `specs/`, Makefile, workflows, root compose)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Remove empty legacy shells, align contributor docs, close the path map.

**Preferred order (within this phase)**: **T024 → T025 → T026** — update **SC-002** / **FR-007** / **FR-006** docs (**T024**) before deleting empty legacy directories (**T025**), then run the final gate (**T026**). If `make ci` stays green, you may swap **T024**/**T025** only when no doc still depends on a path about to be removed.

- [ ] T024 [P] Update path references in **`README.md`** (deploy / layout sections per **SC-002**—re-verify after **T002** if that section predates moves), `CONTRIBUTING.md`, `TESTING_DOCUMENTATION.md`, **`.env.local.example`** (comments and examples that embed repo paths), **`DEPLOYMENT_QUICK_START.md`**, **`DEPLOYMENT_IMPLEMENTATION.md`**, and **`DEPLOY_DATA_MANAGEMENT_API.md`** when those files reference old roots—aligning **FR-007**, **SC-004**, and **SC-002**—with post-move locations under `apis/`, `modal-apps/`, `frontends/`, and **`clients/apis/<api>/`** (canonical for generated HTTP clients after **T020** / **PM-009**). Until **PM-009** is `done`, follow **`artifacts/path-mapping.md`** for any interim **`packages/openapi-clients/`** references; skim **`Makefile`** for stale path strings that violate **FR-006** discoverability
- [ ] T025 Delete or archive empty legacy directories (`apps/`, `services/` if fully evacuated) **or** add FR-011 time-bounded rows in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` with `owner` and `cutover_date` for any intentional leftovers
- [ ] T026 Run `make ci` from repository root. Then: (a) verify `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` has all structural `row_id` rows for completed work set to `done` with no contradictory second mapping doc elsewhere (**SC-006** spot-check); (b) **optionally**, append a one-page **SC-001** onboarding dry-run summary to `specs/018-strict-monorepo-layout/artifacts/sc-001-onboarding-dry-run.md` after `docs/monorepo-layout.md` exists (**SC-001** measurement)

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1** → **Phase 2** → **Phases 3–8** in order for safety (docs before risky moves; US2 before US3–US4 so paths exist for extraction/clients).
- **Phase 4 internal**: T009 ∥ T010 → **T011** (scraper/DM-api wiring). T012 ∥ T013 can run after Phase 2 (in parallel with T009–T011 if staffing allows). **T014** can overlap with frontend/modal tracks if merge conflicts avoided. **T015** → **T016** (hard sequence).
- **Phase 5–6**: Start only after Phase 4 completes (correct `apis/*` paths for PM-010 and PM-009).
- **Phase 7**: Can start after Phase 2 but SHOULD finish after Phase 4 if moves affect `contracts/` sources or **T021** content still names legacy deployable paths.

### User story completion order

1. **US1** (Phase 3) — can proceed in parallel with Phase 4 **only for doc work**; physical moves should follow Phase 2 regardless.
2. **US2** (Phase 4) — **MVP-critical** for deployable ownership; **US3, US4, and US5 implementation (Phases 5–7) MUST NOT merge before the Phase 4 checkpoint** unless the task explicitly allows doc-only work (US5 note).
3. **US3**, **US4**, **US5** — P2/P3 **after** US2 physical paths exist (`apis/*`, `modal-apps/*`, `frontends/*` per path map).

### Parallel opportunities

- **Phase 1**: T002 ∥ T003 after T001 lands.
- **Phase 4**: T009 ∥ T010; T012 ∥ T013; (optional) T014 parallel to modal/frontend tracks if coordinated.
- **Phase 7**: T021 ∥ T022.
- **Phase 8**: **T024** may run in parallel with other polish where paths do not overlap; **T026** runs **after** both **T024** and **T025** (optional **SC-001** work is step **(b)** inside **T026** only).

---

## Parallel Example: User Story 2 (modal slice)

```bash
# After Phase 2, launch embedding + model modal moves together:
# T009 [US2] embedding-modal → modal-apps/embedding-modal/ (PM-004)
# T010 [US2] model-modal → modal-apps/model-modal/ (PM-005)
# Then run T011 sequentially for scraper + DM API image paths (PM-003).
```

---

## Implementation Strategy

### MVP (US2 minimal slice)

1. Complete Phase 1–2.
2. Complete **Phase 4** through at least **one** deployable move (e.g., PM-004 only) with `make ci` to prove the pipeline.
3. Expand to full PM-003–PM-008 before declaring layout refactor “done”.

### Incremental delivery

1. Setup + Foundational (inventory + skeleton).
2. US1 docs for navigability.
3. US2 modal → frontends → submodule → backend split, each merge green.
4. US3 DB package extraction.
5. US4 client relocation (**T020**).
6. US5 contracts/infra/scripts polish (**T021–T023**); **FR-012** closure via **T019** when in scope.

### Task / path-map traceability

Every structural task above cites **`PM-xxx`** in parentheses. When implementing, update the matching `status` / `notes` in `specs/018-strict-monorepo-layout/artifacts/path-mapping.md` in the **same PR** as code moves (spec edge case: plan/tasks vs map drift).

---

## Notes

- Prefer **`git mv`** for traceability (`research.md`).
- Do not merge moves without **`make ci`** green at repo root.
- **Total tasks**: 26 (T001–T026)
- **By user story label**: US1: 2 · US2: 8 · US3: 3 · US4: 1 · US5: 3 · Setup: 3 · Foundational: 3 · Polish: 3

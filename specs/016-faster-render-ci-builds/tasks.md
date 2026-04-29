# Tasks: Faster Render builds and GitHub Actions CI

**Input**: Design documents from `/specs/016-faster-render-ci-builds/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Not requested as new automated tests in the feature spec; verification is **median timing**, **`make ci`**, and **before/after checklists**. Optional regression guard: existing Schemathesis/TraceCov thresholds must not be lowered without **FR-004** approval.

**Organization**: Phases follow user stories **US1** (P1 CI), **US2** (P2 Render builds), **US3** (P3 visibility). Setup and foundational work establish **FR-001** baselines before optimization PRs.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: `[US1]` / `[US2]` / `[US3]` for user-story phases only
- Paths are repo-root relative unless noted

---

## Phase 1: Setup (shared infrastructure)

**Purpose**: Measurement templates and contract alignment so later PRs stay auditable (**FR-005**, **FR-006**).

- [x] T001 Extend [quickstart.md](./quickstart.md) with a copy-paste **baseline table** (columns per [data-model.md](./data-model.md): `phase`, `change_category`, `median_sec`, `n_runs`, `cache_state`, `source`) and note **N ≥ 20** successful runs per [spec.md](./spec.md) **FR-001**; if **N < 20**, label rows **provisional** per spec Definitions
- [x] T002 [P] Audit repo paths against [contracts/ci-path-triggers.md](./contracts/ci-path-triggers.md) and update that file’s wide-trigger list to include every committed **OpenAPI snapshot**, **`packages/`** subtree, and both **`uv.lock`** / root **`package-lock.json`** paths that exist today
- [x] T003 [P] Audit [contracts/render-docker-build-layers.md](./contracts/render-docker-build-layers.md) against current `backend/Dockerfile` **COPY** order; document gaps in the contract file (no Dockerfile behavior change in this task)

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: **FR-001** — documented **before** metrics; no story declares victory without this checkpoint.

**⚠️ CRITICAL**: Complete this phase before merging optimization-heavy PRs for US1–US3.

- [x] T004 Create directory `specs/016-faster-render-ci-builds/artifacts/` and add `specs/016-faster-render-ci-builds/artifacts/baseline-pre-optimization.md` as the **governance artifact** anchor per [spec.md](./spec.md) Definitions with **two** sections. Create empty `specs/016-faster-render-ci-builds/artifacts/required-checks-inventory.md` stub (header only) if missing so **T017**/**T022** can append rows. **Layout:** **(A) Job-level inventory** — a table with one row per **job id** defined under `jobs:` in `.github/workflows/test.yml` (e.g. `workflow-context`, `secret-scan`, `backend-quality`, `frontend-quality`, `data-management-api-structure`, `embedding-modal-quality`, `model-modal-quality`, `scraper-quality`, `backend-ci`, `backend-integration`, `backend-schema-gateway`, `backend-schema-agent`, `backend-schema-data-management`, `frontend-unit`, `backend-integration-pgvector`, …) with columns `median_sec`, `n_runs`, `cache_state`, `provisional`, `source`; optionally add a column mapping each job to contributing **canonical change categories** for rollup notes; **(B) Category rollup** — paired **(a)**/**(b)** rows per **Definitions** canonical categories (where **(b)** applies), derived from or cross-referenced to section (A) plus **T005** Render data; mark **provisional** if **N < 20** per **FR-001**; if branch-protection **required** checks are a strict subset of `test.yml` jobs, attach an export or link under **(A)** and note exclusions
- [x] T005 Append **Render** code-only deploy **build-phase** medians (per service in `render.yaml` using `backend/Dockerfile`) to `specs/016-faster-render-ci-builds/artifacts/baseline-pre-optimization.md` with sampling dates and links or export references

**Checkpoint**: Baseline artifact exists — **US1**/**US2** optimization work may proceed.

---

## Phase 3: User Story 1 — Faster CI feedback (Priority: P1) 🎯 MVP

**Goal**: Shorter wall-clock from push to all required checks green for high-frequency change categories, **without** removing checks (**FR-002**, **FR-007**, **SC-003**).

**Independent Test**: Median **workflow** or **job** duration for the primary PR path drops **≥ 20%** vs `specs/016-faster-render-ci-builds/artifacts/baseline-pre-optimization.md` for the same **change_category**; `make ci` still passes locally.

### Implementation for User Story 1

- [x] T006 [US1] Enable **uv** dependency cache for `backend/uv.lock` in `.github/workflows/test.yml` job `backend-quality` using `astral-sh/setup-uv` cache options or `actions/cache` keyed on the lockfile hash
- [x] T007 [P] [US1] Enable the same **uv** cache pattern in `.github/workflows/quality-gate.yml` job `backend-quality` for the `uv sync --frozen --extra ci` step
- [x] T008 [US1] Refactor `.github/workflows/test.yml` job `backend-schema` so **gateway**, **agent**, and **data-management** Schemathesis pytest invocations run as **three parallel jobs** (or a matrix), each preserving current env vars and **TraceCov** HTML/JUnit outputs; merge artifact upload into one **upload-artifact** step per job or a single summary job that depends on the three
- [x] T009 [US1] Add `--tracecov-fail-under=100` to each Schemathesis pytest command in `.github/workflows/test.yml` **backend-schema** split jobs if missing, matching `Makefile` targets `test-schemathesis-gateway`, `test-schemathesis-agent`, `test-schemathesis-data-management`
- [x] T022 [US1] When completing **T008**/**T009**, if GitHub **check names or job identifiers** seen by branch protection change, either preserve user-visible check stability **or** append **EquivalenceRecord** rows to `specs/016-faster-render-ci-builds/artifacts/required-checks-inventory.md` (create stub in Phase 2 if empty) per **FR-004**; cite the PR link in that file
- [x] T010 [US1] If introducing `paths` / `paths-ignore` or `dorny/paths-filter` on `.github/workflows/test.yml`, add a first step that **echoes** rule ids and booleans per [contracts/ci-path-triggers.md](./contracts/ci-path-triggers.md) (**FR-006**); ensure **default branch** pushes still run the full required set per contract; if no path filters ship, record “**T010 N/A** — no path filters” in `specs/016-faster-render-ci-builds/artifacts/baseline-pre-optimization.md` or the PR description
- [x] T011 [US1] Update `TESTING_DOCUMENTATION.md` with the new **CI layout** (parallel schema jobs, caching), and add optional `Makefile` target `test-schemathesis-parallel` that runs the three gateway/agent/data-management Schemathesis targets **concurrently** (e.g. `make -j3 ...`) **if** safe on developer machines; otherwise document “CI parallel / local sequential” explicitly

**Checkpoint**: **US1** measurable CI improvement documented vs baseline; **`make ci`** green.

---

## Phase 4: User Story 2 — Faster Render build phase (Priority: P2)

**Goal**: Shorter **build phase** for code-only deploys to Render services using `backend/Dockerfile`, same runtime correctness (**FR-003**, **SC-002**).

**Independent Test**: Median Render **build** duration for a **code-only** change improves **≥ 20%** vs baseline (or meets an agreed absolute cap documented in the baseline artifact); image still passes existing health checks.

### Implementation for User Story 2

- [x] T012 [US2] Reorder **COPY** / dependency install steps in `backend/Dockerfile` per [contracts/render-docker-build-layers.md](./contracts/render-docker-build-layers.md) so dependency layers cache independently of app source changes
- [x] T013 [US2] Add `backend/.dockerignore` excluding at minimum `tests/`, `**/__pycache__/`, `.pytest_cache/`, `htmlcov/`, `*.md`, and `.git` from the Render build context unless a documented build step requires them (prefer same PR as **T012** or immediately after, so Docker context stays coherent)
- [x] T014 [US2] Review `render.yaml` and `apps/data-management-frontend/render.yaml` for `dockerContext` / `dockerfilePath`; shrink **context** only if compatible with each service’s Dockerfile (**no** silent switch of Dockerfile for a service without validation)
- [x] T015 [US2] Append **post-change** warm and cold Render build timings to `specs/016-faster-render-ci-builds/artifacts/baseline-pre-optimization.md` (or new `baseline-post-optimization.md`) with same structure as **T005**, labeled **after-US2**

**Checkpoint**: **US2** independently verifiable on Render metrics.

---

## Phase 5: User Story 3 — Visible improvement and guardrails (Priority: P3)

**Goal**: Stakeholders can see improvement and that required checks were not removed to fake speed (**SC-003**, **SC-004**, spec User Story 3).

**Independent Test**: Short report artifact exists with medians + **required-check inventory** before/after; optional retro template for engineer sentiment.

### Implementation for User Story 3

- [x] T016 [US3] Create `specs/016-faster-render-ci-builds/artifacts/before-after-summary.md` linking baseline numbers (**T004**–**T005**) to post-optimization numbers (**T015** + CI job medians) and stating **≥ 20%** improvement claims per **change_category**
- [x] T017 [US3] Expand `specs/016-faster-render-ci-builds/artifacts/required-checks-inventory.md` (stub from **T004**) into the full inventory: every **required** GitHub check name at baseline and post-change, with **no removals** without an **FR-004** **EquivalenceRecord** row in that file
- [x] T018 [US3] Add `specs/016-faster-render-ci-builds/artifacts/engineer-retro-template.md` (three anonymized prompt lines) to support **SC-004** survey collection; assign an owner and due date in **before-after-summary.md** or team channel so **≥3** responses are collected (process requirement for **SC-004**)
- [x] T023 [US3] Add `specs/016-faster-render-ci-builds/artifacts/post-optimization-snapshot.md` recording medians for **FR-008 monitored dimensions** (see [spec.md](./spec.md) Definitions) after **US1**/**US2** ship; include **M3–M5** only if engineering leads named them in the governance artifact (otherwise note “none”); add `specs/016-faster-render-ci-builds/artifacts/fr008-regression-playbook.md` stating how re-baseline / revert / new-target decisions are recorded within **fourteen calendar days** per **FR-008**, and optionally record a **numeric flakiness tolerance** (e.g. max week-over-week retry delta) if leads adopt one—otherwise reference qualitative “lead tolerance” from the spec Edge Cases

**Checkpoint**: **US3** evidence pack complete for release review.

---

## Phase 6: Polish & cross-cutting concerns

**Purpose**: Docs parity, final gate, registry hygiene.

- [x] T019 [P] Update `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` **only** if **T012**–**T014** introduce new build-args or env vars consumed at Docker build time
- [x] T020 Run `make ci` from repository root after all merged changes and record elapsed time in the PR or `specs/016-faster-render-ci-builds/artifacts/before-after-summary.md`
- [x] T021 [P] If any new **contract** or **Pact** test file path is added under `**/tests/contracts/**`, `**/tests/pact/**`, or `**/*.pact.test.ts`, add a row to `.cursor/hooks/registry-contract-pact-tests.json`; **otherwise** skip with a one-line note in the PR

---

## Dependencies & execution order

### Phase dependencies

| Phase | Depends on | Notes |
|-------|------------|--------|
| Phase 1 | — | Start immediately |
| Phase 2 | Phase 1 | Baseline tables and paths must be coherent |
| Phase 3 (US1) | Phase 2 | Compare against **FR-001** artifact |
| Phase 4 (US2) | Phase 2 | Can run **in parallel with US1** after Phase 2 if staffed |
| Phase 5 (US3) | Phases 3–4 (for final numbers) | **T023** after US1/US2 medians exist; templates can start after Phase 2 |
| Phase 6 | US1–US3 scope done | Final polish |

### User story dependencies

- **US1**: No dependency on US2/US3 after Phase 2.
- **US2**: No dependency on US1/US3 after Phase 2 (Docker/Render path is separate).
- **US3**: Needs **post** metrics from US1/US2 for summary; inventory can start at baseline anytime after **T004**.

### Parallel opportunities

- **T002** ∥ **T003** (different contract files)
- **T007** ∥ **T006** (different workflow files) — both US1
- **US2**: **T014** (render YAML review) can start in parallel with **T012** by a second contributor; **T013** follows **T012** in the same PR when practical; **T015** after **T012**–**T014** land
- **T019** ∥ **T021** in polish phase

### Parallel example: User Story 1

```bash
# After Phase 2, two developers:
# Dev A: T006 (.github/workflows/test.yml)
# Dev B: T007 (.github/workflows/quality-gate.yml)
# Then sequence T008 → T009 → T022 (same workflow file / same PR when practical), then T010 → T011
```

### Parallel example: User Story 2

```bash
# After Phase 2:
# Dev A: T012 + T013 (backend/Dockerfile + backend/.dockerignore) in one PR when practical
# Dev B: T014 render.yaml + apps/data-management-frontend/render.yaml review (parallel)
# Then T015 metrics
```

---

## Implementation strategy

### MVP first (User Story 1 only)

1. Complete Phase 1 → Phase 2 (**baseline** locked).  
2. Complete Phase 3 (**US1**): caching + parallel `backend-schema` + docs.  
3. **Stop**: Re-measure CI medians vs `baseline-pre-optimization.md`; confirm **`make ci`**.

### Incremental delivery

1. **US1** merged → CI wins.  
2. **US2** merged → Render build wins.  
3. **US3** → evidence pack for stakeholders.

### Suggested MVP scope

**Phase 1 + Phase 2 + Phase 3 (through T009–T011 as needed, including T022 with schema split)** — largest contributor wait is often **integration + schema** wall-clock; **US2** next for deploy latency.

---

## Task summary

| Metric | Value |
|--------|--------|
| **Total tasks** | 23 |
| **Phase 1** | 3 |
| **Phase 2** | 2 |
| **US1** | 8 |
| **US2** | 4 |
| **US3** | 5 |
| **Polish** | 3 |
| **[P] parallel hints** | T002, T003, T007, T019, T021 (conditional) |

**Format validation**: Every task uses `- [ ] Tnnn …` with a **file path**; **[USn]** only on Phases 3–5.

---

## Notes

- Do **not** lower **TraceCov** thresholds or skip Schemathesis files to gain speed without **FR-004** documentation in `required-checks-inventory.md`.  
- Segment metrics by **change_category** when claiming **20%** improvement (**spec** edge cases: cold cache, lockfile churn).  
- Commit after each logical task group; **`make ci`** before merge-ready per constitution.

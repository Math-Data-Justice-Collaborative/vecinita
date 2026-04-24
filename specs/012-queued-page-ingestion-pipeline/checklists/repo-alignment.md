# Repo & documentation alignment checklist: Queued page ingestion pipeline

**Purpose**: Unit-test the **quality and consistency** of **plan, spec, tasks, contracts, and data-model** against the **current monorepo layout** and “all documents in place” expectations—not implementation behavior.  
**Created**: 2026-04-24  
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [tasks.md](../tasks.md)

## Artifact completeness

- [x] CHK001 Are every path listed under **Plan §Documentation (this feature)** present on disk (`plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/*`, `tasks.md`)? [Completeness, Plan §Documentation]
- [x] CHK002 Does `.specify/feature.json` at repo root still point at **`specs/012-queued-page-ingestion-pipeline`** while work tracks branch **`014-queued-page-ingestion-pipeline`**, and is that dual identifier explained where newcomers land (e.g. spec header or `checklists/requirements.md` Notes)? [Consistency, Clarity, Spec header]
- [x] CHK003 Are **Phase 0 / Phase 1** outputs the plan promises (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) **cross-linked** from `plan.md` so a reader never hits a dead “see below” reference? [Completeness, Plan §Phase 0–1]

## Plan ↔ repository paths

- [x] CHK004 Does every **primary touchpoint** under **Plan §Source code** resolve to an existing path today (`backend/src/api/router_modal_jobs.py`, `router_scraper_pipeline_ingest.py`, `main.py`, `backend/src/services/modal/invoker.py`, `modal_scraper_pipeline_persist.py`, `services/scraper/.../gateway_http.py`, `render.yaml`, `docs/deployment/*.md`)? [Completeness, Plan §Source code]
- [x] CHK005 Are **new** modules introduced only in **`tasks.md`** (e.g. **`pipeline_stage.py`**, **`chunking_defaults.py`**, new test files) either reflected in **`plan.md`** “Source code” tree or explicitly called out as *net-new in implementation* so the plan is not read as exhaustive? [Gap, tasks T007, T037, Plan §Source code]
- [x] CHK006 Does the plan’s reference to **`TESTING_DOCUMENTATION.md`** at repo root remain accurate (file exists, name unchanged)? [Consistency, Plan §Technical Context]

## Plan ↔ tasks consistency

- [x] CHK007 Do **task phases** (Setup → Foundational → US1–US3 → Polish) map cleanly to **plan** phases without orphan phases (e.g. plan “Phase 2” wording vs tasks “Phase 6” polish)? [Consistency, Plan tail, tasks.md headers]
- [x] CHK008 Are **T001–T003** documentation tasks explicit about **which sections** of `MODAL_DEPLOYMENT.md` / `RENDER_SHARED_ENV_CONTRACT.md` receive “See also” links so reviewers can verify completeness? [Clarity, tasks Phase 1]
- [x] CHK009 Does **tasks** language on **TDD / RED ordering** (Phase 2 parallel block) remain **internally consistent** with **T005**’s dependency on **T007** and **T035**’s optional RED-through-**T015** story? [Consistency, tasks §Parallel opportunities, tasks T005, T035]
- [x] CHK010 Is the **SC-001** staging note in **US1 checkpoint** clear that the **spec metric** (≥20 pages) may be satisfied by **documented manual/tag staging** rather than implying a missing CI task? [Clarity, Spec §SC-001, tasks US1 checkpoint]

## Spec ↔ contracts ↔ data-model

- [x] CHK011 Do **spec clarifications (FR-011–FR-015)** align with **`contracts/gateway-ingestion-http-surface.md`** without conflicting terms (e.g. correlation id location, error envelope fields)? [Consistency, Spec §FR-011–FR-015, contracts gateway-ingestion]
- [x] CHK012 Does **`contracts/render-modal-pipeline-wiring.md` § Pipeline stage persistence** state the same **v1 structured-row-first** rule as **tasks T008**, with the same **escape hatch** (DDL only via **T018** + contract update)? [Consistency, contracts render-modal, tasks T008, T018]
- [x] CHK013 Are **queue fairness**, **chunking parameters**, and **dedup** sections in **`data-model.md`** free of internal contradiction (FIFO default vs future per-tenant note; dedup vs force-reprocess future flag)? [Consistency, data-model §Queue fairness, §Chunking, §Dedup]
- [x] CHK014 Does **`data-model.md` § Chunking parameters** give enough **numeric and behavioral** guidance that **FR-004** can be judged complete without reopening the spec? [Measurability, data-model §Chunking, Spec §FR-004]

## Scope & consumer boundaries

- [x] CHK015 Are **main `frontend/`** vs **`apps/data-management-frontend/`** responsibilities spelled clearly enough in **plan + tasks** that **FR-012** (single gateway base for FR-011 consumers) is not confused with **DM API** Pact scope from **`TESTING_DOCUMENTATION.md`**? [Completeness, Spec §FR-012, Plan §Structure Decision, tasks T019, T040]
- [x] CHK016 Is **spec Assumption** “pipeline after discovery” still **explicitly bounded** relative to **plan** touchpoints (no accidental scope creep into crawl frontier) in **tasks** wording? [Consistency, Spec §Assumptions, Plan Summary]

## Non-functional & dependencies (requirements on docs)

- [x] CHK017 Are **Render** operational expectations in the plan (**`render.yaml`**, `checksPass`, health checks) stated as **requirements on documentation accuracy** (i.e. plan must not claim flags the blueprint does not use)? [Clarity, Plan §Technical Context, `render.yaml`]
- [x] CHK018 Are **Modal** “best practices” in the plan tied to **research decisions** so the plan does not read as generic marketing copy without traceable decisions? [Traceability, Plan Summary, research.md Decisions 1–2]
- [x] CHK019 Does **`quickstart.md`** enumerate the **same** primary commands as **`plan.md` Technical Context** (`make ci`, Pact, Schemathesis paths) without introducing a divergent workflow name? [Consistency, quickstart.md, Plan §Technical Context]

## Ambiguities to resolve in docs (before implement)

- [x] CHK020 If any **plan path** or **task file path** fails CHK004/CHK005, is there a **single owner decision** recorded (update plan vs update repo vs defer task) so the artifact set stays authoritative? [Gap, Process]

## Notes

- Check items off as `[x]` when the **requirement-writing** issue is resolved (paths verified, doc drift fixed, or explicit deferral recorded).
- This checklist does **not** replace `make ci` or code review—it validates that **written plans** are ready to drive implementation without silent mismatch.

## Resolution log (2026-04-24)

- **CHK001–CHK003, CHK006–CHK010, CHK015–CHK019, CHK020:** Updated **`spec.md`** (directory vs branch), **`plan.md`** (tasks link, phase mapping, `TESTING_DOCUMENTATION.md`, `vecinita-gateway` blueprint spot-check, consumer split, net-new modules, drift ownership, next-step), **`tasks.md`** (T001/T002 anchors, scope note), **`quickstart.md`** (parity with plan + matrix pointer), **`contracts/gateway-ingestion-http-surface.md`** (spec lockstep sentence), **`data-model.md`** (dedup vs future `force_reprocess` clarified for v1). Primary repo paths for CHK004 verified against workspace (`router_*`, `invoker.py`, `modal_scraper_pipeline_persist.py`, `gateway_http.py`, `render.yaml`, deployment docs).  
- **CHK011–CHK014:** Addressed via contract + data-model edits above; FIFO vs per-tenant remains explicitly “default vs future.”

# Plan Cohesion Checklist: Strict Canonical Monorepo Layout

**Purpose**: Unit-test the **written requirements and planning artifacts** for internal consistency, traceability, and gap coverage (not implementation behavior).  
**Created**: 2026-04-29  
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [tasks.md](../tasks.md)

**Scope defaults** (no interactive session): cohesion across **spec ↔ plan ↔ tasks ↔ path-mapping ↔ contracts/research**; **standard** rigor; intended for **PR / planning review** before large moves merge.

---

## Cross-artifact traceability

- [x] CHK001 Are **FR-001–FR-003** (top-level `apis/`, `modal-apps/`, `frontends/`) explicitly reflected in the **plan** target tree and **tasks** phases without naming drift (same deployable names)? [Consistency, Spec §FR-001–FR-003, Plan §Project Structure, Tasks §Phase 4]
- [x] CHK002 Is **FR-013** (single path map; plan and tasks trace moves) supported by an explicit requirement that **`plan.md` contains a durable link** to `artifacts/path-mapping.md`, matching **SC-006** language? [Completeness, Spec §FR-013, Spec §SC-006, Gap]
- [x] CHK003 Does **tasks.md** commit to updating **`artifacts/path-mapping.md` `status`** in the same change sets as moves, so **spec edge case** (“plan/tasks vs map drift”) is operable rather than aspirational? [Clarity, Spec §Edge Cases, Tasks §Format]
- [x] CHK004 Are **FR-005** (`clients/apis/<api>` mirrors `apis/`) and **Phase 6 / T020** aligned on **which API names** must exist before client relocation (ordering vs **US2** completion)? [Consistency, Spec §FR-005, Tasks §Phases 4–6, Ambiguity]
- [x] CHK005 Is **FR-010** (`scripts/` for non-deployable automation) mapped to a **tasks.md** deliverable that names **which classes** of scripts move (vs remain next to a service), avoiding overlap with **US5** ambiguity? [Completeness, Spec §FR-010, Tasks §Phase 7–8, Gap]

---

## Ordering & dependency coherence

- [x] CHK006 Does the **plan** “phased moves” narrative (**modal/frontends before `backend/` split**) align with **tasks.md** dependency guidance, or are contradictions (e.g., parallel submodule vs scraper) explicitly resolved in prose? [Consistency, Plan §Structure Decision, Tasks §Dependencies, research.md §1]
- [x] CHK007 Is the **high-risk `backend/` split** decomposed so requirements readers see **T015 → T016** as the mandatory gate **before** claiming PM-007/PM-008 complete, matching **plan Summary**? [Traceability, Plan §Summary, Tasks §Phase 4, Spec §FR-001]
- [x] CHK008 Are **optional subtrees** from the spec (e.g., `packages/python/modal-shared`) either **excluded with rationale** in plan/tasks or **given acceptance criteria** so “optional” does not read as “unspecified”? [Clarity, Spec §Assumptions, Plan §Target tree, Gap]

---

## Success criteria vs plan/tasks coverage

- [x] CHK009 Is **SC-001** (“one-page tree overview”) explicitly owned by **named artifacts** (`docs/monorepo-layout.md`, **T003**) and linked from **README** (**T002**), so the success criterion is traceable to tasks? [Traceability, Spec §SC-001, Tasks §Phase 1–3]
- [x] CHK010 Does **SC-002** (single owning path per deployable in release documentation) name **which doc** is “release documentation,” or is that term left undefined relative to `README` / `docs/`? [Clarity, Spec §SC-002, Gap]
- [x] CHK011 Is **SC-006** (path map exists; plan links; five task rows trace to map) reflected in **plan.md** body text (not only in spec), so reviewers can gate **plan** completeness independently of **spec**? [Completeness, Spec §SC-006, Plan §Note, Gap]
- [x] CHK012 Are **SC-003** (post-cutover incident taxonomy) and **SC-005** (`make ci`) acknowledged in **plan/tasks** as **non-functional guardrails** without turning into implementation test steps here? [Consistency, Spec §SC-003–SC-005, Plan §Technical Context]

---

## Edge cases, recovery, and migration policy

- [x] CHK013 Is **FR-011** (time-bounded legacy inventory) tied to **`artifacts/path-mapping.md` fields** (`cutover_date`, `owner`) in **data-model.md** and carried into **tasks** (e.g., **T025**), or is the linkage implicit only? [Traceability, Spec §FR-011, data-model.md, Tasks §Phase 8]
- [x] CHK014 Are **recovery / rollback** expectations for failed mid-migration PRs documented as **requirements** (what “rollback” means for path map rows and deployables), or intentionally **out of scope** with a single explicit sentence? [Coverage, Exception/Recovery, Gap]
- [x] CHK015 Does **spec** + **contracts/monorepo-layout-boundary.md** agree on **whether contract snapshots may live under `specs/**/contracts/`** vs only top-level `contracts/`, without conflicting “canonical home” language? [Consistency, Spec §User Story 5, contracts §Rule 5, Ambiguity]

---

## Research & production wiring

- [x] CHK016 Is the **Render DM API image builds from scraper** finding in **research.md** §4 mirrored in **path-mapping PM-003 notes** and **plan Constitution table**, so three artifacts do not diverge on facts? [Consistency, research.md §4, Plan §Constitution, path-mapping.md]
- [x] CHK017 Are **assumptions** in **spec** (naming collisions, phased migration) duplicated or **referenced** in **plan.md** so implementers do not rely on spec alone for rename policy? [Completeness, Spec §Assumptions, Plan, Gap]

---

## User stories vs task phases

- [x] CHK018 Does each **P1 user story** in **spec** map to a **distinct tasks phase** with matching **Independent Test** language, or are **US1** and **US2** partially overlapping in a way that blurs accountability? [Clarity, Spec §User Stories, Tasks §Phases 3–4]
- [x] CHK019 Are **US3–US5** (P2/P3) explicitly **blocked by** completion of **US2** in **tasks** dependencies, matching the spec’s dependency intuition for physical paths? [Consistency, Spec §User Stories 3–5, Tasks §Dependencies]

---

## Ambiguities & conflicts to resolve in prose

- [x] CHK020 Is the term **“trivial path depth”** in **SC-006** defined or exemplified in **plan** or **quickstart**, so “before any PR…” is reviewable? [Clarity, Spec §SC-006, quickstart.md, Ambiguity]
- [x] CHK021 If **`packages/openapi-clients/`** remains temporarily during migration, is **intermediate dual location** forbidden or allowed under **FR-011** inventory rules? [Conflict, Spec §FR-005 vs FR-011, Tasks §Phase 6, Ambiguity]
- [x] CHK022 Does **constitution “service boundaries”** language in **plan** align with **boundary contract** rule #2 (no duplicated modules) when **T016** might temporarily duplicate until convergence—**or** is a temporary exception documented? [Consistency, Plan §Constitution, contracts §Rules, Tasks §Phase 4, Gap]

---

## Notes

- Check items when the **artifact text** is updated to satisfy the question; this checklist does not replace `make ci` or code review.
- **Clarification defaults used**: cohesion focus; standard depth; PR/planning reviewer audience.
- **2026-04-29**: All items addressed by updates to `spec.md`, `plan.md`, `tasks.md`, `quickstart.md`, `data-model.md`, `contracts/monorepo-layout-boundary.md`, and `artifacts/path-mapping.md`.
- **2026-04-29 (post-analyze)**: `tasks.md` task IDs **T019–T026** adjusted for FR-012, env/deploy docs (**T025**), SC-001 artifact (**T026**); `spec` / `plan` / `quickstart` aligned with `/speckit-analyze` recommendations C1, A1, C2, U1, I1, T1, C3.
- **2026-04-29 (post-analyze 2)**: Phase 8 order **T024→T025→T026** (docs/cleanup/gate); **T024** adds **README** + **Makefile** skim (**SC-002**, **FR-006**); **FR-011** text points to **T025**; **T019** after **T018**; plan **Constraints** wording; quickstart defers trivial-path norm to **spec SC-006**.
- **2026-04-29 (post-analyze 3)**: **PM-012** = **`specs/`** identity (**FR-006**); **T001**/**T023** renumbered to **PM-013+**; **T024** clarifies **`clients/apis/*`** post-**T020** vs interim **`packages/openapi-clients/`**; **Phase 7** + **T021** timing for legacy path references; **plan** **SC-003** ops follow-up; **quickstart** aligns with **PM-009** transition.

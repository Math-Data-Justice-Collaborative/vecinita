---
description: "Task list for faster Render-aligned Docker packaging (Data Management API V1)"
---

# Tasks: Faster Docker packaging for Data Management API V1 (Render-aligned)

**Input**: Design documents from `/specs/002-dm-api-docker-build/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/render-docker-build.md](./contracts/render-docker-build.md), [quickstart.md](./quickstart.md)

**Tests**: Spec does not mandate TDD; validate with existing `services/scraper` CI jobs plus optional
new Docker build job (**FR-004**) and `make ci` before merge.

**Organization**: Phases follow user-story priority (US1 → US2 → US3), then polish. Constitution:
service boundaries, quality gates, no runtime contract drift per `.specify/memory/constitution.md`.

**Remediation (post-analyze)**: **T004** captures **automation** pre-baseline separately from **T003**
(local `docker build`). **T010** compares post-change automation to that row (**fixes I1**).
`baseline-notes.md` defines **variance band** and **FR-007** inventory (**U1**, **U2**).

## Format

`- [X] Tnnn [P?] [USn?] Description with file path`

---

## Phase 1: Setup (shared artifacts)

**Purpose**: Baseline tables and blueprint alignment before changing the image.

- [X] T001 Create or complete `specs/002-dm-api-docker-build/baseline-notes.md` using the template
  already in that file (profiles, **variance band**, **FR-007** inventory, local + automation tables,
  reviewer checklist) per `specs/002-dm-api-docker-build/data-model.md`
- [X] T002 [P] Record in `specs/002-dm-api-docker-build/baseline-notes.md` that root `render.yaml`
  service `vecinita-data-management-api-v1` uses `dockerfilePath: ./services/scraper/Dockerfile` and
  `dockerContext: ./services/scraper`, matching
  `specs/002-dm-api-docker-build/contracts/render-docker-build.md` (or note drift if not)

---

## Phase 2: Foundational (blocking)

**Purpose**: Pre-change timings (local **and** automation), security posture review, before Dockerfile
optimizations.

**⚠️ CRITICAL**: Complete before claiming percentage improvements in US1/US2.

- [X] T003 Run pre-change **local** `docker build` timings from repository root per
  `specs/002-dm-api-docker-build/quickstart.md` (repeat-edit warm cache + cold `--no-cache`); write
  medians, sample counts, dates, and **local** machine profile into
  `specs/002-dm-api-docker-build/baseline-notes.md` (**FR-002**)
- [X] T004 Record pre-change **automation** packaging medians (≥3 successful runs) in
  `specs/002-dm-api-docker-build/baseline-notes.md` **Automation timings** table using the **same**
  workflow + runner profile as **T009** (declare profile ID, e.g. `gha-ubuntu-latest-docker-build`).
  **Order rule (fixes I1):** If the workflow from T009 does not exist yet, land **T009** on default
  branch first (Dockerfile unchanged), collect ≥3 pre runs, **then** merge T006–T008; if that split
  is impossible, document FR-004 deferral with owner in `baseline-notes.md`.
- [X] T005 Audit `services/scraper/Dockerfile` against
  `specs/002-dm-api-docker-build/contracts/render-docker-build.md` (no secret `ARG`s, `CMD`/port
  unchanged); complete the **FR-007 inventory** table in `specs/002-dm-api-docker-build/baseline-notes.md`
  (mark N/A with owner where no tool exists today)

**Checkpoint**: Local + automation pre-baselines, Render contract audit, FR-007 inventory captured.

---

## Phase 3: User Story 1 — Shorter turnaround on typical code edits (Priority: P1) 🎯 MVP

**Goal**: Warm-cache packaging completes ≥25% faster than **T003** local baseline when only `src/`
changes (**FR-003**).

**Independent Test**: Two consecutive repeat-edit builds on the same measurement profile stay within
the **variance band** defined in `baseline-notes.md` and beat the **T003** pre-change median by ≥25%.

### Implementation

- [X] T006 [P] [US1] Add `services/scraper/.dockerignore` excluding `.venv/`, `**/__pycache__/`,
  `.pytest_cache/`, `.mypy_cache/`, `.hypothesis/`, `tests/`, and other dev-only paths per
  `specs/002-dm-api-docker-build/research.md` (verify `pip install .` still succeeds in image)
- [X] T007 [US1] Refactor `services/scraper/Dockerfile` for better layer reuse (install deps before
  final `src` copy; pin `FROM` to an immutable digest or specific patch tag per research) without
  changing runtime `CMD`, `EXPOSE`, or Python 3.11 line (**FR-005**, **FR-006**)
- [X] T008 [US1] Re-run repeat-edit `docker build` per `specs/002-dm-api-docker-build/quickstart.md`;
  append post-change medians to `specs/002-dm-api-docker-build/baseline-notes.md` and confirm ≥25%
  improvement vs **T003** (not T004) or iterate T006/T007

**Checkpoint**: US1 timing target documented with evidence.

---

## Phase 4: User Story 2 — Faster packaging in automation (Priority: P2)

**Goal**: CI shows ≥20% median improvement for source-only builds vs **T004** automation pre-baseline
without dropping required checks (**FR-004**).

**Independent Test**: ≥3 automation runs on distinct days or SHAs with logged wall-clock for
`docker build -f services/scraper/Dockerfile services/scraper` after submodule checkout.

### Implementation

- [X] T009 [US2] Add a GitHub Actions workflow file under `.github/workflows/` (dedicated file
  recommended) that checks out `services/scraper` submodule and runs
  `docker build -f services/scraper/Dockerfile -t vecinita-scraper:ci services/scraper` with elapsed
  time printed (use `ubuntu-latest` and document cache policy in `baseline-notes.md`)
- [X] T010 [US2] Populate **post-change** automation median rows in
  `specs/002-dm-api-docker-build/baseline-notes.md`; confirm ≥20% improvement vs the **pre-change
  automation** row filled in **T004** (same profile ID). If **T004** was deferred, keep the documented
  deferral path instead of comparing to **T003** (local)

**Checkpoint**: Automation evidence exists or explicit deferral with rationale.

---

## Phase 5: User Story 3 — Cold and onboarding builds stay understandable (Priority: P3)

**Goal**: Contributors can follow docs; cold-run numbers live next to repeat-edit baselines.

**Independent Test**: A new contributor can run `quickstart.md` cold path once and find expected
duration documented in `baseline-notes.md`.

- [X] T011 [P] [US3] Extend `services/scraper/README.md` with a “Docker / Render” subsection linking
  to `specs/002-dm-api-docker-build/quickstart.md` and stating cold vs warm expectations
- [X] T012 [US3] Ensure `specs/002-dm-api-docker-build/baseline-notes.md` includes a completed cold-
  run row (post-change acceptable) with the same transparency rules as repeat-edit (**FR-002**,
  **FR-008**)

**Checkpoint**: Onboarding and cold numbers published.

---

## Phase 6: Polish & cross-cutting

- [X] T013 Run `make ci` from repository root after Dockerfile or workflow changes; fix any
  regressions
- [X] T014 [P] Re-verify root `render.yaml` `vecinita-data-management-api-v1` `dockerfilePath` /
  `dockerContext` still match `specs/002-dm-api-docker-build/contracts/render-docker-build.md` after
  all edits
- [X] T015 [P] Complete the **Reviewer checklist** section in
  `specs/002-dm-api-docker-build/baseline-notes.md` (equivalence: existing scraper tests + optional
  `docker run` health smoke) per **FR-006** / **FR-008**

---

## Dependencies (story order)

```text
Phase 1 → Phase 2 → US1 (P1) → US2 (P2) → US3 (P3) → Polish
```

**I1 mitigation**: **T004** (automation pre-baseline) depends on **T009**’s workflow definition **or**
T009 merged first on default branch; see **T004** order rule.

## Parallel execution examples

- **Phase 1**: T001 and T002 in parallel (different sections of `baseline-notes.md`—resolve in one
  commit if needed).
- **US1**: T006 (`.dockerignore`) before T007; T008 strictly after T007.
- **US3**: T011 (`README.md`) and T012 (`baseline-notes.md` cold row) in parallel once US1 numbers
  exist.
- **Polish**: T014 and T015 in parallel (read-only verify + checklist).

## Implementation strategy

1. **MVP**: Phases 1–3 (through **T008**) — local repeat-edit speedup with evidence.  
2. **Increment 2**: **US2** CI timing job + **FR-004** proof (**T009–T010**), respecting **T004** order.  
3. **Increment 3**: **US3** contributor docs + cold transparency.  
4. **Close**: `make ci` + contract cross-check + reviewer checklist.

**Suggested MVP scope**: **T001–T008** (Phases 1–3).

---

## Task summary

| Phase | Task IDs | Count |
|-------|----------|------:|
| Setup | T001–T002 | 2 |
| Foundational | T003–T005 | 3 |
| US1 (P1) | T006–T008 | 3 |
| US2 (P2) | T009–T010 | 2 |
| US3 (P3) | T011–T012 | 2 |
| Polish | T013–T015 | 3 |
| **Total** | **T001–T015** | **15** |

**Parallel opportunities**: T001∥T002; T011∥T012 (late phase); T014∥T015.

**Independent test reminders**: US1 = local warm builds vs **T003**; US2 = CI `docker build` vs **T004**;
US3 = README + cold row in `baseline-notes.md`.

---

## Notes

- Do not change `render.yaml` Docker paths without updating
  `specs/002-dm-api-docker-build/contracts/render-docker-build.md` in the same change.
- Never add `ARG` for secrets; prefer runtime env on Render per contract.
- Submodule: ensure CI jobs run `git submodule update --init services/scraper` before `docker build`.

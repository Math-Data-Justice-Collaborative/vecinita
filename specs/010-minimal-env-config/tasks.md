# Tasks: Minimal environment configuration

**Input**: Design documents from `/specs/010-minimal-env-config/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/configuration-resolution.md](./contracts/configuration-resolution.md), [quickstart.md](./quickstart.md)

**Tests**: Small **template hygiene** tasks are included for SC-003 / contract C7 (not full story TDD).

**Organization**: Phases follow user story priority (US1 → US2 → US3) after shared setup and foundation.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Parallelizable (different files, no ordering dependency within the same checkpoint)
- **[USn]**: User story label from `spec.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Migration doc shell + inventory so SC-002 baseline work is traceable.

- [X] T001 Create `docs/environment-migration.md` with sections: overview, baseline methodology (deduplicated union per clarify), placeholder mapping table, alias timeline, SC-002 before/after count placeholders, and link target anchors per FR-010
- [X] T002 [P] Append to `docs/environment-migration.md` an inventory appendix listing every tracked `*.env.example` and `.env*.example` path under the repository root (absolute paths in prose optional; repo-relative required); add an optional subsection listing **Python entrypoints** that call `os.getenv` / `load_dotenv` outside **`shared_config`** and **`backend/src/config.py`** for a follow-up **FR-008** audit if MVP scope excludes wiring them in this feature

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Single root catalog structure, non-secret defaults artifact, and shared deprecation hook pattern before story-specific trimming.

**⚠️ CRITICAL**: Complete this phase before executing US1–US3 implementation tasks.

- [X] T003 Reconcile root templates per `specs/010-minimal-env-config/research.md`: make `/.env.example` the authoritative full catalog; update `/.env.local.example` to a **minimal** pointer (link + copy instructions to `.env.example`) within the **first 40 lines**, including the exact C4b substring `Canonical environment catalog: repo root .env.example`, per FR-001 and contracts C4 / C4b
- [X] T004 Add explicit comment banners in `/.env.example` for `### REQUIRED — default local` and each `### OPTIONAL PROFILE: <id>` block per FR-002 and FR-007 (**run immediately after T003** — same file; not parallel with T003)
- [X] T005 [P] Add `config/defaults.example.yaml` at repository root containing **non-secret** defaults only (timeouts, flags, public example URLs) with comments; **no** API keys or database passwords per `contracts/configuration-resolution.md` C1
- [X] T006 Document in `docs/environment-migration.md` how **env overrides file** for Python services (order: committed example YAML → local untracked YAML if used → environment variables win) per plan Summary
- [X] T007 Add `services/data-management-api/packages/shared-config/shared_config/env_deprecation.py` that loads alias pairs from `config/env_aliases.example.yaml` (repo-root path resolution) and detects matching keys in `os.environ`, emitting `warnings.warn` with **canonical** names only (no values); integrate from `services/data-management-api/packages/shared-config/shared_config/__init__.py` in the cached settings accessor path per FR-008. For **each** supported alias row, ensure the corresponding **`BaseSettings` field** uses **`AliasChoices` / `validation_alias`** (or equivalent) so legacy keys **still resolve** during the window per `contracts/configuration-resolution.md` C3—warnings alone are not enough.

**Checkpoint**: Root template story is unblocked; **`shared_config`** warns on legacy keys **and** keeps them **resolvable** via **`AliasChoices` / `validation_alias`** per **T007**, without leaking secrets.

---

## Phase 3: User Story 1 — Fast local setup with a short required list (Priority: P1) 🎯 MVP

**Goal**: Contributors use **one** root template + README path; **required** key set is materially smaller while FR-009 holds (Supabase + `DATABASE_URL` when guide promises both).

**Independent Test**: Follow updated `README.md` + `/.env.example` **required** section only; documented default local chat + data-management flows start.

- [X] T008 [US1] Reduce **required** rows in `/.env.example` by removing redundant non-secret keys superseded by `config/defaults.example.yaml` and by **derivation** (e.g. drop discrete `DB_*` when `DATABASE_URL` suffices) without breaking FR-009
- [X] T009 [US1] Extend `backend/src/config.py` to load optional non-secret defaults from `config/defaults.example.yaml` (or documented local `config/defaults.yaml`) and implement `DATABASE_URL` → discrete DB field helpers when individual `DB_*` env vars are unset per contract C2
- [X] T010 [P] [US1] Update `README.md` environment/setup section: copy from `/.env.example`, set **required** keys first, prominent link to `docs/environment-migration.md` per FR-006 and FR-010
- [X] T011 [US1] Update `backend/src/api/main.py` and `backend/src/agent/main.py` header comments for `load_dotenv` to state that `/.env.example` is the **canonical** catalog and `.env.local` / `.env` are local overrides
- [X] T012 [US1] Add `backend/src/env_deprecation.py` that loads legacy→canonical pairs from `config/env_aliases.example.yaml`, **copies legacy values into canonical env keys when the canonical key is unset** (names only in warnings), and warns (names only) when a legacy key is present; call from `backend/src/config.py` early in module import (after `load_dotenv`) so chat **gateway** and **agent** meet FR-008 **acceptance + notice** outside Pydantic per `specs/010-minimal-env-config/plan.md` “Deprecation mechanisms”; implementation MUST be **idempotent** (do not overwrite an already-set canonical value; safe if invoked more than once)
- [X] T013 [P] [US1] Reduce `backend/.env.example` to **minimal** service-local keys and include the exact substring `Canonical environment catalog: repo root .env.example` within the **first 40 lines** per FR-001 and contract C4b

**Checkpoint**: US1 independently verifiable per `specs/010-minimal-env-config/quickstart.md` sections 1–2 and 6.

---

## Phase 4: User Story 2 — Clear optional profiles (Priority: P2)

**Goal**: Optional integrations appear only under named profile banners; subsidiary templates stay minimal.

**Independent Test**: With profiles unset, default local path still works; enabling one profile follows a checklist in `docs/environment-migration.md`.

- [X] T014 [US2] Move remaining optional integration keys in `/.env.example` under the correct `### OPTIONAL PROFILE:` banners (Modal, LangSmith, Render deploy hooks, alternate LLM providers, etc.) per FR-007
- [X] T015 [P] [US2] Add a **profile index** table to `docs/environment-migration.md` (`id`, title, when to enable) aligned with `CapabilityProfile` in `specs/010-minimal-env-config/data-model.md`
- [X] T016 [P] [US2] Update every **committed subsidiary** `*.env.example` under the repo (currently `backend/.env.example`, `frontend/.env.example`, `apps/data-management-frontend/.env.example`, `services/scraper/.env.example`, `services/model-modal/.env.example`, `tests/.env.example`, `deploy/gcp/.env.example` — extend this list in `docs/environment-migration.md` if new examples appear) to **minimal** overrides plus the exact pointer substring `Canonical environment catalog: repo root .env.example` in the **first 40 lines** per contract C4 and C4b; **`/.env.local.example`** is updated under **T003** but must still satisfy C4b when it is pointer-only (**coordinate** with **T013** / **T020**–**T022** to avoid duplicate edits on the same file in one PR)

**Checkpoint**: US2 independently reviewable in template + migration doc structure.

---

## Phase 5: User Story 3 — Safer handoff and migration completeness (Priority: P3)

**Goal**: Migration documentation complete; subsidiary examples + automated hygiene; soft-deprecation observable.

**Independent Test**: `docs/environment-migration.md` contains full mapping + baseline math; pytest template test passes; deprecation warning fires for a chosen legacy alias.

- [X] T017 [US3] Fill the **mapping table** in `docs/environment-migration.md` (legacy → canonical → profile/retired) per FR-005 and FR-008, and **sync the same pairs** into `config/env_aliases.example.yaml` (`aliases` list, names only); verify **T007** `AliasChoices` / field wiring covers **every** supported YAML row (or document explicit bootstrap copy for backend-only keys)
- [X] T018 [US3] Record **deduplicated union** baseline counts and post-change **required** count in `docs/environment-migration.md` proving **≥ 50%** reduction for SC-002 per FR-004; include a **reproducible snapshot** of the “prior” guide state (e.g. **git commit SHA** plus paths, or an excerpt block) so reviewers can re-derive the baseline without guesswork
- [X] T019 [US3] Document **alias support end date** (calendar or release id) in `docs/environment-migration.md` per FR-008
- [X] T020 [P] [US3] Trim `frontend/.env.example` to minimal `VITE_*` lines plus the exact pointer substring `Canonical environment catalog: repo root .env.example` within the **first 40 lines** per FR-001, contract C6, and C4b
- [X] T021 [P] [US3] Trim `apps/data-management-frontend/.env.example` the same way as `frontend/.env.example` (include C4b substring in first 40 lines)
- [X] T022 [P] [US3] Update `tests/.env.example` and `deploy/gcp/.env.example` to include the exact pointer substring `Canonical environment catalog: repo root .env.example` in the **first 40 lines** where those files remain committed per contract C4b
- [X] T023 [US3] Add `backend/tests/unit/test_env_example_templates.py` enforcing: (a) no obvious secret material in tracked `*.env.example` paths; (b) every subsidiary `*.env.example` contains the exact substring `Canonical environment catalog: repo root .env.example` in the first 40 lines per contract C4b and C7; (c) assert the same substring for **`/.env.local.example`** when that file is present and used as a pointer template (contract C4b **Also** clause)

**Checkpoint**: US3 satisfies SC-003 / SC-004 evidence paths and acceptance scenario 4 in `spec.md`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, checklist sync, CI.

- [X] T024 [P] Execute manual steps in `specs/010-minimal-env-config/quickstart.md` (include optional **5-minute** README + root template walkthrough for SC-001) and patch docs or tests for any gap discovered
- [X] T025 [P] Update `specs/010-minimal-env-config/checklists/requirements.md` checkboxes/notes if spec–plan–tasks alignment changed during implementation
- [X] T026 Run `make ci` from the repository root and resolve failures before merge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** → no prerequisites  
- **Phase 2** → depends on Phase 1 (migration file exists for edits in later tasks)  
- **Phase 3 (US1)** → depends on Phase 2  
- **Phase 4 (US2)** → depends on Phase 3 for stable root `/.env.example` structure (can overlap minimally once T003–T004 exist—prefer strict: after Phase 2)  
- **Phase 5 (US3)** → depends on Phases 3–4 for accurate mapping and counts  
- **Phase 6** → depends on desired user stories being complete  

### User Story Dependencies

- **US1**: After Phase 2; no dependency on US2/US3  
- **US2**: After US1 root structure (T003–T004) recommended; independently testable by profile banners + doc index  
- **US3**: Uses outputs of US1/US2 for mapping and counts; independently testable via migration doc + `test_env_example_templates.py`  

### Parallel Opportunities

- **Phase 1**: T002 [P] after T001 file exists (can batch in one commit)  
- **Phase 2**: After **T003**, run **T004** (same file). **T005** [P] can run parallel to other work that does not touch `/.env.example`. **T006**–**T007** after `docs/environment-migration.md` exists; **`config/env_aliases.example.yaml`** is already committed—extend via **T017**.  
- **US1**: T010, T013 [P] after T008–T009 stabilize `/.env.example` and `backend/src/config.py`  
- **US2**: T015 [P]; **T016** coordinates with US1/US3 subsidiary edits—run after T013/T020–T022 or merge in one branch with clear file ownership to avoid conflicts  
- **US3**: T020–T022 [P]  
- **Polish**: T024, T025 [P]  

---

## Parallel Example: User Story 1

After T008–T009 land:

```bash
# Parallel documentation + subsidiary template:
Task T010 — README.md
Task T013 — backend/.env.example
```

---

## Parallel Example: User Story 3

```bash
# Parallel subsidiary templates:
Task T020 — frontend/.env.example
Task T021 — apps/data-management-frontend/.env.example
Task T022 — tests/.env.example and deploy/gcp/.env.example
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1–2  
2. Complete Phase 3 (US1)  
3. Run `quickstart.md` sections for US1 + `make ci` (early **T026** optional)  
4. Demo / internal review  

### Incremental Delivery

1. US1 → minimal **required** set + README + backend derivation/YAML merge  
2. US2 → profile clarity for maintainers  
3. US3 → migration completeness + automated template checks  
4. Polish → full `make ci`  

### Parallel Team Strategy

- Developer A: Phase 2 root + `shared_config` deprecation (`T003`–`T007`)  
- Developer B: Phase 1 docs + inventory (`T001`–`T002`)  
- After Phase 2: split US1 (`backend/src/config.py`, `README.md`) vs US2 (`/.env.example` profiles, services examples)  

---

## Task counts

| Scope | Tasks |
|-------|------|
| Phase 1 Setup | 2 |
| Phase 2 Foundational | 5 |
| Phase 3 US1 | 6 |
| Phase 4 US2 | 3 |
| Phase 5 US3 | 7 |
| Phase 6 Polish | 3 |
| **Total** | **26** |

### Format validation

All tasks use the checklist pattern `- [ ] Tnnn …` with a **Task ID**; user-story phases include **[USn]**; parallelizable tasks include **[P]**; descriptions include **concrete file paths** or repo-root commands.

---

## Notes

- **Vite** remains env-based for `VITE_*`; do not put secrets there (contract C6).  
- **LangSmith / provider rate limits** in CI are environmental; template tests must stay **offline** (no Hub calls).  
- If `config/defaults.yaml` is introduced for local overrides, add it to `.gitignore` in a dedicated task when implementing T005/T009 (same PR as those tasks).
- **Pointer substring** (contract C4b): `Canonical environment catalog: repo root .env.example` — use verbatim in subsidiary `*.env.example` files and in **T023** assertions.

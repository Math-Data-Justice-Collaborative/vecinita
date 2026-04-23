# Tasks: Active crawl CLI (BeautifulSoup + Playwright)

**Input**: Design documents from `/specs/008-make-cli-web-crawler/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Focused **pytest** tasks appear in the Polish phase (constitution-aligned); not test-first unless you extend the spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallel-safe (different files, no ordering dependency within the same checkpoint)
- **[USn]**: Maps to [spec.md](./spec.md) user stories

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package skeleton, seed artifact, and repo wiring surface.

- [X] T001 Create package skeleton including `backend/src/services/scraper/active_crawl/__init__.py`, `backend/src/services/scraper/active_crawl/config.py`, `backend/src/services/scraper/active_crawl/__main__.py` (stub argv), and **`backend/src/services/scraper/active_crawl/runner.py`** (empty `run_once_seeds` stub) per [plan.md](./plan.md)
- [X] T002 [P] Add `data/config/active_crawl_seeds.txt` listing spec FR-003 hostnames (one entry per line; `https://` URLs preferred; comment header for operators)
- [X] T003 [P] Add `data/config/active_crawl_allowlist.example.txt` documenting optional cross-domain allowlist format referenced in [spec.md](./spec.md) FR-004

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database contract + persistence + URL policy before any story can complete.

**⚠️ CRITICAL**: No user story work is considered done until migration and `persistence.py` exist.

- [X] T004 Add append-only schema migration `backend/scripts/migrations/003_active_crawl_tables.sql` implementing fields from [data-model.md](./data-model.md) and invariants from [contracts/crawl-persistence-schema.md](./contracts/crawl-persistence-schema.md)
- [X] T005 Implement `CrawlRepository` (or equivalent) with insert-only helpers for `crawl_runs` and `crawl_fetch_attempts` in `backend/src/services/scraper/active_crawl/persistence.py` using the same `DATABASE_URL` resolution patterns as `backend/src/services/scraper/uploader.py`
- [X] T006 Implement canonical URL normalization + same-registrable-domain scope check + allowlist parsing in `backend/src/services/scraper/active_crawl/url_policy.py`, including loading optional production file **`data/config/active_crawl_allowlist.txt`** (one hostname or registrable domain per line, `#` comments) when present—**not** only the example from T003
- [X] T007 Implement cap loading (max depth, pages total, pages per host, wall time, raw retention) from env + argparse defaults in `backend/src/services/scraper/active_crawl/config.py` per [research.md](./research.md)

**Checkpoint**: Apply `003_active_crawl_tables.sql` to a dev DB; import `persistence` in a Python shell and insert a dry-run row.

---

## Phase 3: User Story 1 — Run a crawl from the project root (Priority: P1) 🎯 MVP

**Goal**: Operator runs **`make active-crawl`** (or script); process uses **`DATABASE_URL`** from `.env`; creates **`crawl_runs`** row and persists per-seed fetch attempts.

**Independent Test**: From repo root with valid `.env`, run `make active-crawl` with tight caps; verify `crawl_runs` + `crawl_fetch_attempts` rows in Postgres.

- [X] T008 [US1] Implement CLI entrypoint: argparse, exit codes from [contracts/cli-active-crawl.md](./contracts/cli-active-crawl.md), `DATABASE_URL` validation, logging in `backend/src/services/scraper/active_crawl/__main__.py`
- [X] T009 [US1] Implement `run_once_seeds()` in `backend/src/services/scraper/active_crawl/runner.py` that reads seeds, creates `crawl_run`, and **fetches each seed URL at least once via `SmartLoader.load_url()`** (no parallel “thin httpx” MVP path—keeps FR-006 static-first / loader semantics). For each attempt, persist **FR-010 MVP fields**: `extracted_text` (primary text from returned documents), `content_sha256` or length, `retrieval_path` mapped from loader type, and `raw_omitted_reason` when `ACTIVE_CRAWL_NO_RAW` or policy skips raw snapshot (raw bytes optional in MVP if omitted is explicit)
- [X] T010 [US1] Add `scripts/run_active_crawl.sh` loading `.env` / `DATABASE_URL` like `scripts/run_scraper_postgres_batch.sh` and invoking `uv run python -m src.services.scraper.active_crawl` from `backend/`
- [X] T011 [US1] Add `active-crawl` target to root `Makefile` delegating to `scripts/run_active_crawl.sh` with passthrough `ARGS`

**Checkpoint**: MVP — one command, visible rows for each seed (even before BFS).

---

## Phase 4: User Story 2 — Discover and capture linked pages (Priority: P2)

**Goal**: Bounded BFS: httpx + **BeautifulSoup** link discovery, same-domain enqueueing, PDF branch, robots/politeness hooks, dedupe within run.

**Independent Test**: Seed page with internal links; after run, child URLs appear as fetch rows; off-domain skipped with `skip_reason`; PDF rows have `pdf_extraction_status`.

- [X] T012 [US2] Implement `fetch_html_for_discovery()` + `extract_same_site_links()` using **httpx** + **BeautifulSoup** in `backend/src/services/scraper/active_crawl/discovery.py`
- [X] T013 [US2] Implement frontier queue, per-run visited set, depth + per-host + global caps in `backend/src/services/scraper/active_crawl/frontier.py`
- [X] T014 [US2] Integrate BFS driver calling `SmartLoader.load_url()` for full retrieval and mapping loader outcome → `retrieval_path` / `outcome` fields in `backend/src/services/scraper/active_crawl/runner.py`; ensure **every successful HTML fetch** persists **primary extracted text** + fingerprint fields per FR-010 (same MVP rules as T009) before Phase 7 refinements. **Note** (see [research.md](./research.md) §2b): discovery (**T012**) may already have fetched the URL via httpx—either **reuse** that HTML when provably equivalent or accept **double fetch** and tune caps / **T031** logging accordingly
- [X] T015 [US2] Implement PDF fetch + **pypdf** text extraction + `pdf_extraction_status` persistence in `backend/src/services/scraper/active_crawl/runner.py` (size caps, `ACTIVE_CRAWL_NO_RAW` respected); for **non-PDF** in-scope binaries use `document_format=other`, `pdf_extraction_status=na`, artifact or explicit skip per [research.md](./research.md) §6
- [X] T016 [US2] Implement minimal `robots.txt` respect (skip enqueue/fetch with `skip_reason=robots`) in `backend/src/services/scraper/active_crawl/robots.py` and call from `runner.py`; support **dev-only** override **`ACTIVE_CRAWL_IGNORE_ROBOTS=1`** (default off) with loud logging when set, per spec **FR-007** internal-testing exception
- [X] T017 [US2] Extend `backend/src/services/scraper/config.py` (or `active_crawl/config.py`) to load seeds from `active_crawl_seeds.txt` with fallback merge to existing lists if required by operators

**Checkpoint**: Multi-page same-domain crawl works under caps; skips are explicit in DB.

---

## Phase 5: User Story 4 — Inspect crawl data in the database (Priority: P2)

**Goal**: Operators can list runs, drill into attempts, and run “latest success per URL” queries documented for append-only history.

**Independent Test**: After a crawl, `psql` snippets from quickstart return expected columns; optional script prints summary.

- [X] T018 [US4] Add `scripts/validate_active_crawl_postgres.sh` (or `.sql` invoked by `psql`) listing recent `crawl_runs` and sample `crawl_fetch_attempts` filtered by run id in `scripts/validate_active_crawl.sql`
- [X] T019 [US4] Update `specs/008-make-cli-web-crawler/quickstart.md` with final table names, indexes, and copy-paste queries matching `003_active_crawl_tables.sql`, and add an **FR-009** subsection contrasting **`make scraper-validate-postgres`** (validates `document_chunks` / existing pipeline) vs **`make active-crawl-validate`** (validates `crawl_runs` / `crawl_fetch_attempts`); update root **`Makefile` help** text wherever `active-crawl` targets are listed
- [X] T020 [US4] Add optional `make active-crawl-validate` in root `Makefile` mirroring `scraper-validate-postgres` ergonomics

**Checkpoint**: Inspection path documented and runnable without the crawler.

---

## Phase 6: User Story 3 — JS-heavy interactions (Priority: P3)

**Goal**: Static-first with documented heuristic escalation to **Playwright** via existing `SmartLoader` / `PlaywrightURLLoader` path; per-seed overrides.

**Independent Test**: Force thin static HTML for a fixture URL in a unit test OR use a known script-heavy seed with low cap; `retrieval_path` shows playwright escalation once; blocked sites record failure detail.

- [X] T021 [US3] Implement stripped-text length heuristic (default threshold per [research.md](./research.md)) and single guarded `force_loader="playwright"` retry in `backend/src/services/scraper/active_crawl/escalation.py`
- [X] T022 [US3] Wire escalation + per-seed `retrieval` preference (static_only / static_first / always_playwright) from optional `data/config/active_crawl_overrides.yaml` parsed in `backend/src/services/scraper/active_crawl/config.py`
- [X] T023 [US3] Ensure `crawl_fetch_attempts.retrieval_path` and error fields capture escalation decisions and Playwright failures distinctly in `backend/src/services/scraper/active_crawl/runner.py`

**Checkpoint**: At least one escalation path verified manually or via pytest with mocks.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Tests, docs, CI safety, FR-010 raw retention toggles.

- [X] T024 [P] Add unit tests for `url_policy.py` in `backend/tests/services/scraper/active_crawl/test_url_policy.py`
- [X] T025 [P] Add unit tests for `frontier.py` dedupe and caps in `backend/tests/services/scraper/active_crawl/test_frontier.py`
- [X] T026 [P] Add unit tests for persistence SQL parameter shaping (mock connection) in `backend/tests/services/scraper/active_crawl/test_persistence.py`
- [X] T027 Document `uv sync --extra scraping` + `playwright install` prerequisites for operators in `specs/008-make-cli-web-crawler/quickstart.md` and root `Makefile` help for `active-crawl` (do not duplicate the **FR-009** validate-target contrast—**T019** owns that)
- [X] T028 Refine **`raw_artifact`** storage for HTML (byte caps, strip oversized bodies, tighten `raw_omitted_reason` codes) on top of the **FR-010 baseline** already required in T009/T014—must not be the first time extracted text appears
- [X] T029 Run `make ci` (or documented backend pytest slice) from repo root and fix regressions in `backend/` per [plan.md](./plan.md) and `.specify/memory/constitution.md`
- [X] T030 [P] Add `backend/tests/services/scraper/active_crawl/ACCEPTANCE_SEEDS.md` documenting **≥5 hosts** spanning static and script-heavy behavior (align with spec **SC-002**) and add `backend/tests/services/scraper/active_crawl/test_sc002_acceptance_seeds.py` that validates the file (non-empty lines, minimum count, no duplicate canonical hosts)
- [X] T031 Emit **structured log lines** after each completed fetch in `backend/src/services/scraper/active_crawl/runner.py` (e.g. `active_crawl_rate host=<host> delta_ms=<int>`) so operators can verify per-host spacing vs `ScraperConfig.RATE_LIMIT_DELAY` / caps in staging logs per **SC-004**; add `backend/tests/services/scraper/active_crawl/test_sc004_rate_log_format.py` asserting regex/format stability

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 → 2 → 3** strictly sequential for MVP integrity.
- **Phase 4** depends on Phase 3 runner + persistence (extend BFS in same `runner.py`).
- **Phase 5** can start after Phase 3 (queries work on partial data) but should finish after Phase 4 for realistic drill-down examples.
- **Phase 6** depends on Phase 4 (full fetch path) and touches `runner.py` / `escalation.py`.
- **Phase 7** last (**T030** can parallelize with other polish tests; **T031** should follow **T014** so `runner.py` emits rate logs).

### User Story Dependencies

| Story | Depends on |
|-------|------------|
| US1 (P1) | Foundational (Phase 2) |
| US2 (P2) | US1 CLI + run loop shell |
| US4 (P2) | US1 persistence tables (Phase 2+) |
| US3 (P3) | US2 SmartLoader integration |

### Parallel Opportunities

- **T002 || T003** (Setup)
- **T024 || T025 || T026 || T030** (Polish tests / docs)
- After Phase 2: developer A on US1 script/Makefile (**T008–T011**) while developer B drafts validation SQL (**T018**) — coordinate on table names once **T004** lands.

### Parallel Example: User Story 1

```bash
# After T004–T007 land, split:
Task T008  # __main__.py
Task T010  # run_active_crawl.sh   (coordinate on module flags with T008)
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1–2.  
2. Complete Phase 3 (US1).  
3. **STOP**: run `make active-crawl` against dev DB; verify `crawl_runs` + attempts for seeds.

### Incremental Delivery

1. Add Phase 4 (US2) for real crawling value.  
2. Add Phase 5 (US4) for operator confidence.  
3. Add Phase 6 (US3) for JS-heavy sites.  
4. Phase 7 hardens for CI and raw retention.

---

## Notes

- Table names in SQL should match what **T018–T019** document (pick real names in **T004**, then freeze).  
- Do not modify `services/scraper/` Modal app in this feature slice.  
- `document_chunks` upsert pipeline remains unchanged; crawl history lives in new tables only.  
- **Task count**: T001–T031 (31 tasks); analysis remediation folded **FR-009 Makefile/quickstart** contrast into **T019** (no duplicate quickstart-only task).  
- **SC-002**: full 90% metric is **staging/manual** per `quickstart.md`; **T030** covers file-level automation only.

# Tasks: Reliable scrape outcomes for protected pages

**Input**: Design documents from `/specs/011-fix-scraper-success/`  
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/crawled-url-outcome.md](./contracts/crawled-url-outcome.md), [quickstart.md](./quickstart.md)

**Tests**: Targeted **unit and integration** tests are included where they reduce regression risk for classification and routing (constitution quality gate); the feature spec does not mandate strict TDD ordering.

**Organization**: Phases follow user story priority (P1 → P2 → P3) after shared setup and foundation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies within the same phase)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`) on story-phase tasks only

## Path conventions

Primary implementation root: `services/scraper/` (see [plan.md](./plan.md)).

---

## Phase 1: Setup (shared infrastructure)

**Purpose**: Dependencies and smoke asset scaffolding.

- [ ] T001 Add `pypdf` and `charset-normalizer` dependencies to `services/scraper/pyproject.toml` per `specs/011-fix-scraper-success/research.md`
- [ ] T002 [P] Create `services/scraper/smoke/crawl_smoke_urls.yaml` with commented schema and placeholder entries documenting SC-001 composition (≥2 HTML, 1 PDF, 1 text, 1 extra)
- [ ] T003 [P] Add optional `max_direct_fetch_bytes` (or equivalent) field to `CrawlConfig` in `services/scraper/src/vecinita_scraper/core/models.py` with safe default aligned to Modal memory

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Shared types, `CrawledPage` shape, classification helpers, persistence payload—**required before any user story behavior ships**.

**⚠️ CRITICAL**: No user story phase work should merge until this phase is complete.

- [ ] T004 Add `ResponseKind` and `FailureCategory` `StrEnum` definitions in `services/scraper/src/vecinita_scraper/core/outcome_kinds.py` aligned to `specs/011-fix-scraper-success/data-model.md`
- [ ] T005 Extend `CrawledPage` in `services/scraper/src/vecinita_scraper/crawlers/crawl4ai_adapter.py` with optional `response_kind`, `failure_category`, and `operator_summary` fields (defaults preserve current callers)
- [ ] T006 [P] Implement substantive-content metrics and HTML outcome classification helpers in `services/scraper/src/vecinita_scraper/crawlers/classification.py` (including Crawl4AI `error_message` substring → `FailureCategory` mapping table)
- [ ] T007 [P] Implement structured `error_message` JSON encode/decode helpers per `specs/011-fix-scraper-success/contracts/crawled-url-outcome.md` in `services/scraper/src/vecinita_scraper/crawlers/outcome_codec.py`
- [ ] T008 Extend `store_crawled_url` in `services/scraper/src/vecinita_scraper/persistence/gateway_http.py` and mirror kwargs in `services/scraper/src/vecinita_scraper/core/db.py`, encoding optional fields into JSON in `error_message` when gateway/DM columns are not yet available

**Checkpoint**: Foundation types and persistence path ready for user stories.

---

## Phase 3: User Story 1 — Understand why a crawl failed (Priority: P1) 🎯 MVP

**Goal**: Operators see **stable failure categories** and plain-language explanations per URL when crawls fail (FR-001, FR-002, spec US1).

**Independent Test**: Crawl a URL that returns HTTP success but no substantive extractable body; job summary shows a **non-generic** `failure_category` and `operator_summary`, not only Crawl4AI’s raw string.

### Implementation for User Story 1

- [ ] T009 [US1] Apply post-crawl substantive-content check and set `success`, `failure_category`, `response_kind`, and `operator_summary` in `services/scraper/src/vecinita_scraper/crawlers/crawl4ai_adapter.py` method `_crawl_single` using `classification.py`
- [ ] T010 [US1] Update `run_scrape_job` in `services/scraper/src/vecinita_scraper/workers/scraper.py` to pass outcome fields into `store_crawled_url` and derive processor `content_type` from `response_kind` when set (else keep `determine_content_type(url)` fallback)
- [ ] T011 [P] [US1] Add unit tests in `services/scraper/tests/unit/test_classification.py` and `services/scraper/tests/unit/test_outcome_codec.py` covering empty HTML, bot/shell-like Crawl4AI messages, and JSON round-trip

**Checkpoint**: US1 delivers operator-visible classification for HTML path failures independently of PDF/text routing.

---

## Phase 4: User Story 2 — Increase successful captures (Priority: P2)

**Goal**: **Direct PDF** and **plain text** URLs use **httpx** + type-specific extractors; HTML path tuned within FR-004/FR-006; smoke list supports SC-001 (spec US2, FR-008).

**Independent Test**: Run unit tests for fetch router + extractors; optionally run `-m live` smoke against approved URLs listed in `services/scraper/smoke/crawl_smoke_urls.yaml`.

### Implementation for User Story 2

- [ ] T012 [US2] Implement `services/scraper/src/vecinita_scraper/crawlers/document_fetcher.py` with bounded HEAD/GET sniff, `Content-Type` + magic-byte detection, and async fetch returning bytes + metadata per `specs/011-fix-scraper-success/research.md`
- [ ] T013 [P] [US2] Implement PDF text extraction and PDF-specific exceptions mapped to `FailureCategory` in `services/scraper/src/vecinita_scraper/crawlers/text_extractors.py`
- [ ] T014 [P] [US2] Implement plain-text decoding with charset fallbacks (`charset-normalizer`) and `text_encoding_failure` / `text_empty` categories in `services/scraper/src/vecinita_scraper/crawlers/text_extractors.py`
- [ ] T015 [US2] Integrate fetch routing in `services/scraper/src/vecinita_scraper/workers/scraper.py` so single-URL jobs invoke `document_fetcher` for PDF/plain_text and `Crawl4AIAdapter` for HTML, synthesizing `CrawledPage` consistently for all branches
- [ ] T016 [US2] Adjust `services/scraper/src/vecinita_scraper/crawlers/crawl4ai_adapter.py` `_build_run_config` wait/timeout behavior to satisfy FR-006 and reduce false “content not ready” vs immediate block confusion (document chosen defaults in `plan.md` or code comments only where necessary)
- [ ] T017 [P] [US2] Add `services/scraper/tests/unit/test_document_fetcher.py` using `httpx.MockTransport` for type sniffing and size-cap behavior
- [ ] T018 [US2] Replace smoke placeholders with operator-approved public URLs (≥5 entries per SC-001) in `services/scraper/smoke/crawl_smoke_urls.yaml` and add `services/scraper/tests/integration/test_smoke_list_composition.py` (no network) plus optional `services/scraper/tests/integration/test_smoke_crawl_live.py` marked `live` for manual/scheduled runs

**Checkpoint**: US2 enables successful or correctly classified outcomes for HTML + direct PDF + direct text targets.

---

## Phase 5: User Story 3 — Stable job semantics for downstream systems (Priority: P3)

**Goal**: When **zero** pages succeed, aggregate job messaging is **structured and honest** (spec US3, contract job-level section).

**Independent Test**: Force a job where every page fails with different categories; `update_job_status` receives an aggregate `error_message` listing capped per-URL summaries without implying infrastructure fault.

### Implementation for User Story 3

- [ ] T019 [US3] Build capped multi-URL aggregate `error_message` in `services/scraper/src/vecinita_scraper/workers/scraper.py` when `processed_count == 0`, per `specs/011-fix-scraper-success/contracts/crawled-url-outcome.md`
- [ ] T020 [P] [US3] Append operator runbook table (`failure_category` → recommended action) to `specs/011-fix-scraper-success/contracts/crawled-url-outcome.md`
- [ ] T021 [P] [US3] Add `services/scraper/tests/integration/test_scrape_job_zero_success_summary.py` asserting aggregate JSON/text shape from `run_scrape_job` with mocked `store_crawled_url` / DB

**Checkpoint**: US3 complete—downstream-visible failure semantics documented and tested at worker boundary.

---

## Phase 6: Polish & cross-cutting concerns

**Purpose**: Docs, repo hygiene, CI validation.

- [ ] T022 [P] Update `services/scraper/README.md` with smoke list location, `live` pytest marker usage, and classification overview for operators
- [ ] T023 Run `services/scraper` test suite and repo `make ci` (or documented equivalent) from repository root; fix any regressions introduced by this feature per project CI rules

---

## Dependencies & execution order

### Phase dependencies

| Phase | Depends on | Notes |
|-------|------------|--------|
| 1 Setup | — | Start immediately |
| 2 Foundational | Phase 1 | **Blocks** all user stories |
| 3 US1 | Phase 2 | MVP deliverable |
| 4 US2 | Phase 2 | Builds on shared `CrawledPage` + persistence; **functionally stacks** on US1 HTML classification but should keep PDF/text paths testable alone via T012–T015 |
| 5 US3 | Phase 3–4 recommended | Needs per-URL `failure_category` populated (US1/US2) |
| 6 Polish | US1–US3 as scoped | Can run final doc/CI after intended stories merge |

### User story dependencies

- **US1**: After Phase 2 only—no dependency on US2/US3.
- **US2**: After Phase 2—parallel with US1 in staffing, but **merge order** should keep US1 classification on `main` before or with US2 to avoid conflicting edits to `crawl4ai_adapter.py` / `scraper.py`.
- **US3**: After US1 (and ideally US2) so aggregate messages include rich categories.

### Parallel opportunities

- **Phase 1**: T002 and T003 in parallel after T001 (or T001–T003 all [P] if dependency only on lockfile—here T002/T003 are [P] once T001 merged or accept parallel PRs touching different files).
- **Phase 2**: T006 and T007 in parallel after T004–T005; T008 follows T007.
- **Phase 3**: T011 parallel after T009–T010 land.
- **Phase 4**: T013 and T014 in parallel; T017 parallel after T012; T018 coordinates YAML + tests.
- **Phase 5**: T020 and T021 in parallel after T019.
- **Phase 6**: T022 parallel before final T023.

---

## Parallel example: User Story 2 extractors

```text
T013 [P] [US2] PDF path in services/scraper/src/vecinita_scraper/crawlers/text_extractors.py
T014 [P] [US2] Plain-text path in services/scraper/src/vecinita_scraper/crawlers/text_extractors.py
```

---

## Implementation strategy

### MVP first (User Story 1 only)

1. Complete Phase 1 and Phase 2.  
2. Complete Phase 3 (US1).  
3. **STOP**: Demo HTML-only classification + persistence to stakeholders.  
4. Proceed to US2/US3 when MVP is accepted.

### Incremental delivery

1. Setup + Foundational → shared library ready.  
2. US1 → operator-readable HTML failures.  
3. US2 → PDF/text routing + smoke list.  
4. US3 → aggregate job semantics + runbook.  
5. Polish → README + `make ci` green.

### Task counts

| Area | Task IDs | Count |
|------|-----------|-------|
| Setup | T001–T003 | 3 |
| Foundational | T004–T008 | 5 |
| US1 | T009–T011 | 3 |
| US2 | T012–T018 | 7 |
| US3 | T019–T021 | 3 |
| Polish | T022–T023 | 2 |
| **Total** | **T001–T023** | **23** |

---

## Notes

- Keep **FR-004** in scope: no deceptive client impersonation; document any Crawl4AI/browser knob changes.  
- Gateway schema migrations (optional columns) are **out of band**—use contract JSON fallback until DM ships.  
- Prefer **small PRs** per phase to simplify review (especially `crawl4ai_adapter.py` vs `scraper.py`).

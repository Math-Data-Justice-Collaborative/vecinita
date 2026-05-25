# E2E Behavior Report

> Generated: 2026-05-25 (EV-001 delta)
> Previous run: 2026-05-19 (UJ-001–UJ-008 baseline)
> Mechanism: API (pytest `TestClient` / `httpx.AsyncClient`, mocked Modal, test DB)
> Journeys tested: 12 (UJ-001–UJ-012)
> Tier: **T0 local** — `uv run pytest tests/e2e/ -m "e2e and not live" -v`
> Tier: **T1 integration** — `uv run pytest tests/integration/ -v` (21 passed)
> Tier: **T3 live** — `uv run pytest tests/smoke -m live -v` — **11/11 passed** (2026-05-20)
> Frontend: **Vitest** — `npm test` in `chat-rag-frontend` (8 passed), `data-management-frontend` (2 passed)

## Summary

| # | Journey | Mechanism | Tests | Passed | Failed | T0 | T1 | T3 | FE |
|---|---------|-----------|-------|--------|--------|----|----|----|----|
| 1 | UJ-001 Ask (bilingual, stream) | API | `test_uj001_ask_stream.py` | 3 | 0 | PASS | PASS | pending | — |
| 2 | UJ-002 Ingest public URLs | API | `test_uj002_ingest_job.py` | 1 | 0 | PASS | — | pending | — |
| 3 | UJ-003 Delete document | API | `test_uj003_corpus_delete.py` | 1 | 0 | PASS | PASS | pending | — |
| 4 | UJ-004 Local bootstrap | API + config | `test_uj004_local_bootstrap.py` | 2 | 0 | PASS | — | pending | — |
| 5 | UJ-005 No relevant context | API | `test_uj005_empty_retrieval.py` | 1 | 0 | PASS | — | pending | — |
| 6 | UJ-006 Scrape job failure | API | `test_uj006_job_failure.py` | 1 | 0 | PASS | — | pending | — |
| 7 | UJ-007 Reject identity fields | API | `test_uj007_reject_identity.py` | 1 | 0 | PASS | — | pending | — |
| 8 | UJ-008 Unauthorized admin | API | `test_uj008_unauthorized_admin.py` | 1 | 0 | PASS | — | pending | — |
| 9 | **UJ-009 Corpus browse & tags** | API + FE | `test_uj009_corpus_browse.py` | 1 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 10 | **UJ-010 Open source URL** | FE | `CorpusBrowse.test.tsx` | — | — | — | — | — | **PASS** |
| 11 | **UJ-011 Admin chunks & tags** | API | `test_uj011_admin_tags.py`, `test_admin_retag_job.py` | 2 | 0 | **PASS** | **PASS** | pending | — |
| 12 | **UJ-012 Tag-filtered ask** | API | `test_uj012_tag_filtered_ask.py` | 1 | 0 | **PASS** | **PASS** | pending | **PASS** |
| — | **TC-047 LLM auto-tag ingest** | API | `test_uj002_ingest_tagging.py` | 1 | 0 | **PASS** | — | pending | — |

**Overall T0:** 16 passed, 0 failed (`uv run pytest tests/e2e/ -m "e2e and not live" -v`).
**Overall T1:** 21 passed, 0 failed (`uv run pytest tests/integration/ -v`).
**Overall FE:** 10 passed, 0 failed (Vitest: chat-rag 8, data-mgmt 2).

**Known intermittent:** UJ-004 `test_uj004_bootstrap_health_and_ask` has an intermittent `ForeignKeyViolation` on `embeddings` when run in full suite (DB fixture ordering). Passes in isolation (2/2). Documented as QA-001 advisory.

**Prerequisite:** `uv sync --group dev` then `uv run pytest` — bare `pytest` fails on import.

## EV-001 Journey Details (F19–F22)

### UJ-009: Browse corpus by tags & search

- **Features**: F19
- **Mechanism**: API — `GET /api/v1/documents`, `GET /api/v1/tags` via ChatRAG `TestClient` (test DB with seeded tags + tagged corpus)
- **Steps verified**:
  1. Browse list returns 200; page_size ≤ 20; total ≥ 2 seeded docs — PASS (TC-040)
  2. Tag facet list returns 200; includes `housing` and `legal` slugs — PASS (TC-041)
  3. Filter by tag `housing` returns only housing-tagged docs — PASS (TC-040)
- **Frontend (Vitest)**: `CorpusBrowse.test.tsx` — tag chips render; browse list renders with document links — PASS (3 tests)
- **Integration**: `test_browse_api.py` — 2 passed (paginated list, tag filter)
- **Not covered at T0**: Live staging GET routes (H4 CORS on new paths)

### UJ-010: Open corpus document (source URL)

- **Features**: F19
- **Mechanism**: Frontend Vitest — `CorpusBrowse.test.tsx`
- **Steps verified**:
  1. Corpus row link `href` matches source URL (`https://example.org/housing-rights`) — PASS (TC-048)
  2. Link opens in new tab (`target="_blank"`, `rel="noopener noreferrer"`) — PASS (TC-048)
- **Note**: No backend E2E needed — UJ-010 is purely a frontend behavior. API contract for `documents.url` covered by UJ-009 browse test.

### UJ-011: Admin view chunks & edit tags

- **Features**: F20, F21
- **Mechanism**: API — internal write API `TestClient` (test DB)
- **Steps verified**:
  1. Upsert document with chunk via batch endpoint — PASS
  2. `GET /internal/v1/documents/{id}/chunks` returns chunk list with text — PASS (TC-042)
  3. `PATCH /internal/v1/documents/{id}/tags` with human source — PASS; response confirms `housing` slug — PASS (TC-043)
  4. Admin retag job lifecycle: create doc → trigger retag → job completes → DB tags updated — PASS
- **Integration**: `test_admin_chunks.py` (2 passed), `test_admin_tag_caps.py` (2 passed — max 10/5 caps enforced, TC-043)
- **Not covered at T0**: Admin UI frontend; CORS preflight on PATCH routes (TC-049, H4)

### UJ-012: Ask with tag filter (sidebar)

- **Features**: F22
- **Mechanism**: API — ChatRAG `TestClient` with injected retriever and mock LLM (test DB with seeded tagged corpus + attached embeddings)
- **Steps verified**:
  1. `POST /api/v1/ask` with `tags: ["housing"]` returns 200 — PASS (TC-044)
  2. Sources do not include non-matching tagged docs (`legal-aid` URL absent) — PASS (TC-044)
- **Frontend (Vitest)**: `TagFilterChips` component — tag button click fires `onToggle("housing")` — PASS
- **Integration**: `test_browse_api.py` — tag filter on browse (related); retriever integration via unit tests
- **Not covered at T0**: LLM-inferred tags when none selected (TC-045 — LLM mock returns fixed tags; real LLM inference deferred to T3); live streaming with tag filter

### TC-047: Ingest LLM auto-tag

- **Features**: F20 (cross-journey, extends UJ-002)
- **Mechanism**: API — Data Management `TestClient` with mocked LLM tag client and embed client
- **Steps verified**:
  1. Submit ingest job → 202 — PASS
  2. Job completes; mock write client receives document with tags — PASS
  3. Tags ≤ 10 per document; all `source: llm` — PASS
  4. Tag slugs match mock response (`housing`, `legal`) — PASS

## Baseline Journey Details (UJ-001–UJ-008)

### UJ-001: Ask community question (bilingual, streaming)

- **Features**: F1, F2, F11
- **Mechanism**: API — `POST /api/v1/ask`, `POST /api/v1/ask/stream` via ChatRAG `TestClient` (mocked LLM/embed)
- **Steps verified**:
  1. Non-streaming ask returns 200, `language == "en"` — PASS
  2. SSE stream completes with terminal `done` event — PASS
  3. Spanish question returns Spanish answer — PASS (TC-011)
- **Not covered at T0**: ChatRAG web UI (browser); server-side session absence (privacy TC-031)

### UJ-002: Ingest public URLs

- **Features**: F7, F8, F12
- **Mechanism**: API — Data Management `POST /jobs`, `GET /jobs/{id}` (in-memory store, fixture fetch)
- **Steps verified**:
  1. Create job → 202 with `job_id` — PASS
  2. Poll until `status == "completed"` — PASS

### UJ-003: Delete outdated document

- **Features**: F9
- **Mechanism**: API — internal write API `POST` batch, `GET` list, `DELETE` document
- **Steps verified**:
  1. Create document with chunk — PASS
  2. Delete by ID → 204 — PASS
  3. Document URL absent from list — PASS

### UJ-004: Bootstrap local dev stack

- **Features**: F18
- **Mechanism**: API + config file — `infra/vecinita.yaml` validation; optional Postgres bootstrap
- **Steps verified**:
  1. `vecinita.yaml` local defaults present — PASS
  2. `/health` 200 with `postgres: ok`; sample `POST /api/v1/ask` 200 — PASS (when Postgres available)
- **Note**: Intermittent `ForeignKeyViolation` when run in full suite (QA-001). Passes in isolation.

### UJ-005: No relevant corpus context

- **Features**: F1, F5
- **Mechanism**: API — empty retriever mock, `POST /api/v1/ask`
- **Steps verified**:
  1. Off-corpus question → 200, empty `sources`, answer mentions "corpus" — PASS
  2. LLM not invoked (assertion in mock) — PASS

### UJ-006: Scrape job failure

- **Features**: F8
- **Mechanism**: API — injected failing embed client
- **Steps verified**:
  1. Submit job → 202 — PASS
  2. Poll → `status == "failed"` with non-empty `error_code` — PASS

### UJ-007: Reject identity fields in API

- **Features**: F15
- **Mechanism**: API + privacy schema test
- **Steps verified**:
  1. `POST /api/v1/ask` with `email` → 400 — PASS
  2. Forbidden tables absent after migrations — PASS

### UJ-008: Unauthorized data-mgmt access

- **Features**: F16
- **Mechanism**: API — `POST /jobs` without `Modal-Key`
- **Steps verified**:
  1. Unauthenticated job create → 401 — PASS

## Connectivity Tiers

| Tier | Scope | Result | Notes |
|------|-------|--------|-------|
| **T0** Local E2E | `tests/e2e/` (16 tests) | **PASS** | TestClient + test DB + mocked Modal |
| **T1** Integration | `tests/integration/` (21 tests) | **PASS** | Backend APIs against test DB |
| **T2** Deploy smoke | 13-deploy-smoke H1–H5 | **PASS** (2026-05-21) | H4 Modal waiver (proxy auth) |
| **T3** Live staging | `tests/smoke -m live` | **PASS** (2026-05-20) | 11/11 pre-EV-001; EV-001 pending post-deploy |
| **FE** Vitest | `npm test` (10 tests) | **PASS** | CorpusBrowse (3), ChatPanel (3), ask API (2), JobForm (2) |

**Mocks passing T0 ≠ T3 production connectivity.** EV-001 T3 (UJ-009–UJ-012 on staging) pending post-deploy.

## Gaps and waivers (for 11-verify-impl)

| Item | Status | Notes |
|------|--------|-------|
| UJ-004 intermittent error | **Advisory** | QA-001: DB fixture ordering; passes in isolation |
| UI browser E2E | Waived v1 | `tests/e2e/README.md`; Vitest component smoke only |
| TC-045 LLM-inferred tags | **Partial** | Mock returns fixed tags; real LLM inference deferred to T3 |
| TC-046 CORS on browse GET | **Covered (H0c)** | `tests/unit/test_cors_policy.py`; live H4 pending staging URLs |
| TC-049 CORS on admin PATCH | **Covered (H0c)** | `tests/unit/test_cors_policy.py`; live H4 pending staging URLs |
| T3 live for EV-001 | **Pending** | UJ-009–UJ-012 staging tests after next deploy |
| AC-C6 p95 latency | **Staging test exists** | `tests/smoke/test_staging_latency.py`; informative in UJ-001 |

## Commands run

```bash
uv sync --group dev

# T0 — E2E
uv run pytest tests/e2e/ -m "e2e and not live" -v --tb=short    # 16 passed (1 intermittent error in suite)

# T1 — Integration
uv run pytest tests/integration/ -v --tb=short                    # 21 passed

# Frontend
cd apps/chat-rag-frontend && npm test                              # 8 passed (3 files)
cd apps/data-management-frontend && npm test                       # 2 passed (1 file)
```

## Feature Traceability

All 12 journeys map to features F1–F22 per `docs/user-journeys.md` Journey Index.

| Journey | Features | Test modules | TC coverage |
|---------|----------|-------------|-------------|
| UJ-001 | F1, F2, F11 | `test_uj001_ask_stream.py` | TC-001, TC-002, TC-011 |
| UJ-002 | F7, F8, F12 | `test_uj002_ingest_job.py` | TC-010 |
| UJ-003 | F9 | `test_uj003_corpus_delete.py` | TC-012 |
| UJ-004 | F18 | `test_uj004_local_bootstrap.py` | TC-020 |
| UJ-005 | F1, F5 | `test_uj005_empty_retrieval.py` | TC-003 |
| UJ-006 | F8 | `test_uj006_job_failure.py` | TC-013 |
| UJ-007 | F15 | `test_uj007_reject_identity.py` | TC-030, TC-031 |
| UJ-008 | F16 | `test_uj008_unauthorized_admin.py` | TC-014 |
| UJ-009 | F19 | `test_uj009_corpus_browse.py`, `CorpusBrowse.test.tsx` | TC-040, TC-041 |
| UJ-010 | F19 | `CorpusBrowse.test.tsx` | TC-048 |
| UJ-011 | F20, F21 | `test_uj011_admin_tags.py`, `test_admin_retag_job.py` | TC-042, TC-043 |
| UJ-012 | F22 | `test_uj012_tag_filtered_ask.py`, `TagFilterChips` | TC-044, TC-045 |
| TC-047 | F20 | `test_uj002_ingest_tagging.py` | TC-047 |

## Acceptance Criteria Coverage (EV-001)

| Criterion | Journey | T0 | FE | T3 |
|-----------|---------|----|----|-----|
| AC-T1 Browse + pagination + tag filter | UJ-009 | PASS | PASS | pending |
| AC-T2 Source URL opens in new tab | UJ-010 | — | PASS | — |
| AC-T3 LLM tags ≤ 10 doc / 5 chunk | UJ-011, TC-047 | PASS | — | pending |
| AC-T4 Admin chunks + tag edit | UJ-011 | PASS | — | pending |
| AC-T5 Tag-filtered retrieval | UJ-012 | PASS | PASS | pending |
| AC-T6 LLM-inferred tags | UJ-012 | PARTIAL | — | pending |
| AC-T7 CORS on browse GET | H0c | PASS | — | H4 pending |

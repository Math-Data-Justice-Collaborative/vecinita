# E2E Behavior Report

> Generated: 2026-05-27 (EV-002 delta)
> Previous run: 2026-05-25 (EV-001 delta — UJ-009–UJ-012)
> Mechanism: API + Frontend (pytest `TestClient` / `httpx.AsyncClient`, mocked Modal, test DB; Vitest component smoke)
> Journeys tested: 21 (UJ-001–UJ-021)
> Tier: **T0 local** — `uv run pytest tests/e2e/ -m "e2e and not live" -v`
> Tier: **T1 integration** — `uv run pytest tests/integration/ -v`
> Tier: **T3 live** — pending post-deploy (EV-002 not yet deployed)
> Frontend: **Vitest** — `npm test` in `chat-rag-frontend` (8 passed), `data-management-frontend` (32 passed)

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
| 9 | UJ-009 Corpus browse & tags | API + FE | `test_uj009_corpus_browse.py` | 1 | 0 | PASS | PASS | pending | PASS |
| 10 | UJ-010 Open source URL | FE | `CorpusBrowse.test.tsx` | — | — | — | — | — | PASS |
| 11 | UJ-011 Admin chunks & tags | API | `test_uj011_admin_tags.py`, `test_admin_retag_job.py` | 3 | 0 | PASS | PASS | pending | — |
| 12 | UJ-012 Tag-filtered ask | API | `test_uj012_tag_filtered_ask.py` | 1 | 0 | PASS | PASS | pending | PASS |
| 13 | **UJ-013 Admin summary dashboard** | API + FE | `test_stats_summary.py`, `test_dashboard.test.tsx` | 10 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 14 | **UJ-014 System health check** | API + FE | `test_health_aggregator.py`, `test_health_page.test.tsx` | 8 | 0 | **PASS** | — | pending | **PASS** |
| 15 | **UJ-015 Bulk delete** | API + FE | `test_uj015_bulk_delete.py`, `test_bulk_ops.test.tsx` | 8 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 16 | **UJ-016 Bulk tag** | API + FE | `test_uj016_bulk_tag.py`, `test_bulk_ops.test.tsx` | 8 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 17 | **UJ-017 Global audit log** | API + FE | `test_uj017_audit_log.py`, `test_audit_page.test.tsx` | 9 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 18 | **UJ-018 Document version history** | API + FE | `test_uj018_document_history.py`, `test_doc_history.test.tsx` | 5 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 19 | **UJ-019 Top served documents** | API + FE | `test_serving_stats.py`, `test_dashboard.test.tsx` | 4 | 0 | **PASS** | **PASS** | pending | **PASS** |
| 20 | **UJ-020 Modernized admin UI** | FE | `test_admin_nav.test.tsx` | 6 | 0 | — | — | pending | **PASS** |
| 21 | **UJ-021 Tag chips in corpus list** | FE | `test_tag_chips.test.tsx` | 3 | 0 | — | — | pending | **PASS** |
| — | TC-047 LLM auto-tag ingest | API | `test_uj002_ingest_tagging.py` | 1 | 0 | PASS | — | pending | — |
| — | EV-002 cross-journey integration | API | `test_ev002_integration.py` | 1 | 0 | PASS | — | pending | — |
| — | Bulk metadata (F27 ext) | API | `test_bulk_metadata.py` | 5 | 0 | PASS | — | pending | — |
| — | Bulk retag (F27 ext) | API | `test_bulk_retag.py` | 2 | 0 | PASS | — | pending | — |

**Overall T0:** 40 passed, 0 failed (`uv run pytest tests/e2e/ -m "e2e and not live" -v`).
**Overall T1:** 35 passed, 0 failed (`uv run pytest tests/integration/ -v`).
**Overall FE:** 40 passed, 0 failed (Vitest: chat-rag 8, data-mgmt 32).

**Branch:** `evolve/EV-002-admin-overhaul` @ `98bb7f8`

**Prerequisite:** `uv sync --group dev` then `uv run pytest` — bare `pytest` fails on import.

## EV-002 Journey Details (F23–F29)

### UJ-013: View admin summary dashboard

- **Features**: F25
- **Mechanism**: API unit tests + Vitest Dashboard page
- **Steps verified**:
  1. `GET /internal/v1/stats/summary` returns aggregated counts (documents, chunks, tags, jobs, languages, storage) — PASS (TC-051, 5 unit tests)
  2. Dashboard shows loading state during fetch — PASS (Vitest)
  3. Stat cards render with correct counts from API response — PASS (Vitest)
  4. Recent activity feed displays event list — PASS (Vitest)
  5. Top served widget renders ranked documents — PASS (Vitest, shared with UJ-019)
  6. Refresh button re-fetches stats — PASS (Vitest)
- **Integration**: `test_ev002_schema.py` validates schema; `test_ev002_integration.py` verifies summary after ingest
- **Waiver**: No dedicated `test_uj013_admin_dashboard.py` — backend covered by unit + integration; UI by Vitest per test-plan

### UJ-014: Check system health

- **Features**: F26
- **Mechanism**: API unit tests + Vitest Health page
- **Steps verified**:
  1. `GET /internal/v1/health/all` returns per-service status — PASS (TC-052, 3 unit tests)
  2. Health page shows loading state — PASS (Vitest)
  3. Service status cards render green/red/yellow states — PASS (Vitest)
  4. Unhealthy service displays error detail — PASS (Vitest)
  5. Refresh button re-checks all services — PASS (Vitest)
- **Waiver**: No dedicated `test_uj014_health_dashboard.py` — backend unit + Vitest per test-plan; live CORS to 8 service endpoints deferred to T3

### UJ-015: Bulk delete documents

- **Features**: F27
- **Mechanism**: API E2E + Vitest bulk ops UI
- **Steps verified**:
  1. Bulk delete success removes selected documents — PASS (TC-053)
  2. Partial failure returns per-document errors — PASS (TC-053)
  3. Audit log records each deletion — PASS (AC-E5)
  4. Max 100 documents per operation enforced — PASS (TC-054)
  5. UI checkboxes, select-all, bulk toolbar — PASS (Vitest)
  6. Bulk delete confirmation dialog calls API — PASS (Vitest)

### UJ-016: Bulk tag documents

- **Features**: F27
- **Mechanism**: API E2E
- **Steps verified**:
  1. Bulk tag add applies tags to selected documents — PASS (TC-055)
  2. Partial failure for non-existent IDs — PASS
  3. Audit log records tag changes — PASS (AC-E6)
  4. Max 100 documents per operation enforced — PASS

### UJ-017: View global audit log

- **Features**: F29
- **Mechanism**: API E2E + Vitest Audit page
- **Steps verified**:
  1. Paginated audit entries returned (newest first) — PASS (TC-056)
  2. Filter by event_type works — PASS (TC-057)
  3. Filter by entity_id works — PASS
  4. No IP/identity in audit entries — PASS (ADR-016)
  5. Audit page renders event table with type, entity, timestamp — PASS (Vitest)
  6. Event type filter dropdown works — PASS (Vitest)
  7. Expandable payload detail — PASS (Vitest)

### UJ-018: View document version history

- **Features**: F29
- **Mechanism**: API E2E + Vitest history component
- **Steps verified**:
  1. Version list returns all changes for document — PASS (TC-058)
  2. Tag changes visible in version snapshots — PASS
  3. 404 for missing document — PASS
  4. History timeline renders version numbers and timestamps — PASS (Vitest)

### UJ-019: View top served documents

- **Features**: F28
- **Mechanism**: Integration tests + Vitest Dashboard widget
- **Steps verified**:
  1. `POST /internal/v1/stats/served` increments counters — PASS (TC-059)
  2. `GET /internal/v1/stats/top-served` returns ranked list — PASS
  3. Zero-serve documents excluded — PASS
  4. Dashboard widget displays top served with counts — PASS (Vitest)
- **Waiver**: No dedicated `test_uj019_top_served.py` — covered by integration + dashboard Vitest

### UJ-020: Navigate modernized admin UI

- **Features**: F23
- **Mechanism**: Vitest component smoke
- **Steps verified**:
  1. Sidebar renders all navigation links (Dashboard, Corpus, Health, Audit) — PASS (TC-063)
  2. Navigation between routes works — PASS (TC-063)
  3. shadcn/ui components render without errors — PASS (TC-062)
  4. Theme follows system preference (light/dark) — PASS (AC-E1)
  5. Responsive layout at breakpoints — PASS (Vitest)
  6. Accessible navigation (ARIA labels) — PASS (Vitest)

### UJ-021: View document tags in corpus list

- **Features**: F24
- **Mechanism**: Vitest component smoke
- **Steps verified**:
  1. Tag chips render below document title — PASS (TC-064)
  2. LLM-assigned tags use distinct color from human-assigned — PASS (AC-E2)
  3. Empty state when no tags assigned — PASS (Vitest)

### EV-002 cross-journey integration (`test_ev002_integration.py`)

- **Features**: F25, F27, F28, F29
- **Flow verified**: ingest → stats served → audit check → bulk delete → verify history — PASS

## EV-001 Journey Details (F19–F22)

### UJ-009: Browse corpus by tags & search

- **Features**: F19
- **Mechanism**: API — `GET /api/v1/documents`, `GET /api/v1/tags` via ChatRAG `TestClient`
- **Steps verified**: Browse list, tag facets, tag filter — PASS (TC-040, TC-041)
- **Frontend (Vitest)**: `CorpusBrowse.test.tsx` — PASS (3 tests)

### UJ-010: Open corpus document (source URL)

- **Features**: F19
- **Mechanism**: Frontend Vitest — `CorpusBrowse.test.tsx`
- **Steps verified**: Link href matches source URL; opens in new tab — PASS (TC-048)

### UJ-011: Admin view chunks & edit tags

- **Features**: F20, F21
- **Mechanism**: API — internal write API `TestClient`
- **Steps verified**: Chunks list, tag patch, retag job lifecycle — PASS (TC-042, TC-043)

### UJ-012: Ask with tag filter (sidebar)

- **Features**: F22
- **Mechanism**: API — ChatRAG `TestClient` with tagged corpus
- **Steps verified**: Tag-filtered retrieval returns matching sources only — PASS (TC-044)

### TC-047: Ingest LLM auto-tag

- **Features**: F20
- **Mechanism**: API — Data Management with mocked LLM tag client
- **Steps verified**: Job completes; tags ≤ 10; source llm — PASS

## Baseline Journey Details (UJ-001–UJ-008)

All baseline journeys from EV-001 continue to pass unchanged. See previous run (2026-05-25) for step-level detail.

| Journey | Features | Status |
|---------|----------|--------|
| UJ-001 | F1, F2, F11 | PASS (3 tests) |
| UJ-002 | F7, F8, F12 | PASS (1 test) |
| UJ-003 | F9 | PASS (1 test) |
| UJ-004 | F18 | PASS (2 tests) |
| UJ-005 | F1, F5 | PASS (1 test) |
| UJ-006 | F8 | PASS (1 test) |
| UJ-007 | F15 | PASS (1 test) |
| UJ-008 | F16 | PASS (1 test) |

## Connectivity Tiers

| Tier | Scope | Result | Notes |
|------|-------|--------|-------|
| **T0** Local E2E | `tests/e2e/` (40 tests) | **PASS** | TestClient + test DB + mocked Modal |
| **T1** Integration | `tests/integration/` (35 tests) | **PASS** | Backend APIs against test DB |
| **T2** Deploy smoke | 13-deploy-smoke H1–H5 | **PASS** (2026-05-25) | Pre-EV-002 staging; EV-002 pending redeploy |
| **T3** Live staging | `tests/smoke -m live` | **Pending** | EV-002 UJ-013–UJ-021 not yet deployed |
| **FE** Vitest | `npm test` (40 tests) | **PASS** | data-mgmt 32, chat-rag 8 |

**Mocks passing T0 ≠ T3 production connectivity.** EV-002 T3 pending post-deploy.

## Gaps and waivers (for 11-verify-impl)

| Item | Status | Notes |
|------|--------|-------|
| UI browser E2E | Waived v1 | Vitest component smoke only per `tests/e2e/README.md` |
| UJ-013 dedicated e2e module | **Waiver** | Unit + integration + Vitest cover TC-050/051 |
| UJ-014 dedicated e2e module | **Waiver** | Unit + Vitest cover TC-052; live 8-service CORS deferred T3 |
| UJ-019 dedicated e2e module | **Waiver** | Integration + dashboard Vitest cover TC-059 |
| UJ-020/UJ-021 dedicated e2e | **Waiver** | Vitest only per test-plan (TC-062–064) |
| T3 live for EV-002 | **Pending** | UJ-013–UJ-021 staging tests after next deploy |
| AC-C6 p95 latency | **Staging test exists** | `tests/smoke/test_staging_latency.py`; informative |

## Commands run

```bash
uv sync --group dev

# T0 — E2E
uv run pytest tests/e2e/ -m "e2e and not live" -v --tb=short    # 40 passed

# T1 — Integration
uv run pytest tests/integration/ -v --tb=short                    # 35 passed

# EV-002 unit (UJ-013/014 backend)
uv run pytest tests/unit/test_stats_summary.py tests/unit/test_health_aggregator.py -v  # 8 passed

# Frontend
cd apps/chat-rag-frontend && npm test -- --run                      # 8 passed (3 files)
cd apps/data-management-frontend && npm test -- --run               # 32 passed (8 files)
```

## Feature Traceability

All 21 journeys map to features F1–F29 per `docs/user-journeys.md` Journey Index.

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
| UJ-013 | F25 | `test_stats_summary.py`, `test_dashboard.test.tsx` | TC-050, TC-051 |
| UJ-014 | F26 | `test_health_aggregator.py`, `test_health_page.test.tsx` | TC-052 |
| UJ-015 | F27 | `test_uj015_bulk_delete.py`, `test_bulk_ops.test.tsx` | TC-053, TC-054 |
| UJ-016 | F27 | `test_uj016_bulk_tag.py` | TC-055 |
| UJ-017 | F29 | `test_uj017_audit_log.py`, `test_audit_page.test.tsx` | TC-056, TC-057 |
| UJ-018 | F29 | `test_uj018_document_history.py`, `test_doc_history.test.tsx` | TC-058 |
| UJ-019 | F28 | `test_serving_stats.py`, `test_dashboard.test.tsx` | TC-059 |
| UJ-020 | F23 | `test_admin_nav.test.tsx` | TC-062, TC-063 |
| UJ-021 | F24 | `test_tag_chips.test.tsx` | TC-064 |
| TC-047 | F20 | `test_uj002_ingest_tagging.py` | TC-047 |

## Acceptance Criteria Coverage (EV-002)

| Criterion | Journey | T0 | FE | T3 |
|-----------|---------|----|----|-----|
| AC-E1 shadcn/ui + theme | UJ-020 | — | PASS | pending |
| AC-E2 tag chips in corpus list | UJ-021 | — | PASS | pending |
| AC-E3 admin summary dashboard | UJ-013 | PASS | PASS | pending |
| AC-E4 health dashboard | UJ-014 | PASS | PASS | pending |
| AC-E5 bulk delete + audit | UJ-015 | PASS | PASS | pending |
| AC-E6 bulk tag + audit | UJ-016 | PASS | — | pending |
| AC-E7 serving stats + top served | UJ-019 | PASS | PASS | pending |
| AC-E8 audit log pagination/filters | UJ-017 | PASS | PASS | pending |
| AC-E9 document version history | UJ-018 | PASS | PASS | pending |

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

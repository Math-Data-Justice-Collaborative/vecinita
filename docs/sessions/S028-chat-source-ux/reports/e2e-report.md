# E2E Behavior Report — EV-026 / S028 (F72–F74)

> Generated: 2026-08-06  
> Mechanism: mixed — API (FastAPI TestClient) + Vitest (SourceList / DocumentAdmin)  
> Journeys: **UJ-077**, **UJ-078**, **UJ-079** (+ regression **UJ-076** post QA-S028-001)  
> Branch: `evolve/EV-026-chat-source-ux` @ `8537690`  
> Mode: evolve / delta · after **09-qa** remediation  
> Features: **F72** citation URL safety · **F73** relevance-gated sources · **F74** display_title  

[Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
[Spec: docs/user-journeys.md §UJ-077] [Spec: docs/user-journeys.md §UJ-078] [Spec: docs/user-journeys.md §UJ-079]  
[Spec: docs/test-plan.md §TC-242–251]  
[Spec: docs/acceptance-criteria.md §AC-SU1–SU10]  
[Spec: docs/sessions/S028-chat-source-ux/reports/qa-remediation.md]

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-077 Citation link only for valid http(s) | Vitest `SourceList` | T0-UI | **PASS** | TC-242–244 · 8/8 |
| 2 | UJ-078 Ask sources length 0…top_k | API e2e TestClient | T0 | **PASS** | TC-245–247 · 2/2 |
| 3 | UJ-079 Operator sets display_title | API e2e + Vitest admin | T0 | **PASS** | TC-248–251 · API 1/1; DocumentAdmin + corpus PATCH green |
| 4 | UJ-076 F36 promote E0 retain (regression) | API e2e TestClient | T0 | **PASS** | TC-239 / QA-S028-001 · 4/4 |
| — | Browser / Playwright live | staging | T2/T3 | **DEFERRED** | QA-S028-003 → 13; H4–H5 AskQuestion (S028-D2) |
| — | T1 Integration | `tests/integration/` | T1 | **OUT OF SCOPE** | Delta; covered at 07/09 |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke |
| — | T3 Live UJ | staging/prod | T3 | **DEFERRED** | 13 / 15 |

**Overall T0 (EV-026 delta):** **PASS** — UJ-077–079 green; UJ-076 regression green after remediation.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** | pytest UJ-078/079/076 **7 passed**; Vitest SourceList **8 passed**; DocumentAdmin + corpus **49 passed** (suite files) |
| **T2 connectivity** | **DEFERRED** | QA-S028-003 → 13-deploy-smoke H4–H5 (staging FE URLs unset) |
| **T3 browser** | **DEFERRED** | Live browser UJ after H4–H5; T0 Vitest ≠ production CORS/`VITE_*` |

## Journey → test matrix

| Journey | Module | TCs | T0 | T3 |
|---------|--------|-----|----|-----|
| UJ-077 | `apps/chat-rag-frontend/src/components/SourceList.test.tsx` | TC-242–244 | **PASS** | Live SourceList @ 13 |
| UJ-078 | `tests/e2e/test_uj078_relevance_sources.py` | TC-245–247 | **PASS** | Live ask sources @ 13 |
| UJ-079 | `tests/e2e/test_uj079_display_title.py` + Vitest DocumentAdmin | TC-248–251 | **PASS** | Live rename + cite @ 13 |
| UJ-076 (reg.) | `tests/e2e/test_uj076_embed_promote_report.py` | TC-232/235–236/239/241 | **PASS** | Live promote @ 13 |

## UJ-077 step results (Vitest)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | Valid `https`/`http` → `<a href>` | TC-242 · linked sources + absolute http | **PASS** |
| 2 | Invalid URL (`fixture://`, relative, `javascript:`) → plain title | TC-243 | **PASS** |
| 3 | Missing URL → title plain text; no ingest change | TC-244 | **PASS** |

```text
cd apps/chat-rag-frontend && npm test -- --run src/components/SourceList.test.tsx
# Test Files  1 passed · Tests  8 passed
```

## UJ-078 step results (API e2e)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | Few strong hits — `sources[]` not padded to `top_k` | TC-245–246 | **PASS** |
| 2 | Weak-only / none clear bar — empty `sources[]` valid | TC-247 | **PASS** |

```text
uv run pytest tests/e2e/test_uj078_relevance_sources.py -m "e2e and not live" -v
# 2 passed
```

## UJ-079 step results (API e2e + Vitest)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1–2 | PATCH `display_title` + DocumentAdmin save/clear | TC-248, TC-251 · Vitest UJ-079 / TC-251 | **PASS** |
| 3 | Ask citation uses coalesce display title | TC-249 · `test_uj079_display_title.py` | **PASS** |
| 4 | Rescrape preserves `display_title` | TC-250 (unit/integration @ 07/09; e2e cites coalesce path) | **PASS** (prior + API cite) |

```text
uv run pytest tests/e2e/test_uj079_display_title.py -m "e2e and not live" -v
# 1 passed
cd apps/data-management-frontend && npm test -- --run src/test/test_document_admin.test.tsx src/api/corpus.test.ts
# Test Files  2 passed · Tests  49 passed
```

## UJ-076 regression (QA-S028-001)

| Step / TC | Assertion | Status |
|-----------|-----------|--------|
| TC-239 | Promote activates shadow; E0 / `LEGACY_E0` retained | **PASS** |
| TC-232/241, 235–236 | Stamp + EN/ES report | **PASS** |

```text
uv run pytest tests/e2e/test_uj076_embed_promote_report.py -m "e2e and not live" -v
# 4 passed in <1s @ 8537690
```

## Commands (combined delta)

```bash
uv run pytest \
  tests/e2e/test_uj078_relevance_sources.py \
  tests/e2e/test_uj079_display_title.py \
  tests/e2e/test_uj076_embed_promote_report.py \
  -m "e2e and not live" -v --tb=short
# 7 passed @ 8537690

cd apps/chat-rag-frontend && npm test -- --run src/components/SourceList.test.tsx
cd apps/data-management-frontend && npm test -- --run \
  src/test/test_document_admin.test.tsx src/api/corpus.test.ts
```

## AC mapping (delta @ 10-e2e)

| AC | Status @ 10-e2e |
|----|-----------------|
| AC-SU1 (safe href) | **PASS** T0-UI (TC-242–243) |
| AC-SU2 (plain text invalid/missing) | **PASS** T0-UI (TC-243–244) |
| AC-SU3 (0…top_k, no pad) | **PASS** T0 (TC-245–246) |
| AC-SU4 (filter weak) | **PASS** T0 (TC-245–246) |
| AC-SU5 (empty sources valid) | **PASS** T0 (TC-247) |
| AC-SU6 (single-doc display_title) | **PASS** T0 API + Vitest (TC-248) |
| AC-SU7 (audit document.edited) | **PASS** prior unit/integration @ 07/09 |
| AC-SU8 (COALESCE in citations) | **PASS** T0 (TC-249) |
| AC-SU9 (rescrape preserves display) | **PASS** prior unit + ADR-051 |
| AC-SU10 (null clears → scraped title) | **PASS** Vitest TC-251 |
| AC-SU11 | **N/A** out of EV-026 |

## Playwright / browser

**T0-ui** Playwright suite was green at 09-qa (46 passed, 2 staging skipped). Live H4–H5 **not** run — deferred to **13** per QA-S028-003 / S028-D2.

## Recommendation

**10-e2e can be marked `completed`** for EV-026:

- T0 UJ-077–079 **PASS**
- UJ-076 regression **PASS** (QA-S028-001 closed)
- T2/T3 / H4–H5 deferred to **13-deploy-smoke** (AskQuestion)

Collect with 09-qa + remediation at **11-verify-impl** (carry QA-S028-005 issue close).

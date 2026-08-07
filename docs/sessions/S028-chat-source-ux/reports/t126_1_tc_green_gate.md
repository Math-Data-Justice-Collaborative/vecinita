# T126.1 — TC-242–251 green gate

**Session:** S028-chat-source-ux · **Cycle:** EV-026 · **Milestone:** M126  
**Date:** 2026-08-06  
**Branch tip at run:** `aecb764` (M125)

[Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
[Spec: docs/test-plan.md §TC-242–251] [Spec: docs/acceptance-criteria.md §AC-SU1–SU10]  
[Spec: docs/user-journeys.md §UJ-077–UJ-079]

## Result

| Gate | Status | Evidence |
|------|--------|----------|
| TC-242–244 F72 URL helper + SourceList | **PASS** | `packages/frontend-ui` Vitest (6) + `SourceList.test.tsx` (8) |
| TC-245–247 F73 relevance / no-pad | **PASS** | unit `test_service` threshold cases + `tests/e2e/test_uj078_relevance_sources.py` |
| TC-248–251 F74 display_title | **PASS** | unit migration/PATCH/COALESCE + `tests/e2e/test_uj079_display_title.py` + admin Vitest |
| CORS H0c PATCH `/documents/{id}` | **PASS** | `tests/unit/test_cors_ev002.py::test_cors_patch_document_metadata` |
| Playwright | **N/A** | optional only (RD-317); Vitest covers UJ-077/079 UI |

## Commands (local)

```bash
# F72 Vitest
cd packages/frontend-ui && npm test -- --run src/test/isSafeHttpUrl.test.ts
cd apps/chat-rag-frontend && npm test -- --run src/components/SourceList.test.tsx

# F73–F74 pytest (+ CORS)
uv run pytest \
  tests/unit/chat_rag/test_service.py::test_retrieve_dense_score_threshold_no_pad \
  tests/unit/chat_rag/test_service.py::test_retrieve_all_below_threshold_returns_empty_sources \
  tests/unit/chat_rag/test_service.py::test_retrieve_ce_threshold_no_pad_to_top_k \
  tests/e2e/test_uj078_relevance_sources.py \
  tests/unit/database/test_ev026_display_title.py \
  tests/unit/rag/test_display_title_coalesce.py \
  tests/unit/internal_write_api/test_display_title.py \
  tests/e2e/test_uj079_display_title.py \
  tests/unit/test_cors_ev002.py::test_cors_patch_document_metadata -q

# F74 admin Vitest
cd apps/data-management-frontend && npm test -- --run src/test/test_document_admin.test.tsx -t display_title
```

**Outcome:** all listed suites green (2026-08-06). Combined pytest slice: 17 + 6 = 23 passed; Vitest: 6 + 8 + 2 = 16 passed.

## Next

T126.2 — ADR-051 Accepted; OpenAPI/api-contract confirm; inventory unchanged.

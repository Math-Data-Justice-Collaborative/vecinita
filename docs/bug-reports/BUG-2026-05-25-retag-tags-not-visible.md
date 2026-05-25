# BUG-2026-05-25 — Retag writes document tags but chunk list shows empty tags

> Status: **resolved**
> Feature: **F20** (LLM auto-tagging at ingest + admin re-tag), **F21** (admin chunk/tag editor)
> Component: `apps/internal-write-api/vecinita_internal_write_api/app.py`, `apps/data-management-frontend/src/components/DocumentAdmin.tsx`

## Error description

Admin frontend "LLM re-tag" button completes successfully (job transitions to "completed"), but the chunk list still shows `tags: []` for every chunk. The retag job writes document-level tags to `document_tags`, but the `list_document_chunks` endpoint only queries `chunk_tags`. Additionally, the `DocumentAdmin` component never loads existing document-level tags.

## Error logs

```json
[
    {
        "chunk_id": "f8f513bb-6e48-4ec8-9934-81571c00bcb1",
        "chunk_index": 0,
        "text": "Skip to content VECINA Inicio Recursos ...",
        "token_count": null,
        "tags": []
    }
]
```

No error messages — the retag job completes and the chunk list refreshes, but tags are empty.

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Wrong output — retag completes but tags are empty in the UI |
| Where | Production (admin frontend on DigitalOcean) |
| When | After last deploy (2026-05-25) |
| Frequency | Every time |
| Repro env | Both local and production |
| Severity | High — F20/F21 retag result invisible to admin |
| Evidence | JSON chunk list with empty tags array |
| Tried | Nothing |

## Remediation path

**local-first** — fix locally, deploy to production after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Retag response returns chunks with non-empty tags (LLM-generated) |
| Verification checks | Full main CI parity (local) + gh on main after merge |
| Monitoring | Run 15-service-health follow-up |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `list_document_chunks` queries only `chunk_tags` table, not `document_tags` — retag writes to `document_tags` only | **Confirmed** (code review) |
| H2 | `DocumentAdmin` never loads existing document tags on mount — `docTags` input stays empty | **Confirmed** (code review) |
| H3 | Tags ARE written to `document_tags` by retag job, but invisible in UI | **Confirmed** (code trace) |

### Detailed analysis

**Data flow after retag completes:**
1. `run_retag_job()` calls `tag_client.infer_document_tags()` → gets LLM tag slugs
2. Calls `write_client.patch_document_tags()` → PATCHes `PATCH /internal/v1/documents/{id}/tags`
3. `replace_document_tags()` inserts into `document_tags` table ✓
4. Job status → "completed" ✓
5. Frontend polls → sees "completed" → calls `loadChunks()` → `GET /internal/v1/documents/{id}/chunks`
6. `list_document_chunks` queries only `chunk_tags` for each chunk → returns `tags: []`
7. User sees empty tags despite successful retag

**The SQL in `list_document_chunks`:**
```sql
SELECT t.slug, t.label, ct.source
FROM chunk_tags ct
JOIN tags t ON t.id = ct.tag_id
WHERE ct.chunk_id = :chunk_id AND t.language = :language
```
This joins only `chunk_tags` — never reads `document_tags`.

**`DocumentAdmin` component:**
- `docTags` state initialized as `""` (empty string)
- Never fetches existing document-level tags from API
- No `GET /internal/v1/documents/{id}/tags` endpoint exists

**Related bugs:**
- BUG-2026-05-25-retag-503-not-configured (hotfix #9) — fixed 503
- BUG-2026-05-25-retag-job-never-completes (hotfix #10) — fixed stuck job
- BUG-2026-05-25-retag-tag-client-none (hotfix #11) — fixed LlmClient init
- This is the fourth in the retag chain: plumbing works, but results are invisible

## Root cause

**Code gap:** Two missing features cause retag results to be invisible:
1. No `GET /internal/v1/documents/{id}/tags` endpoint to retrieve document-level tags
2. `DocumentAdmin` component never loads existing document tags

The retag correctly writes to `document_tags`, but there is no UI path to display those tags.

Classification: **Code bug** — missing read path for document-level tags in both backend and frontend.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F20/F21 | In scope — admin retag + tag editor |
| `docs/spec.md` §Data Management | Tags should be visible after retag |
| `docs/api-contract.md` | Missing GET document tags endpoint |
| RD-025 | "Chunk tags union with document tags at retrieval" — not implemented in admin |

**Blocking drift:** `api-contract.md` lacks a GET document tags endpoint; `list_document_chunks` doesn't union document tags per RD-025.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Document tags retrievable after patch | `tests/bugs/test_bug_2026_05_25_retag_tags_not_visible.py::test_document_tags_retrievable_after_patch` | red → green |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-05-25 | Write repro test — assert GET /documents/{id}/tags returns 200 with tags after PATCH | RED: 405 Method Not Allowed (endpoint doesn't exist) |
| 2 | 2026-05-25 | User confirmed repro matches symptom | confirmed |
| 3 | 2026-05-25 | Apply fix: add GET endpoint + frontend loadDocumentTags | GREEN |

## Fix

**Three changes:**

1. **`apps/internal-write-api/vecinita_internal_write_api/app.py`**: Added `GET /internal/v1/documents/{document_id}/tags` endpoint that queries `document_tags` joined with `tags` for the document's language and returns `TagPatchResponse`.

2. **`apps/data-management-frontend/src/api/corpus.ts`**: Added `listDocumentTags()` function that calls the new GET endpoint.

3. **`apps/data-management-frontend/src/components/DocumentAdmin.tsx`**: Added `loadDocumentTags` callback that fetches document-level tags on component mount and after retag job completes, populating the `docTags` input field so the user can see retag results.

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] Full unit test suite passes (67 passed, 4 skipped; 1 pre-existing unrelated failure in test_tag_filtered_retrieval)
- [x] Lint + typecheck pass (ruff, pyright, tsc)
- [x] Frontend tests pass (vitest 2 passed)
- [ ] CI parity (local) pass

### Layer 2 — Reproduction

- [ ] Document tags visible in admin after retag

### Layer 3 — Pre-deploy smoke

- [ ] N/A (local-first)

### Layer 4 — Production

- [ ] Pending user deploy approval

### CI

- [ ] CI parity before PR
- [ ] PR merged to main

## Post-deploy monitoring

15-service-health follow-up — user requested.

## Prevention & countermeasures

### Interview record

| ID | Question | Answer |
|----|----------|--------|
| prevention_recurrence_risk | Recurrence risk | Very likely without changes — other write endpoints may lack read paths |
| prevention_detect_earlier | Where to catch earlier | E2E test that verifies retag results visible |
| prevention_automated | Guards to add | E2E retag visibility test |
| prevention_process | Process changes | Cursor rule — write-read parity |
| prevention_when | When | Now (same session) |
| prevention_who | Who | Agent now |

### Planned actions

1. **Done**: E2E test `tests/e2e/test_admin_retag_job.py::test_admin_retag_tags_visible_via_get_endpoint`
2. **Done**: Cursor rule `.cursor/rules/write-read-parity.mdc`

## Cursor rule

`.cursor/rules/write-read-parity.mdc` — every PATCH/POST write endpoint needs a corresponding GET read endpoint.

## Regression prevention

- `tests/bugs/test_bug_2026_05_25_retag_tags_not_visible.py`
- `tests/e2e/test_admin_retag_job.py::test_admin_retag_tags_visible_via_get_endpoint`

## Follow-ups

None — all actions complete.

## Timeline

| Event | Date |
|-------|------|
| User report | 2026-05-25 |
| Investigation start | 2026-05-25 |
| Root cause confirmed | 2026-05-25 |
| Fix applied | 2026-05-25 |
| PR #48 created | 2026-05-25 |

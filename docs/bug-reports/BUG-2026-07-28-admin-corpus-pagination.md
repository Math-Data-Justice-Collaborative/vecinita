# BUG-2026-07-28 — Admin Corpus Documents table lacks pagination

**Status:** fixing  
**Severity:** medium (UX / performance as corpus grows)  
**Feature:** F9 / F31 — Admin corpus list  
**GitHub:** [#112](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/112)  
**Session:** S012-hotfix-admin-ui-112-105  
**Reported:** 2026-07-28

## Error description

The **Corpus Documents** table on `/corpus` loads and renders the **entire** corpus in one
unpaginated table. Operators cannot page; DOM and payload grow with corpus size.

## Error logs

N/A (behavioral / UX). Observed on staging admin `/corpus`.

## Symptoms & reproduction

| Field | User report |
|-------|-------------|
| Symptom type | Missing pagination / unbounded list |
| Where | Staging admin frontend |
| Frequency | Always |
| Repro env | Staging (interview) |
| Severity | Medium |
| Related | UJ-003; prior art Users page + ChatRAG CorpusBrowse |

## Investigation

| Time | Finding |
|------|---------|
| 2026-07-28 | `CorpusList.tsx` calls `listDocuments()` with no page state / no `PaginationControls`. |
| 2026-07-28 | `GET /internal/v1/documents` returns flat `DocumentSummary[]` (no `page`/`page_size`/`total`). |
| 2026-07-28 | Users page + public browse already use `{ items\|users, page, page_size, total }`. |

## Root cause

*(pending Phase 1)* — FE + API both lack pagination contract.

## Spec conformance

| Check | Result |
|-------|--------|
| UJ-003 | List/delete works; pagination not required in journey text — UX gap |
| api-contract / OpenAPI `GET /documents` | Flat array today — **spec update needed** with pagination (user approved hotfix path S012-D4) |
| Users / browse parity | Implementation drift vs other admin tables |

## Remediation path

**local-first** — extend write API + FE; one PR with #105; merge+deploy after approval.

## Repro tests

| Layer | Path | Status |
|-------|------|--------|
| API (OpenAPI contract) | `tests/bugs/test_bug_2026_07_28_admin_corpus_pagination.py` | **GREEN** |
| UI | `apps/data-management-frontend/src/test/test_bug_2026_07_28_admin_corpus_pagination.test.tsx` | **GREEN** |

## Root cause

FE + API both lacked pagination: `GET /internal/v1/documents` returned a flat array;
`CorpusList` rendered all rows with no `PaginationControls`.

## Fix

- Schema: `DocumentListPage` (`items`, `page`, `page_size`, `total`)
- API: `GET /internal/v1/documents?page=&page_size=` (default 50)
- FE: `listDocuments` + `CorpusList` with shared `PaginationControls`; **page-scoped** select-all
- OpenAPI + `docs/api-contract.md` updated; test helpers parse `items`

## Verification plan

*(confirm with user — Step 0.5)*

| Field | Proposed |
|-------|----------|
| Success criterion | Corpus table paginates server-side; total visible; page change fetches that page only |
| Checks | pytest bugs + Vitest + openapi check; PR CI; staging `/corpus` after deploy |
| Monitoring | User staging check after deploy |

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Phase 0 intake | Hotfix pagination approved; one PR with #105 |
| 2 | Bulk-select decision | Recommend **page-scoped** select-all (match typical Users patterns) |

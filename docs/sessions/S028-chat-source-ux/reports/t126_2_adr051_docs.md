# T126.2 — ADR-051 Accepted + OpenAPI / inventory

**Session:** S028-chat-source-ux · **Cycle:** EV-026 · **Milestone:** M126  
**Date:** 2026-08-06

[Corpus: feature-list.md §F74] [Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md]  
[Spec: docs/api-contract.md §PATCH /internal/v1/documents/{document_id}]  
[Corpus: dependency-inventory.md] [Spec: docs/adr/ADR-011-openapi-contract-source-of-truth.md]

## Result

| Item | Status | Notes |
|------|--------|-------|
| ADR-051 | **Accepted** | Promoted from Proposed at M126 / T126.2 |
| OpenAPI | **PASS** | `openapi/internal-write.yaml` has PATCH `/documents/{document_id}`, `DocumentPatchRequest`, `display_title`; `scripts/check_openapi_specs.sh` OK |
| api-contract.md | **PASS** | Single-doc PATCH + bulk `display_title` + OpenAPI cross-ref |
| dependency-inventory | **Unchanged deps** | No new packages; F72 helpers noted on `vecinita-frontend-ui`; EV-026 no-new-deps note |
| RD-321 ingest title→display | **Deferred** | Remains out of cycle (TP2) |

## Next

T126.3 — Phase 29 gate checklist + H4–H5 at 13 note + #222–#224 closeout notes.

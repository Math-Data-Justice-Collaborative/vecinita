# 01-requirements — Website scrape & crawl (S024 / EV-022)

**Date:** 2026-08-03  
**Features:** F59 (#69), F60 (#71), F61 (#70)  
**Mode:** delta / evolve  

## Phase 0C

Confirmed L1–L16 (S024-D27). Open Qs:

| Q | Choice | Decision |
|---|--------|----------|
| Hierarchy API | Nested JSON | S024-D28 / RD-243 |
| PDF | Best-effort + soft-fail | S024-D29 / RD-239 |
| ChatRAG meta | Backend path/parent only | S024-D30 / RD-244 |
| Test IDs | UJ-064–066, TC-196–207, AC-SC* | S024-D31 / RD-247 |

## Documents updated

| Doc | Delta |
|-----|--------|
| `docs/feature-list.md` | F59–F61 (Phase 1) |
| `docs/spec.md` | Ingest algorithm + tree; deferred PDF/OCR + ChatRAG UI |
| `docs/config-spec.md` | Scrape/crawl env knobs + validation |
| `docs/api-contract.md` | Crawl JobOptions; `/jobs/{id}/tree`; `/corpus/tree` |
| `docs/user-journeys.md` | UJ-064, UJ-065, UJ-066 |
| `docs/test-plan.md` | TC-196–207 + journey map |
| `docs/acceptance-criteria.md` | AC-SC1–SC12 |
| `docs/decisions.md` | RD-252–RD-263 |
| `docs/decisions/evolve-decisions.md` | D27–D31 |

## OpenAPI note

`openapi/data-management.yaml` mirror deferred to **04/07** (same pattern as prior cycles)
unless 02 requires contract file sync first.

## Next

**02-verify-plan** — consistency pass on F59–F61 deltas; Gate A→B.

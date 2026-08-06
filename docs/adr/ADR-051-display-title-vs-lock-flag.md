# ADR-051: `display_title` column vs title lock-flag

**Status:** Proposed (04-tech-plan EV-026 / S028) — promote to Accepted at M126 / Gate B→C  
**Date:** 2026-08-06  
**Related:** F74, RD-312, RD-320, RD-321; GitHub #224  
**Corpus:** [Corpus: feature-list.md §F74] [Corpus: adr]

## Context

Operators need a durable display name for corpus documents that survives scrape /
re-ingest, which always refreshes the scraped **`title`**. Two shapes were considered:

1. **Lock-flag** — keep a single `title` column; add `title_locked` (bool). When locked,
   scrape must skip overwriting `title`.
2. **Separate `display_title`** — nullable override column; scrape always writes raw
   `title`; citations and packing use `COALESCE(display_title, title)`.

Intake locked option 2 (S028-D10 / RD-312). This ADR records the architectural choice
and rejects the lock-flag alternative so 07-build does not re-litigate it.

## Decision

1. Add nullable **`documents.display_title`** (text).
2. Scrape / re-ingest **always** updates **`title`**; never clears or overwrites
   `display_title` unless an explicit operator action does.
3. ChatRAG `sources[].title`, admin list labels, and P3 packing use
   **`COALESCE(display_title, title)`** (RD-320).
4. Clearing override: PATCH `display_title: null` → UI falls back to scraped `title`
   (AC-SU10 / TC-251).
5. Single-doc API: **`PATCH /internal/v1/documents/{id}`** with `{ "display_title": ... }`;
   bulk metadata also accepts `display_title` (RD-313). Audit: `document.edited` with
   before/after including `display_title`.
6. **Out of this cycle (TP2 / RD-321 defer):** job/upsert ingest path does **not** copy
   `title` → `display_title`. Operator-set paths only (DocumentAdmin + PATCH/bulk).

## Consequences

- Migration is additive and compatible (nullable column; no rewrite of existing rows).
- Scrape logic stays simple — always write `title`; no lock branching in crawlers.
- Operators can rename without blocking future scrape title refresh for SEO/debug.
- Slightly more surface area: two title-like fields on DTOs / OpenAPI / admin forms.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| `title_locked` + single `title` | Couples scrape and operator intent; risk of stale locked titles forever; harder “reset to scraped” (must unlock + rescrape). |
| Overwrite `title` only via admin | Loses scraped title as SoT; breaks “rescrape refreshes raw title” (AC-SU9). |
| Separate display table | Overkill for one nullable string; F27 metadata already document-scoped. |

## References

- [Corpus: feature-list.md §F74]
- [Spec: docs/api-contract.md §PATCH /internal/v1/documents/{id}]
- [Corpus: decisions.md §RD-312–RD-321]
- S028-D10 / S028-D22 (TP2 defer ingest; TP4 ADR-051)

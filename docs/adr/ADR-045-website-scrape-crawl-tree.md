# ADR-045: Website scrape, crawl hierarchy, and soft-fail ingest

**Status**: Accepted  
**Date**: 2026-08-03  
**Session**: S024 / EV-022 (F59–F61)  
**Decisions**: S024-D35–D37; TP1–TP6; RD-261 lock; epic #185

## Context

Epic [#185](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/185) upgrades
URL ingest from minimal HTML parsing to: main-content extraction + politeness (#69 / F59),
same-site multi-page crawl (#71 / F60), and Admin corpus tree browse (#70 / F61). Product
locks (RD-252–263) require additive job options, nested JSON trees, soft per-page failure,
best-effort PDF text, and JS-render in v1 (`off`/`auto`/`always`).

Open questions for 04-tech-plan were: (1) how to render JS pages in Modal workers,
(2) which main-content library to add, (3) whether hierarchy + soft-fail deserve an ADR.

## Decision

1. **Hierarchy + soft-fail (product architecture)**  
   - Store **nested source fields** on documents (`source_domain`, `source_path`,
     `parent_url` as applicable).  
   - Expose **nested JSON** trees via `GET /internal/v1/corpus/tree` and
     `GET /jobs/{id}/tree` (domain → path → document → chunks).  
   - **Soft-fail** per page/PDF: record structured fetch errors; job may `completed` with
     partial success (`pages_failed`, failed tree nodes). No silent empty documents.

2. **JS-render runtime (F59)**  
   - Run **Playwright in the Modal data-management worker** when
     `VECINITA_SCRAPE_JS_RENDER` is `auto` or `always`.  
   - `off` = static fetch only; `auto` = escalate to Playwright when static extract is
     sparse/empty; `always` = always render.  
   - Not heuristic-only (no browser); not an external render service in EV-022.

3. **Extraction / PDF libraries (F59)**  
   - Main-content: prefer **`trafilatura`** (pin in `pyproject.toml` / Modal image in 07).  
   - PDF text: reuse existing **`pypdf`**; soft-fail when no extractable text
     (`VECINITA_SCRAPE_PDF_ENABLED`).

4. **Deploy path**  
   Path A: Modal DM workers + internal-write API + Admin FE. No new CORS origins (TP6).
   OpenAPI JobOptions + tree paths + `infra/vecinita.yaml` scrape/crawl keys land in
   Phase 26 (TP3).

## Consequences

- Modal DM image gains Playwright browser deps → larger image, higher cold start / cost.  
- New runtime dep `trafilatura` (+ transitive parsers); license audit in 07/08.  
- Crawl and tree UIs depend on nested metadata written at scrape/crawl time.  
- ChatRAG may read nested fields; **no ChatRAG tree UI** this cycle (S024-D17).

## Alternatives considered

| Option | Why not |
|--------|---------|
| Heuristic-only JS (`auto`≈retry static) | Rejects S024-D7 / JS-render in v1 |
| External render SaaS | New integration + ops; deferred |
| Skip ADR (tech notes only) | Rejected — hierarchy + soft-fail + browser-in-worker need durable ADR |
| `readability-lxml` only | Trafilatura preferred for main-content quality; may revisit if spike fails |
| Full OCR product | Out of scope (AC-SC12); PDF text only |

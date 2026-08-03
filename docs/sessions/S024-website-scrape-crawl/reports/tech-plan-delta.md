# 04-tech-plan delta — EV-022 / F59–F61 (locked)

> **Session:** S024 · **Cycle:** EV-022 · **Date:** 2026-08-03  
> **Status:** **locked** — TP1–TP6 + JS-render A + trafilatura (S024-D35)

## TP1–TP6 (approved)

| ID | Topic | Choice |
|----|-------|--------|
| **TP1** | Phase / milestones | **Phase 26**: M108 (F59) → M109 (F60) → M110 (F61) → M111 (e2e/OpenAPI/gate). Ship PRs `#69 → #71 → #70` from `evolve/EV-022-website-scrape-crawl` (stacked or sequential commits; one or more PRs) |
| **TP2** | ADR | **[ADR-045](../../../adr/ADR-045-website-scrape-crawl-tree.md)** — crawl/tree hierarchy + soft-fail scrape/PDF + Playwright-in-worker |
| **TP3** | Schema / OpenAPI / config | Nested source columns; OpenAPI JobOptions + tree paths; `infra/vecinita.yaml` scrape/crawl keys |
| **TP4** | Tests | Unit TC-196–201; API e2e UJ-064/065/066; Vitest JobForm+tree; Playwright **required** UJ-066; UJ-065 Playwright optional |
| **TP5** | Deploy / deps | Path A: Modal DM + write API + admin FE. Reuse **`pypdf`**; add **`trafilatura`**; Playwright in Modal worker image |
| **TP6** | Connectivity | Existing admin CORS; H4–H5 at 13; no new origins |

## Spike locks (S024-D21 / RD-261)

| Topic | Lock |
|-------|------|
| **JS-render** | **A — Playwright in Modal worker** (`auto`/`always`); not heuristic-only |
| **Extract** | **`trafilatura`** (preferred; confirm green in M108 spike task) |
| **PDF** | Reuse **`pypdf`**; best-effort soft-fail |

## Milestones

| M | Focus | Fn | Issue PR |
|---|-------|-----|----------|
| M108 | Main-content + politeness + PDF + JS-render path | F59 | #69 |
| M109 | Crawl BFS/scope/dedup + JobForm options + `/jobs/{id}/tree` | F60 | #71 |
| M110 | `/corpus/tree` + Admin tree UI + nested meta | F61 | #70 |
| M111 | OpenAPI mirror + UJ e2e suite + phase-gate docs | F59–F61 | epic #185 |

## Carry locks

| ID | Value |
|----|--------|
| Order | F59 → F60 → F61 (RD-253) |
| Defaults | max_depth **2**, max_pages **25**, RPS **0.5** |
| PDF | best-effort soft-fail (S024-D29) |
| Hierarchy | nested JSON trees (S024-D28) |
| ChatRAG UI | out (S024-D17) |

## Artifacts

| Artifact | Path |
|----------|------|
| ADR | `docs/adr/ADR-045-website-scrape-crawl-tree.md` |
| Execution plan | Phase 26 in `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Roadmap | `docs/sessions/S024-website-scrape-crawl/roadmap.md` |

## Next

Gate **B→C** AskQuestion → on PASS start **07-build** (05/06 skipped).

---
session_id: S024-website-scrape-crawl
type: feature
status: in_progress
branch: evolve/EV-022-website-scrape-crawl
started_at: 2026-08-03
intent: "Epic #185 — Website scrape & crawl pipeline: robust scrape (#69) → multi-page crawl (#71) → admin tree UI (#70); independently shippable PRs"
orchestrator: 16-evolve
evolve_cycle_id: EV-022
github_issues: [185, 69, 71, 70]
predecessor: S023-retrieval-topk-packing
predecessor_cycle: EV-020
context_briefs: []
standing_docs_touched:
  - docs/feature-list.md
  - docs/decisions/evolve-decisions.md
  - docs/spec.md
  - docs/config-spec.md
  - docs/user-journeys.md
  - docs/test-plan.md
  - docs/acceptance-criteria.md
  - docs/api-contract.md
  - docs/data-management-plan.md
---

# Session S024 — Website scrape & crawl pipeline

## Intent

Ship the **scrape → crawl → tree UI** sequence for multi-page website ingest
([epic #185](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/185)):

1. Robust main-content extraction + politeness ([#69](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/69))
2. Multi-page same-site crawl from a seed URL ([#71](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/71))
3. Tree display of ingest/crawl results in Data Management ([#70](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/70))

Children ship as **independently reviewable PRs** in order `#69 → #71 → #70`.

## Predecessor

| Item | Ref |
|------|-----|
| Session | [S023-retrieval-topk-packing](../S023-retrieval-topk-packing/session-brief.md) |
| Cycle | EV-020 — completed 2026-08-03 (F50/F51; Path A PASS) |
| Pipeline | Idle after S023 close; branch from `main` |

## Issues in scope

| Issue | Title | Role |
|-------|-------|------|
| [#185](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/185) | Website scrape & crawl pipeline (epic) | Parent |
| [#69](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/69) | Robust scraping / main-content extraction | Slice A (foundation) |
| [#71](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/71) | Multi-page website crawl | Slice B |
| [#70](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/70) | Tree display of ingest/crawl results | Slice C (admin UI) |

## Related (not children)

| Issue | Note |
|-------|------|
| [#94](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/94) | Corpus source curation (ops) — **out of cycle** |

## Scope discipline

**In (pending Phase 0 lock):**
- Improve `packages/ingest` scrape layer (boilerplate strip, redirects/charset, robots + rate limit, richer metadata)
- Crawl engine: seed URL → same-site pages with depth/page limits, dedup, link graph
- DM job form + API options for crawl config
- Admin tree view for crawl/ingest hierarchy + status
- Spec/test/e2e deltas; Modal DM worker wiring

**Out (unless Phase 0 expands):**
- #94 spreadsheet curation
- ChatRAG retrieval redesign
- Multimodal / heavy PDF pipeline (unless #69 optional non-HTML handling is scoped narrowly)
- Provider ABC / multi-scraper backends

## Decisions (session open — 2026-08-03)

| ID | Decision |
|----|----------|
| S024-D1 | Open `feature` session **S024-website-scrape-crawl** after S023/EV-020 close |
| S024-D2 | Routing = **Standard**; skip 03, 05, 06, 15 |
| S024-D3 | Ship order **#69 → #71 → #70**; independent PRs |
| S024-D4 | Evolve cycle **EV-022** |
| S024-D25 | Fn **F59** (#69), **F60** (#71), **F61** (#70) |
| S024-D34 | Gate A→B **PASS** |
| S024-D35 | TP1–TP6 + Playwright worker + trafilatura + ADR-045 |

## Routing plan

See [routing-plan.md](./routing-plan.md).

## Roadmap

See [roadmap.md](./roadmap.md) — Phase 26 M108–M111.

## Links

- Epic: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/185
- Standing: [feature-list.md](../../feature-list.md), [api-contract.md](../../api-contract.md), [spec.md](../../spec.md)
- ADR: [ADR-045](../../adr/ADR-045-website-scrape-crawl-tree.md)
- Tech plan: [reports/tech-plan-delta.md](./reports/tech-plan-delta.md)
- Current scrape: `packages/ingest/vecinita_ingest/scrape.py` (minimal HTMLParser extract)
- 01 seed: [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) (filled after Phase 0)

# Impact analysis — EV-022 / S024 (Phase 1)

**Date:** 2026-08-03  
**Features:** F59 (#69), F60 (#71), F61 (#70)  
**Epic:** [#185](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/185)

## Docs to update (01+)

| Doc | Why |
|-----|-----|
| `docs/spec.md` | Scrape robustness, crawl semantics, tree UX |
| `docs/config-spec.md` | max_depth/pages, rate limit, UA, PDF/JS flags |
| `docs/api-contract.md` | Additive job options; hierarchy endpoints |
| `openapi/data-management.yaml` | Mirror contract |
| `docs/user-journeys.md` | Admin crawl + tree browse |
| `docs/test-plan.md` | TC per Fn |
| `docs/acceptance-criteria.md` | AC per Fn |
| `docs/data-management-plan.md` | Crawl ops / politeness |
| `docs/dependency-inventory.md` | After 04 spike chooses libs |
| `docs/decisions.md` | RD block when 01 locks remaining Qs |

## Code surfaces (07)

| Slice | Primary paths |
|-------|----------------|
| F59 | `packages/ingest`, DM pipeline, Modal DM app |
| F60 | ingest crawl module, JobForm, job options OpenAPI |
| F61 | Corpus tree FE, hierarchy API, chat-rag-backend meta only |

## Risks / spikes

| Item | When |
|------|------|
| JS-render runtime (Playwright vs heuristics) | **04-tech-plan** (S024-D21) |
| ChatRAG nesting UI licensing | Research note only (S024-D17) |
| PDF text quality on real corpuses | Fixture + sample in 09/10 |

## Routing (unchanged)

Standard: `01 → 02 → 04 → 07 → 08 → 09 → 10 → 11 → 12 → 13` (skip 03/05/06/15).

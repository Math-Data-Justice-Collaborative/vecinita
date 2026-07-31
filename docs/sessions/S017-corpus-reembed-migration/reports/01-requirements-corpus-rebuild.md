# 01-requirements — F41 corpus rebuild + document store (EV-015 / #167)

**Session:** S017-corpus-reembed-migration  
**Cycle:** EV-015  
**Date:** 2026-07-30  
**Status:** complete (delta specs written)

## Scope (locked)

| ID | Decision |
|----|----------|
| S017-D3 | Implement rebuild (expand #167 beyond investigation) |
| S017-D4→D9 | Modes: `reembed` \| `rechunk` \| `rescrape` (all three in API); **ops this cycle** prefer store-backed reembed/rechunk — **no live scrape** unless explicit rescrape |
| S017-D5 | Admin Jobs UI + Modal job + `force` |
| S017-D6 | Staging + F36; prod = runbook only |
| S017-D10 | `job_type=rebuild` + `mode` enum |
| S017-D11 | Dry-run = **shadow dual-write** + promote |
| S017-D12 | Scope = whole corpus default + optional `document_ids` |
| S017-D13 | Version stamps + track across revisions; dim dual-write deferred to #159 |
| S017-D14 | Retag stays separate job |
| S017-D15 | Progress = Jobs SSE + `/jobs/:id` only |
| S017-D16 | Postgres document store (`body_text` + `document_revisions`) |
| S017-D17 | Document store folded into **F41** (not F42) |

## Artifacts

| Doc | Delta |
|-----|-------|
| feature-list.md | F41 expanded |
| user-journeys.md | UJ-053, UJ-054 |
| test-plan.md | TC-161–TC-168 |
| acceptance-criteria.md | AC-RB1–AC-RB10 |
| api-contract.md | rebuild job + store fields |
| spec.md | short F41 delta |
| config-spec.md | rebuild / shadow knobs |
| ADR-040 | document store + rebuild + version stamps |
| decisions.md | RD-188–RD-196 |
| evolve-decisions.md | Cycle EV-015 intake |
| runbook outline | `reports/runbook-corpus-rebuild-outline.md` |

## Dependency map (#159–#166)

| Issue | Can ship without F41 rebuild? | Must wait / uses F41 |
|-------|-------------------------------|----------------------|
| #159 multilingual embeddings | Design/spike OK | **Prod model swap needs F41** + dim checklist (ADR-008 successor) |
| #160 chunk overlap / sizing | Design OK | **Needs rechunk mode + store** |
| #163 hash-skip | Can ship skip logic | Must expose **`force`** for rebuild |
| #164 chunk-level tags | Can ship on ingest | Rebuild does **not** retag; use separate retag |
| #166 embed batch retries | Can ship independently | Rebuild jobs **stress** this path — nice-to-have before large staging runs |

## Out of scope (this cycle)

- Live production re-embed
- Choosing multilingual model (#159)
- Chunk overlap parameter values (#160)
- Dual-write dim migration implementation (#159)
- New progress widget beyond Jobs

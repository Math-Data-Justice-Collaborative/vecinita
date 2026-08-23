# 01-requirements report — S030 / EV-027

**Status:** complete (pending user gate → 02-verify-plan)  
**Session:** S030-corpus-automations  
**Cycle:** EV-027 · **F75, F76, F77** · Issues #73, #219, #72  
**Mode:** delta  
**Date:** 2026-08-07

## Summary

Locked seeds S1–S9 confirmed (S030-D15). Open questions OQ1–OQ8 resolved (S030-D16–D23).
Delta specs + ADRs written; RD-325–344 recorded.

## Decisions

| Band | IDs |
|------|-----|
| Locked seeds → RD | RD-325–333 |
| OQs → RD | RD-334–341 |
| Docs/ADR map | RD-342–344 |
| Session | S030-D15–D23 |

**Notable:** F77 promote gate is **human operator judgment** (S030-D20 / RD-338), not an
automated metric threshold — eval evidence still required for the operator to judge
“better than base” (S030-D10 / RD-331).

## Artifacts written

| Doc | Delta |
|-----|--------|
| `docs/feature-list.md` | F75–F77 refined |
| `docs/user-journeys.md` | UJ-080–082 |
| `docs/test-plan.md` | TC-252–263 |
| `docs/acceptance-criteria.md` | AC-AU*, AC-FR*, AC-FT* |
| `docs/api-contract.md` | EV-027 section |
| `docs/config-spec.md` | automation/freshness/FT env |
| `docs/spec.md` | F75–F77 components |
| `docs/decisions.md` | RD-325–344 |
| `docs/adr/ADR-052-*.md` | Automation orchestration (Proposed) |
| `docs/adr/ADR-053-*.md` | Modal LoRA FT (Proposed) |
| `docs/adr/README.md` | index rows |

## Next

**02-verify-plan** — Gate A→B.

[Corpus: product] [Corpus: journeys] [Corpus: tests] [Corpus: acceptance] [Corpus: api]
[Corpus: adr]

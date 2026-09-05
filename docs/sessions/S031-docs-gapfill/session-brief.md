---
session_id: S031-docs-gapfill
type: feature
status: in_progress
branch: feat/S031-docs-gapfill
started_at: 2026-08-18
intent: "Brownfield standard-scale docs/corpus gap-fill for existing Vecinita work not fully on the pack; inventory then gap-fill; after documenting verify + HANDOFF gate, implement backlog spawned by gap-fill. Not evolve."
orchestrator: brownfield
evolve_cycle_id: null
scale: standard
angles: all_v1_documenting_packs
documenting_to_implementing_gate: closed
context_briefs: []
standing_docs_touched: []
---

# Session S031 — docs gap-fill

## Intent

Brownfield **standard-scale** docs/corpus gap-fill for existing Vecinita work that is not fully on the pack: full inventory, then gap-fill standing docs. After documenting verify + HANDOFF gate, implement any backlog spawned by gap-fill.

**Not evolve.** Prior S030/EV-027 treated as closed; PR #238 left as-is; optional S030-D65 not in scope.

## Scope

**In**

- Inventory existing standing docs / corpus vs pack expectations
- Gap-fill only (do not regenerate the whole doc tree)
- Documenting band → verify documenting → HANDOFF → gate
- After gate open|waived: implementing/build + implementing twins for gap-fill backlog

**Out**

- Evolve cycle / new Fn allocation as the entry path
- Staging/prod mutations (local only)
- Merging or changing PR #238 as part of this open
- Answering optional S030-D65

## Constraints

- Local only — no staging/prod mutations

## Routing plan

See [routing-plan.md](./routing-plan.md).

## Links

- Orchestrator: [Corpus: orchestrators] brownfield intake 2026-08-18
- Prior closed: S030/EV-027 (S030-D64)
- Standing: [CORPUS.md](../../CORPUS.md), [feature-list.md](../../feature-list.md)

## Next

**documenting/context** — inventory docs/code; do not implement product code yet.

# S031 documenting/context inventory

**Session:** S031-docs-gapfill  
**Orchestrator:** brownfield (standard)  
**Date:** 2026-08-18  
**Base branch tip:** `evolve/EV-027-corpus-automations` @ `588dab6` (PR #238 open)

[Corpus: docs/CORPUS.md] [Corpus: feature-list.md §F75–F77]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]

## Summary

Standing CORPUS paths all exist. F75–F77 are specified in product, API, journeys, tests,
ADRs, and acceptance. Primary debt is **staleness** (status / operator docs / diagrams /
antibody leftover rules), not missing feature definitions.

S030 closed with cutover deferred (`close_cycle_defer_cutover`, S030-D64). Live enable and
FT promote remain AskQuestion-gated.

## Approved this turn (S031-D1)

| Item | Action |
|------|--------|
| feature-list F75–F77 status | Update to in-tree implemented; live cutover deferred |
| plan-adherence + constraint-enforcement + template-conformance | Rewrite away from antibody F1–F9 / Job template to ChatRAG `feature-list.md` |

## Deferred gap-fills (not selected)

staging-runbook EV-027 section · architecture finetune_app row · data-management-plan schema ·
data-flow Mermaid · deploy-checklist EV-027 · CHANGELOG Unreleased · spec.md six-app polish ·
CORPUS satellites · eval-golden F77 note · community-maps mock waiver

## Orphans / contradictions noted

- Untracked `apps/chat-rag-frontend/mockups/community-maps-alerts.html` — no Fn (do not invent)
- Antibody always-apply rules contradicted ChatRAG feature-list (rewrite approved)
- `main` lacks EV-027; S031 branch rebased onto EV-027 tip per S031-D2

## Next

documenting/draft-docs for approved items → requirements/feasibility light pass → verify documenting.

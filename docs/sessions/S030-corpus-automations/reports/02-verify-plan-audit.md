# 02-verify-plan audit — EV-027 / F75–F77

> **Session:** S030 · **Cycle:** EV-027 · **Date:** 2026-08-07  
> **Mode:** evolve delta · **Status:** ready for Gate A→B (S030-D25 fixes applied)  
> **Citations:** [Corpus: feature-list.md §F75–F77] [Corpus: journeys] [Corpus: tests]
> [Corpus: acceptance] [Corpus: api] [Corpus: adr] [Spec: docs/decisions.md §RD-325–348]
> [Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
> [Spec: docs/adr/ADR-053-modal-lora-finetune.md]

## Inventory (delta)

| # | Document | Sections | Status |
|---|----------|----------|--------|
| 1 | feature-list.md | Summary F75–F77; detail §F75–F77; P3 note | audited + M1/C2 title |
| 2 | spec.md | Corpus automations + FT components | audited |
| 3 | user-journeys.md | UJ-080–082 | audited + TC cites |
| 4 | test-plan.md | Journey map + TC-252–265 | audited + TC-264/265 |
| 5 | acceptance-criteria.md | AC-AU*/FR*/FT* | audited + AC-FT9 |
| 6 | api-contract.md | EV-027 routes | audited |
| 7 | config-spec.md | automation/freshness/FT env | audited + M4 note |
| 8 | ADR-052 / ADR-053 | Proposed decisions | audited |
| 9 | decisions.md RD-325–348 | reference + product verdicts | audited |
| 10 | evolve-decisions.md §EV-027 | intake scope wording | **C1/C2 fixed** |

## Consistency

| Check | Result |
|-------|--------|
| Feature ↔ Spec | **Pass** |
| Feature ↔ Journey | **Pass** (UJ-080–082) |
| Journey ↔ Test | **Pass** (TC-252–265) |
| Feature ↔ Test | **Pass** (TC-264 covers AC-AU4) |
| Spec ↔ Config | **Pass** (30d / flags; FT cap → 04) |
| Test ↔ Acceptance | **Pass** (AC-FT9 + TC-265) |
| RD ↔ Spec | **Pass** |
| Scope boundaries | **Pass** after C1 |
| Naming | **Pass** after M1 (`document_id`+`revision`) |
| Connectivity | **Pass** — API e2e + Vitest; Playwright `opt` when UI ships |
| “Eval-gated” title vs human promote | **Pass** after C2 |

## Verdicts

### Auto-approved (high confidence) — 18

H1–H18 from RD-325–342 / S030-D15–D23 (see mid-stage draft).

### Medium / low — user-approved (S030-D25: option 1)

| ID | Statement | Verdict | Action |
|----|-----------|---------|--------|
| C1 | evolve-decisions F75 “ingest→embed→index” vs RD-334 | **Approved (fix)** | Catch-up-only wording; RD-345 |
| C2 | “eval-gated” / “eval better” vs RD-338 | **Approved (fix)** | Human judgment + eval evidence; RD-346; titles clarified |
| M1 | `doc_id` vs `document_id` | **Approved (fix)** | Normalize to `document_id`+`revision` |
| M2 | AC-AU4 lacked dedicated TC | **Approved (fix)** | TC-264; RD-347 |
| M3 | UJ-082 rollback lacked AC/TC | **Approved (fix)** | AC-FT9 + TC-265; RD-347 |
| M4 | FT cost-cap env thin | **Approved (fix)** | Shared kill-switch now; 04 names `VECINITA_FINETUNE_MAX_*`; RD-348 |

## Source updates

| File | Change |
|------|--------|
| `docs/decisions/evolve-decisions.md` | F75/F77 scope + S030-D10 clarify |
| `docs/feature-list.md` | `document_id`; TC-264/265; F77 title; eval-gated note |
| `docs/acceptance-criteria.md` | AC-AU4→TC-264; AC-FT9; AC-FT7 M4 note |
| `docs/test-plan.md` | TC-264, TC-265; journey map |
| `docs/user-journeys.md` | Acceptance TC/AC cites |
| `docs/config-spec.md` | Kill-switch M4 note; adapter rollback; last updated |
| `docs/decisions.md` | EV027 product verdicts; RD-345–348 |
| Session card / routing / seed / impact | C2 wording aligned |

## Gate A→B

**Ready** — AskQuestion pending (S030-D25 applied; phase_a still pending until user approve).

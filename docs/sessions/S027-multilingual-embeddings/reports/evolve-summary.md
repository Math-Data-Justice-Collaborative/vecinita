# Evolve summary — EV-025 / S027

> **Cycle:** EV-025 — Multilingual embeddings (#159)  
> **Features:** F70, F71  
> **Status:** **completed** (S027-D63)  
> **Live tip:** `4b7231b`  
> **Closed:** 2026-08-05

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]  
[Spec: docs/decisions/evolve-decisions.md §S027-D63]

## Outcome

| Fn | Result |
|----|--------|
| **F70** | E1 pin `intfloat/multilingual-e5-small` @ 384-d; Modal ST runtime (+ FastEmbed→ST fallback #221) |
| **F71** | Staging shadow→F36→promote; **staging-as-live** = prod cutover (S027-D61); E0 restorable via runbook |

## Deploy evidence

| Item | Value |
|------|--------|
| Hotfix | PR [#221](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/221) @ `4b7231b` |
| Promote | `094e957e-41b2-40e4-891a-29743c29baa6` · 385 chunks / 47 docs |
| F36 | `c3a6d484-…` · retrieval/faith ~0.94 |
| H3 sources | EN=8 · ES=3 |
| H4–H5 / 15-health | PASS |

## Notable decisions

S027-D11 operator promote · D12 ST fallback · D21 staging-first · D34 CI split · D35 compose waive · D59 staging promote · D61 staging-as-live · D62 15-before-close · **D63 cycle closed**

## Follow-ons

- **17-retrospective** — queued (prod bugs + flaky security install; S027-D41+)

# Deploy Smoke — S027 / EV-025 (F70–F71) — CLOSED (staging-as-live)

> **Date**: 2026-08-05  
> **Status**: **PASS** (conditional — staging-as-live = F71 prod cutover; S027-D61)  
> **Decisions**: S027-D50–D61  
> **Commit (CD)**: `4b7231b` (PR #221 merge)  

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/deployment-integration.md §EV-025]  
[Spec: docs/staging-runbook.md §EV-025]  
[Spec: docs/decisions/evolve-decisions.md §S027-D61]

## Pre-Deploy / CD @ `4b7231b`

| Item | Status |
|------|--------|
| PR #221 MERGED | **success** @ `4b7231b` |
| CI / preflight / Modal / DO | **success** (runs recorded prior) |
| Modal embed | ST + E1 pin @ 384-d |

## F71 cutover

| Step | Result |
|------|--------|
| Staging shadow → F36 | **completed** (`094e957e-…` / `c3a6d484-…`) |
| Operator promote (S027-D59) | **385** chunks / **47** docs · E1 pin · status `promoted` |
| Live corpus | 387 chunks · 385 embeddings @ **384-d** |
| Prod stack | **None separate** — DO apps/DB are staging-named live surface |
| Prod resolution (S027-D61) | **staging-as-live complete** — no second promote |

## Smoke tiers (post-promote)

| Tier | Status | Notes |
|------|--------|-------|
| H0c | **PASS** | `verify_connectivity.sh` |
| H1 | **PASS** | deps postgres/modal_embed/modal_llm `ok` |
| H2 | **PASS** | staging DB |
| H3 EN | **PASS** | **sources=8** |
| H3 ES | **PASS** | **sources=3** |
| H4 | **PASS** | live connectivity |
| H5 | **PASS** | FE bundle hosts |

## Gate

| Gate | Status |
|------|--------|
| 13-deploy-smoke | **completed** PASS (cond. S027-D61) |
| Phase D / deploy | **passed** |

## Next

AskQuestion: close EV-025 · 15-service-health · 14-hotfix · 17-retrospective (queued).

# Evolve summary — EV-027 / S030

> **Cycle:** EV-027 — Corpus automations (#73) + LoRA FT (#72) + freshness (#219)  
> **Features:** F75, F76, F77  
> **Status:** **completed** — baseline + health only; **cutover deferred** (S030-D64)  
> **Branch tip (local):** `7861b47` (+3 unpushed docs vs origin `588dab6`)  
> **Closed:** 2026-08-13

[Corpus: feature-list.md §F75–F77]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]

## Outcome

| Fn | Built / verified | Live |
|----|------------------|------|
| **F75** catch-up automations | Spec + Phase 30 impl + T0 e2e/UI | **not cut over**; flags **off** |
| **F76** freshness (30d stale) | Spec + impl + T0 | **not cut over**; flags **off** |
| **F77** LoRA FT + human promote | Spec + Modal FT app + T0 | **not cut over**; promote gated |

## Deploy / health evidence

| Item | Value |
|------|--------|
| `env_role` | `staging_as_live` = live/prod |
| 12-verify-deploy | **ready** flags-off — `reports/deploy-checklist.md` |
| 13-deploy-smoke | **PASS** `passed_baseline_only` — `reports/deploy-smoke.md` |
| 15-service-health | **OVERALL PASS** — `reports/service-health.md` |
| Tip CI (smoke) | PASS @ `588dab6` [run 31709704821](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31709704821) |
| H0ci `main` | PASS (advisory) @ `8ae9d17` [run 31178547214](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31178547214) |
| PR | [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) **OPEN** (unmerged) |
| Live alembic | `20260806_0014` (tip head `20260812_0016` — advisory) |

## Notable decisions

| ID | Choice |
|----|--------|
| S030-D60 | Baseline live smoke only; no cutover/enable |
| S030-D61 | Accept H2 alembic tip-drift |
| S030-D62 | Run 15-service-health |
| S030-D63 | Recommended post-baseline health package |
| S030-D64 | **Close cycle; defer cutover/enable/FT promote** |

## Follow-ons (later session)

1. Push tip docs commits (`fee4d12`…`7861b47`) optional  
2. Merge/ship PR #238 + migrate live DB + CD (flags still off)  
3. AskQuestion before `*_ENABLED` / FT promote on live  
4. Optional 17-retrospective

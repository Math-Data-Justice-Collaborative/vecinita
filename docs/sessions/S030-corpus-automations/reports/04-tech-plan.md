# 04-tech-plan report — S030 / EV-027

**Status:** completed  
**Session:** S030-corpus-automations  
**Cycle:** EV-027 · **F75, F76, F77** · Issues #73, #219, #72  
**Mode:** delta  
**Date:** 2026-08-07  
**Decisions:** S030-D28 (start 04), S030-D29 (TP1–TP10 lock)

## Summary

Technical plan locked for corpus automations + freshness + LoRA FT. Appended
**Phase 30** (M127–M130) to the execution plan; ADR-052/053 **Accepted** with path
and cap locks; session roadmap + tech-plan-delta written. No product code.

## TP1–TP10

| ID | Lock |
|----|------|
| TP1 | Phase 30: M127→M128→M129→M130 |
| TP2 | One `schedule=modal.Period(days=1)` on `vecinita-data-management` |
| TP3 | Table `automation_runs` |
| TP4 | `infra/modal/finetune_app.py` / `vecinita-llm-finetune` / `llm-finetune-adapters` |
| TP5 | `VECINITA_FINETUNE_MAX_CONCURRENT=1`, `MAX_RUNS_PER_DAY=3` |
| TP6 | `POST /jobs/{id}/approve` |
| TP7 | `refresh_enabled`, `last_checked_at` |
| TP8 | Unit + API e2e + Vitest + Playwright T0-ui (UJ-080–082) |
| TP9 | Staging first; AskQuestion before prod |
| TP10 | 06 required for PEFT/TRL |

## Artifacts

| Artifact | Path |
|----------|------|
| Tech-plan delta | `docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md` |
| Execution plan | Phase 30 in `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Roadmap | `docs/sessions/S030-corpus-automations/roadmap.md` |
| ADR-052 / ADR-053 | Accepted |
| Config / API / inventory / secrets matrix | Back-added |
| Decisions | TP-S030-01–10; evolve S030-D28/D29 |

## Task counts (Phase 30)

| Milestone | Tasks (approx.) |
|-----------|-----------------|
| M127 F75 | T127.1–T127.10 (10) |
| M128 F76 | T128.1–T128.7 (7) |
| M129 F77 | T129.1–T129.10 (10) |
| M130 gate | T130.1–T130.4 (4) |
| **Total** | **31** pending |

## Next

**05-verify-tech** → Gate B→C → **06-tech-tooling** → **07-build**.

```
Enter this into the chat to continue:
@.cursor/skills/05-verify-tech/SKILL.md
```

[Corpus: feature-list.md §F75–F77] [Spec: docs/adr/ADR-052] [Spec: docs/adr/ADR-053]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md]

# Evolve report — EV-027

**Title:** Corpus automations + freshness + LoRA FT (F75–F77)  
**Session:** S030-corpus-automations  
**Features:** F75, F76, F77  
**Status:** completed — **baseline health close**; live cutover **deferred** (S030-D64)  
**PR:** [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open  
**Issues:** #73 · #72 · #219  
**Closed:** 2026-08-13

## Summary

Implemented catch-up automations (F75), corpus freshness with 30-day stale default (F76), and LoRA/PEFT fine-tune with manual approve + human promote (F77) through Spec→Build (Phase 30 M127–M130) and Phase D verify. Live sole stack (`staging_as_live`) passed **baseline** deploy-smoke and service-health with flags **off**. EV-027 code is **not** on live; alembic tip-drift and enable/promote remain deferred to a future ship AskQuestion.

## Gates

| Gate | Result |
|------|--------|
| A→B | passed |
| B→C | passed |
| C→D | passed |
| Spec→Build | opened (build completed) |
| Deploy | **`passed_baseline_only`** (no EV-027 cutover) |
| 15-service-health | **OVERALL PASS** |

## Follow-ups

- Ship-path: merge #238 → migrate → CD with `*_ENABLED=false`  
- Separate AskQuestion for live automation enable / FT promote  
- Optional push of closeout docs tip (`7861b47`)  
- Optional 17-retrospective

See: `docs/sessions/S030-corpus-automations/reports/evolve-summary.md`.

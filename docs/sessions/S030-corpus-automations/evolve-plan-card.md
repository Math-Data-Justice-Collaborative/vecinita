# Evolve Plan Card

> Cycle: EV-027 | Session: S030-corpus-automations | Updated: 2026-08-12

## Goal

Ship corpus change automations (#73), Modal LoRA fine-tune (#72) with human promote after
eval evidence (no auto-abort), and corpus freshness (#219) in one Full-preset cycle.

## Features

| Fn | Issue | Title | Corpus |
|----|-------|-------|--------|
| **F75** | #73 | Corpus change automations | [Corpus: product] |
| **F76** | #219 | Corpus freshness automation | [Corpus: product] |
| **F77** | #72 | Modal LoRA fine-tune + human promote (eval evidence) | [Corpus: product] |

## In / out of scope

- In: S030-D2–D13 (see evolve-decisions §EV-027); TP1–TP10 (S030-D29)
- Out: #192 dashboard widgets; blind FT promote; prod corpus mutation without AskQuestion

## Preset + routing

- Preset: **Full** (S030-D9)
- Stages: 00 → 16 → 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13

## Next child stage

**07-build** — Phase 30 M128 (F76) T128.3 in progress; T128.2 done @7b1aa87; M127 PR #238 open (no merge); FT pins ready for M129

## Risks / open decisions

- AskQuestion before live prod automation enable / FT promote (TP9)
- Wire `FINETUNE_IMAGE_PIPS` in `finetune_app.py` at M129 (S030-D33)


## Corpus cites

[Corpus: product] [Corpus: system-spec] [Corpus: deploy-integration] [Corpus: data]
[Corpus: journeys] [Corpus: api] [Corpus: acceptance] [Corpus: tests] [Corpus: adr]
[Spec: docs/adr/ADR-052] [Spec: docs/adr/ADR-053]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md]

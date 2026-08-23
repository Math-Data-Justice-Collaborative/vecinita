# Evolve Plan Card

> Cycle: EV-027 | Session: S030-corpus-automations | Updated: 2026-08-13  
> **Status:** completed — `close_cycle_defer_cutover` (S030-D64)

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

## Phase split

- Active phase: **closed** (Build + baseline verify/health done)
- Spec→Build gate: **open** (historical)
- Live cutover / enable / FT promote: **deferred**

## Spec-development band (00–06)

Completed (Full preset).

## Build band (07–15)

| Stage | Status |
|-------|--------|
| 07–11 | completed |
| 12 | completed (ready flags-off) |
| 13 | completed (`passed_baseline_only`) |
| 15 | completed (OVERALL PASS) |

## Next child stage

**None** — cycle closed. Resume ship-path via new `00-context` session.

## Risks / open decisions

- AskQuestion before live prod automation enable / FT promote (TP9)
- PR #238 still open; tip docs commits may be unpushed

## Corpus cites

[Corpus: product] [Corpus: feature-list.md §F75–F77] [Corpus: deploy-integration]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]

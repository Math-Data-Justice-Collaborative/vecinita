# Session roadmap — S028 / EV-026

> **Session:** S028-chat-source-ux  
> **Evolve cycle:** EV-026  
> **Features:** F72–F74  
> **Branch:** `feat/S028-chat-source-ux` → planned `evolve/EV-026-chat-source-ux` at 07  
> **Last updated:** 2026-08-06  
> **Sources:** [session-brief](./session-brief.md) · [routing-plan](./routing-plan.md) ·
> [execution-plan](../S000-internal-docs-archive/execution-plan.md) Phase 29 ·
> [tech-plan-delta](./reports/tech-plan-delta.md) ·
> [ADR-051](../../adr/ADR-051-display-title-vs-lock-flag.md)

## Purpose

Ship chat source UX: citation URL validation (F72/#222), relevance-gated sources without
fixed pad (F73/#223), and operator `display_title` (F74/#224).

## Current state

| Track | Status | Notes |
|-------|--------|-------|
| 00-context | ✅ Complete | Feature preset; prod-careful |
| 01-requirements | ✅ Complete | RD-309–321 |
| 02-verify-plan | ✅ Complete | Gate A→B PASS (S028-D20) |
| 04-tech-plan | 🔄 In progress | TP1–TP4 locked (S028-D22); plan review |
| 05-verify-tech | ⬜ Pending | |
| 07–11 | ⬜ Pending | |
| 12–13 | ⬜ Pending | **AskQuestion before prod** (S028-D2) |

## Milestone build order

```mermaid
flowchart LR
  M123[M123 F72 URL helper] --> M124[M124 F73 filter]
  M124 --> M125[M125 F74 display_title]
  M125 --> M126[M126 gate]
```

## GitHub issue dependency graph

```mermaid
flowchart TD
  I222["#222 citation URLs"] --> M123
  I223["#223 relevance sources"] --> M124
  I224["#224 display_title"] --> M125
  M123 --> M124
  M124 --> M125
  M125 --> M126
```

## Session pipeline stages

```mermaid
flowchart LR
  s00[00] --> s01[01] --> s02[02] --> s04[04] --> s05[05] --> s07[07]
  s07 --> s08[08] --> s09[09] --> s10[10] --> s11[11] --> s12[12] --> s13[13]
```

## Critical path (remaining)

```mermaid
flowchart LR
  tp[04 plan approve] --> v05[05-verify-tech]
  v05 --> b07[07 M123-M126]
  b07 --> v08[08-verify-build]
  v08 --> d09[09-qa]
  d09 --> e10[10-e2e]
  e10 --> v11[11-verify-impl]
  v11 --> d12[12 AskQ]
  d12 --> s13[13 AskQ smoke]
```

## Phase gate checklist (exit)

- [ ] T123.1–T126.3 completed
- [ ] AC-SU1–SU10 mapped; TC-242–251 green at verify
- [ ] ADR-051 Accepted
- [ ] OpenAPI + CORS H0c for `PATCH /documents/{id}`
- [ ] No new deps (06 skipped); Playwright optional only
- [ ] Live prod smoke only after AskQuestion (S028-D2)

## PR plan

| Order | Milestone | PR slot | Status |
|-------|-----------|---------|--------|
| 1 | M123 F72 | PR-72 | pending |
| 2 | M124 F73 | PR-73 | pending |
| 3 | M125 F74 | PR-74 | completed |
| 4 | M126 gate | PR-75 | pending |
| 5 | Phase 29 major | PR-76 | pending — after Gate C→D / verify |

## Issue closeout

Close #222 / #223 / #224 after **11-verify-impl** (and 13 only if deploy approved). Do not
close on M126 alone if live smoke is still open.

## Issue creation (optional — do not run without approval)

```bash
# Epics already #222 #223 #224 — child issues only if operator wants split
```

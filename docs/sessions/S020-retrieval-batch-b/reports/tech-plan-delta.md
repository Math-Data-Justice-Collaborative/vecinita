# 04-tech-plan delta — EV-017 / F43–F45

> **Session:** S020 · **Cycle:** EV-017 · **Date:** 2026-08-02  
> **Status:** completed — Gate B→C passed (S020-D18)

## Approvals

| Choice | Result |
|--------|--------|
| TP1–TP7 (milestones, ADR, embed reuse, CE pattern, order, deps, skip topology) | **Approved** (user option 1) |
| Phase 22 M94–M98 | Drafted — pending Gate B→C |
| ADR-042 | Written — pending Gate B→C accept with plan |
| Dependency / data-mgmt / deploy topology | Skipped (TP7); Path A + CE spike runbook only |

## Artifacts

| Artifact | Path |
|----------|------|
| Execution plan Phase 22 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| ADR-042 | `docs/adr/ADR-042-in-process-h1-answer-cache.md` |
| Session roadmap | `docs/sessions/S020-retrieval-batch-b/roadmap.md` |

## Milestones

| M | Focus | Fn |
|---|-------|-----|
| M94 | `packages/rag` H1 cascade (TC-176–178) | F43 |
| M95 | ChatRAG + OpenAPI `cache_hit` + F36 harness (TC-179) | F43 |
| M96 | Soft language L1 + empty-hit fixture (TC-180–181) | F44 |
| M97 | CE Modal T4 spike + mockable client (TC-182–183) | F45 |
| M98 | E2E UJ-057–060 + CE ship-gate docs (TC-184 staging) | F43–F45 |

## Locked defaults (carry)

| ID | Value |
|----|--------|
| M1 | Semantic threshold **0.92** |
| M2 | TTL **3600s**, max_entries **1024** |
| M3 | CE ephemeral Modal T4; ChatRAG ≠ playground |
| M4 | OpenAPI `cache_hit` in **07-build** (T95.4) |

## Next

Phase B checkpoint → gate B→C → `07-build` (05/06 skipped).

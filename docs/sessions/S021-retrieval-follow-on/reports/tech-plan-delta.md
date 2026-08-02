# 04-tech-plan delta — EV-018 / F46 + F45 re-gate

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Status:** completed — TP1–TP6 approved; awaiting Gate B→C

## Approvals

| Choice | Result |
|--------|--------|
| TP1–TP6 (phase/milestones, ADR, diagnose order, tests, deploy/deps, connectivity) | **Approved** (user option 1) |
| Phase 23 M99–M100 | Drafted into execution-plan |
| New ADR | None (reuse ADR-041/042 + existing CE spike) |
| Dependency / data-mgmt / deploy topology | Skipped (TP5); Path A + Path B escalate only |

## Artifacts

| Artifact | Path |
|----------|------|
| Execution plan Phase 23 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| Session roadmap | `docs/sessions/S021-retrieval-follow-on/roadmap.md` |
| This report | `docs/sessions/S021-retrieval-follow-on/reports/tech-plan-delta.md` |

## Milestones

| M | Focus | Fn |
|---|-------|-----|
| M99 | Diagnose empty pools + minimal fix + UJ-061 e2e (TC-185/186) | F46 |
| M100 | CE re-gate after F46 + ship-gate docs (TC-184 / AC-BB9) | F45 |

## Locked defaults (carry)

| ID | Value |
|----|--------|
| Diagnose order (TP3) | pin → fixture URLs → `min_retrieval_score`/filters → code/BUG |
| CE model | `BAAI/bge-reranker-v2-m3` Modal T4 |
| Floors | relevancy ≥ **0.28**, faith ≥ **0.91** |
| Prod CE | **false** until AC-BB9 + deploy approval |
| Order | F46 (M99) before F45 re-gate (M100) |

## Next

Gate B→C AskQuestion → on pass: `07-build` (05/06 skipped) starting at T99.1.

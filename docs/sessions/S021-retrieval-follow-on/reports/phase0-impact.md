# EV-018 Phase 0 — impact analysis (draft → approve)

> **Status:** `phase0_approved` (S021-D9–D12) · 01 complete · **Session:** S021  
> **Date:** 2026-08-02

## Feature allocation

| Fn | Title | Status | Issues / criteria |
|----|-------|--------|-------------------|
| **F46** | Staging retrieve reliability (non-empty pools) | Planned | Staging `pool=0` / empty `sources` |
| **F45** | CE spike + gated ship (re-gate) | Planned (extend) | #83 / #161; AC-BB9 / UJ-060 / TC-184 |

## Intake lock

| ID | Decision |
|----|----------|
| S021-D8 | Allocate **F46** + extend **F45** |
| S021-D9 | **F46 → F45** ordering (two milestones, one cycle) |
| S021-D10 | Evolve Fn work (not default hotfix) |
| S021-D11 | Deploy **Path A** default; Path B if corpus rebuild |
| S021-D12 | Proceed → EV-018 + 01-requirements after confirm |

## Docs to update (Phase A — 01)

| Doc | Delta |
|-----|-------|
| `feature-list.md` | **Done (Phase 0)** — F46 row + F45 EV-018 extension |
| `spec.md` | Retrieve reliability / staging pin notes if behavior changes |
| `config-spec.md` | Only if `min_score` / retrieve knobs change |
| `api-contract.md` | Only if new diagnostics endpoints |
| `user-journeys.md` | UJ-060 re-gate; optional retrieve-health journey |
| `test-plan.md` / `acceptance-criteria.md` | AC/TC for non-empty retrieve + CE re-gate |
| `decisions/evolve-decisions.md` | **Done (stub)** — §Cycle EV-018 |
| `bug-reports/` + `tests/bugs/` | If root cause classified as tracked bug |

## Code / ops surfaces (Phase C — provisional)

| Area | F46 | F45 re-gate |
|------|-----|-------------|
| `packages/rag` / chat-rag retrieve | Fix or knobs | Reuse CE path |
| Corpus / embed pin / F41 | Rebuild if drift | — |
| Spike scripts / Modal T4 | — | Re-run ship gate |
| tests / e2e | Non-empty pool asserts | TC-184 / UJ-060 |

## Hypotheses (investigate in 01/04/07)

1. Embed ↔ corpus pin drift  
2. `min_score` filters everything  
3. Golden fixture URLs missing from staging corpus  
4. Retrieve/RPC/filter bug  

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Re-gate on still-empty pools | Hard gate: F46 success criteria before F45 run |
| CE fails again with real pools | Spike-only default; floors unchanged |
| Corpus rebuild needed | Path B escalate (S021-D11); do not silently skip |
| Scope creep (#159, LangGraph) | Out of scope unless AskQuestion unlocks |

## Routing

Standard: `01 → 02 → 04 → 07 → 08 → 09 → 10 → 11 → 12 → 13` (skip 03/05/06/15).

## Next

User confirm D9–D12 → mark impact **approved** → **01-requirements** (delta; load seed).

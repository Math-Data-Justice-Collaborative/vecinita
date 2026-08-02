---
session_id: S020-retrieval-batch-b
type: feature
status: in_progress
branch: evolve/EV-017-retrieval-batch-b
started_at: 2026-08-02
intent: "Batch B retrieval — F43 answer cache + #83/#161 CE spike + #162 soft language filter (continues S019)"
orchestrator: 16-evolve
evolve_cycle_id: EV-017
github_issues: [83, 161, 162]
predecessor: S019-retrieval-quality
predecessor_cycle: EV-016
context_briefs: []
standing_docs_touched:
  - docs/feature-list.md
  - docs/decisions/evolve-decisions.md
  - docs/config-spec.md
  - docs/test-plan.md
  - docs/spec.md
---

# Session S020 — Retrieval Batch B

## Intent

Continue S019 retrieval work as **Batch B**: ship the **F43 answer/retrieval cache**
(cost win from H1/H9 harness), keep **#83 / #161** cross-encoder rerank as an open
spike-gated track, and include **#162** soft language filter in the same cycle
(optional / empty-hit path — not proven on staging golden).

## Predecessor

| Item | Ref |
|------|-----|
| Session | [S019-retrieval-quality](../S019-retrieval-quality/session-brief.md) |
| Cycle | EV-016 (F42 H7+P1) — **completed**; PR #172 @ `b08ec30` |
| Cache spike | [spike-harness-cache.md](../S019-retrieval-quality/reports/spike-harness-cache.md) |
| CE spike | [spike-a4-r3-cross-encoder.md](../S019-retrieval-quality/reports/spike-a4-r3-cross-encoder.md) |
| Language spike | [spike-a3-language.md](../S019-retrieval-quality/reports/spike-a3-language.md) |
| Recommendation | [spike-recommendation.md](../S019-retrieval-quality/reports/spike-recommendation.md) |

## Issues in scope

| Issue | Title | Role |
|-------|-------|------|
| F43 (new Fn) | Answer / retrieval cache | **Primary ship** — H1/H9 cost win; no LangGraph |
| [#83](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/83) / [#161](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/161) | Smart retrieval + rerank (CE) | Spike track — prior R3 failed lift bar; still open |
| [#162](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/162) | Soft language filter | In cycle — optional / empty-hit; not proven on golden |

## Scope discipline

**In:**
- F43 cache on ChatRAG / shared RAG path (exact ± semantic / retrieve cache per Phase 0 lock)
- Renewed CE spike plan for #83/#161 with a clear ship/no-ship gate
- #162 soft fallback design for empty-hit / #54-class cases (config-gated unless proven)

**Out (unless Phase 0 expands):**
- LangGraph / ADR-006 amend (S019-D27 still deferred)
- Multilingual embed swap / #159
- Model upsizing / synthesizer change
- Re-opening F42 packing (already LIVE)

## Decisions (session open — 2026-08-02)

| ID | Decision |
|----|----------|
| S020-D1 | Open new `feature` session **S020-retrieval-batch-b** (do not reopen S019) |
| S020-D2 | Scope = **all three** in one cycle (F43 + CE spike + #162) |
| S020-D3 | Routing = **Standard** (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06, 15) |

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Standard**.

## Evolve

- Cycle: **EV-017**
- Feature IDs: **F43** (+ possible secondary Fn if #162 / CE ship — Phase 1 allocation)
- Branch: `evolve/EV-017-retrieval-batch-b`

## 01-requirements handoff

Load [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) first
(after Phase 0 scope lock). Not a greenfield interview.

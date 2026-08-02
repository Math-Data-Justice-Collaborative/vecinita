---
session_id: S021-retrieval-follow-on
type: feature
status: in_progress
branch: evolve/EV-018-retrieval-follow-on
started_at: 2026-08-02
intent: "Empty retrieve + CE re-gate follow-on after EV-017 (F45 spike-only); fix staging empty retrieve pools then re-run AC-BB9/UJ-060/#83 ship gate"
orchestrator: 16-evolve
evolve_cycle_id: EV-018
github_issues: [83, 161]
predecessor: S020-retrieval-batch-b
predecessor_cycle: EV-017
context_briefs:
  - ./context-brief.md
standing_docs_touched:
  - docs/feature-list.md
  - docs/decisions/evolve-decisions.md
  - docs/spec.md
  - docs/user-journeys.md
  - docs/test-plan.md
  - docs/acceptance-criteria.md
  - docs/decisions.md
---

# Session S021 — Retrieval follow-on (empty retrieve + CE re-gate)

## Intent

Successor to **S020 / EV-017**. F43 (H1 cache) and F44 (soft language) shipped;
F45 CE stayed **spike-only** because staging golden / live H3 returned **empty retrieve
pools** (`pool=0`, faith null). This session investigates and fixes retrieve reliability,
then re-runs the CE ship gate (AC-BB9 / UJ-060 / #83).

## Predecessor

| Item | Ref |
|------|-----|
| Session | [S020-retrieval-batch-b](../S020-retrieval-batch-b/session-brief.md) |
| Cycle | EV-017 — **completed**; PR [#173](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/173) @ `f24a620` |
| Evolve summary | [evolve-summary.md](../S020-retrieval-batch-b/reports/evolve-summary.md) |
| CE ship gate FAIL | [ce-ship-gate.md](../S020-retrieval-batch-b/reports/ce-ship-gate.md) |
| CE runbook | [spike-f45-ce-runbook.md](../S020-retrieval-batch-b/reports/spike-f45-ce-runbook.md) |

## Issues in scope

| Issue | Title | Role |
|-------|-------|------|
| Staging empty retrieve | `pool=0` / empty `sources` on golden + live H3 | **Primary** — unblock CE re-gate |
| [#83](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/83) / [#161](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/161) | Smart retrieval + CE rerank | Re-run ship gate after retrieve fix; ship or keep spike-only |
| AC-BB9 / UJ-060 / TC-184 | CE floors (relevancy ≥0.28, faith ≥0.91) | Re-evaluate once pools non-empty |

## Scope discipline

**In:**
- Diagnose staging retrieve emptiness (embed ↔ corpus pin / `min_score` / fixture URLs / index)
- Fix or document + remediate so golden rows return non-empty pools
- Re-run F45 CE ship gate against staging; record ship vs spike-only
- Spec/test deltas only as needed for the fix + re-gate

**Out (unless Phase 0 expands):**
- Re-litigate F43 cache / F44 soft language (already LIVE; flags stay as deployed)
- LangGraph / ADR-006 amend
- Multilingual embed swap / #159
- Synthesizer / model upsizing
- Closing #83 without a non-empty retrieve re-gate

## Decisions (session open — 2026-08-02)

| ID | Decision |
|----|----------|
| S021-D1 | Open new `feature` session **S021-retrieval-follow-on** (do not reopen S020) |
| S021-D2 | Scope = **empty retrieve investigation + CE re-gate** in one cycle |
| S021-D3 | Routing = **Standard** (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06, 15) |
| S021-D4 | 00-context = **scoped delta** (reuse S020 priors; no full regenerate) |
| S021-D5 | EV-018 allocated by **16-evolve** after Phase 0 Fn lock (not at 00 open) |
| S021-D6 | Carry forward CE floors: relevancy ≥ **0.28**, faith ≥ **0.91** (S020-D12) unless Phase 0 changes |
| S021-D7 | Prod `VECINITA_RAG_RERANK_CE` stays **false** until re-gate passes + deploy approval |
| S021-D8 | Fn ids: **F46** retrieve reliability + extend **F45** CE re-gate |
| S021-D9 | Ordering: **F46 first**, then F45 re-gate (two milestones) |
| S021-D10 | Planned Fn in evolve (not nested hotfix by default) |
| S021-D11 | Deploy **Path A** default; Path B if corpus rebuild required |
| S021-D12 | Proceed → EV-018 + 01 after user confirm |
| S021-D13 | Outcome-based ACs; diagnose root cause in 04/07 |
| S021-D14 | Defer BUG file until 07 code repro |
| S021-D15 | UJ-061 + TC-185/186 + AC-FO1–FO5; amend UJ-060 |
| S021-D16 | Approve locked L1–L14 |

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Standard**.

## Evolve

- Cycle: **EV-018**
- Feature IDs: **F46** (retrieve reliability), **F45** (CE re-gate extension) — S021-D8
- Branch: `evolve/EV-018-retrieval-follow-on` (from `origin/main` @ `f24a620`)
- Impact: [reports/phase0-impact.md](./reports/phase0-impact.md)

## 01-requirements

- Seed: [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md)
- Report: [reports/01-requirements-follow-on.md](./reports/01-requirements-follow-on.md) — **completed**
- RD-209–RD-218 · S021-D13–D16

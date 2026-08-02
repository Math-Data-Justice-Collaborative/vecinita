---
session_id: S019-retrieval-quality
type: feature
status: in_progress
branch: evolve/EV-016-retrieval-quality
started_at: 2026-07-31
intent: "Batch A retrieval quality — F42=H7+P1 on E0; phase0_approved; Phase A 01-requirements; E1 rejected (S019-D37)"
orchestrator: 16-evolve
evolve_cycle_id: EV-016
github_issues: [158, 161, 165, 162]
parent_issue_if_rerank: 83
context_briefs: []
standing_docs_touched:
  - docs/feature-list.md
  - docs/decisions/evolve-decisions.md
  - docs/config-spec.md
  - docs/test-plan.md
---

# Session S019 — Batch A retrieval quality

## Intent

Investigate retrieval-quality levers on the **F36 eval harness**, pick winners, allocate
**one Fn (F42)**, and ship **at most one** change on the shared surface
(`packages/rag` + ChatRAG prompt assembly).

## Issues in scope (investigation set)

| Issue | Title | Role |
|-------|-------|------|
| [#158](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/158) | Tune top_k / sources returned | Candidate |
| [#161](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/161) | Rerank approach on F36 → feeds #83 | Candidate |
| [#165](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/165) | Richer context packing | Candidate |
| [#162](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/162) | Soft language filter / cross-lang fallback | Optional 4th candidate |

## Scope discipline

**In:**
- F36 spike / baseline + cheap ablations across the four candidates
- Recommendation → allocate **F42** → Standard build of **one** shipped change
  (e.g. packing + top_k default, or a cheap rerank slice)
- If rerank wins: ship a **cheap** slice this cycle; leave full [#83](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/83) open as parent

**Out:**
- [#82](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/82) query refinement
- [#84](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/84) groundedness / answer formatting
- Full [#76](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/76) umbrella
- Full #83 smart retrieval (unless cheap slice only)

## Decisions (session open)

| ID | Decision |
|----|----------|
| S019-D1 | Open `feature` session → 16-evolve |
| S019-D2 | Routing = **Standard** (`01→02→04→07→08→09→10→11→12→13`; skip 03, 05, 06) |
| S019-D3 | Include **#162** in investigation set |
| S019-D4 | Spike F36 first → recommend → allocate F42 → build |
| S019-D5 | If rerank wins → ship cheap slice; #83 remains parent |
| S019-D6 | Success = F36 lift vs baseline + Admin promote-path smoke |
| S019-D7 | Local fixtures first; staging only if lift unclear |
| S019-D8 | Prefer heuristic; CE on Modal OK if lift clear (A+C) |
| S019-D9 | Lock scope → spike plan → F36 baseline |

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Standard**.

## Evolve

- Cycle: **EV-016**
- Feature IDs: **F42** = **H7+P1** (S019-D22 packing + S019-D31 hybrid) — `phase0_approved` pending; ISS-008 gates promote smoke
- Branch: `evolve/EV-016-retrieval-quality`
- F43 cache / Spanish relevancy follow-on — later unless expanded

## Decisions (Phase 0 batch 1 — 2026-07-31)

| ID | Decision |
|----|----------|
| S019-D21 | Lock synthesizer `qwen2.5:1.5b-instruct`; stop model sweep (skip M1+) |
| S019-D22 | Allocate **F42 = P1 packing** |
| S019-D23 | Harness spike separate from F42 ship track |
| S019-D24 | Intend LangGraph in ChatRAG → **ADR-006 amend required** before ship |
| S019-D25 | Cache matrix: embed/retrieve + KV + answer cache + ephemeral memory |
| S019-D26 | Playground GPU → **T4** |
| S019-D27 | ADR-006: spike first; defer amend until data |
| S019-D28 | Harness → **H0–H9** + schemas S0–S8 (intent / sub-agents / answer class) |
| S019-D29 | Hybrid option **A** — measure Hy0–Hy4 then ship |
| S019-D30 | EN/ES + answer_lang_match + cross_lang metrics |
| S019-D31 | Sweep winner **F42 = H7+P1**; drop R1; es_rel follow-on |
| S019-D32 | No-prompt baselines per model vs pack/prompt/H7 lifts |

## Model sweep (closed)

All Tiny–S3 cells tied @ relevancy **0.23** vs 1.5B control → **no model change**.

- Plan: [reports/model-sweep-plan.md](./reports/model-sweep-plan.md)
- Tracker: [reports/model-sweep-tracker.md](./reports/model-sweep-tracker.md) — status **closed**
- Harness plan: [reports/spike-harness-cache.md](./reports/spike-harness-cache.md)
- Harness runner: [scripts/spike_harness_workflows.py](./scripts/spike_harness_workflows.py) (H0-H9)
- Hybrid: [reports/spike-hybrid-plan.md](./reports/spike-hybrid-plan.md) · `20260801T002819Z_hybrid-sweep.json`
- Prompt baselines: [reports/spike-model-prompt-baseline.md](./reports/spike-model-prompt-baseline.md) · `20260801T011751Z_model-prompt-baseline.json`
- F42 draft: [reports/spike-recommendation.md](./reports/spike-recommendation.md)

## Links

- Related: F36 eval; S018 eval job dispatch; ADR-006 / ADR-004 (LangGraph); ADR-013; ADR-037
- Standing: [feature-list.md](../../feature-list.md), [spec.md](../../spec.md), [test-plan.md](../../test-plan.md)
- Scope: [evolve-decisions.md](../../decisions/evolve-decisions.md) §Cycle EV-016

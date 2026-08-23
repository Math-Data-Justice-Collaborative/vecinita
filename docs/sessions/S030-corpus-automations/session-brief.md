---
session_id: S030-corpus-automations
type: feature
status: in_progress
branch: evolve/EV-027-corpus-automations
started_at: 2026-08-07
intent: "GitHub #73+#72+#219 — corpus automations, Modal fine-tune, freshness via 16-evolve EV-027"
orchestrator: 16-evolve
evolve_cycle_id: EV-027
github_issue: 73
github_issues: [73, 72, 219]
context_briefs: []
standing_docs_touched: []
---

# Session S030 — Corpus automations (#73)

## Intent

Set up **automations** so that when corpus content is added or changed, relevant downstream
jobs run automatically (e.g. ingest → embed → write/index; optional fine-tune thresholds;
Modal schedule/queue; idempotency; DM observability; enable/disable + cost caps).

Source: [GitHub #73](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/73).

## Scope (Phase 0 — intake locked pending proceed gate)

**In (S030-D2–D12):**

- **#73** automations: job completion + cron + doc CRUD; chain; idempotency; kill-switch/cost caps; DM run history + enable/disable
- **#219** freshness: scheduled refresh, stale detection, change-aware ingest, operator refresh controls
- **#72** fine-tune: LoRA/PEFT on pinned Qwen; Modal train + serve; eval vs base; **prod promote only if better**; manual train approve

**Out:**

- #192 full dashboard widgets
- Blind FT prod promote without eval win
- Casual prod corpus mutation without AskQuestion

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **Full** (S030-D9).

## Roadmap / tech plan

- [roadmap.md](./roadmap.md) — GH issue map + Phase 30 milestones
- [reports/tech-plan-delta.md](./reports/tech-plan-delta.md) — TP1–TP10 locked (S030-D29)
- Execution plan: Phase 30 (M127–M130)

## Evolve

- Orchestrator: **16-evolve**
- Cycle: **EV-027**
- Decisions: S030-D0…D29
- Branch: `evolve/EV-027-corpus-automations`
- Features: **F75** (#73), **F76** (#219), **F77** (#72)

## Corpus cites

[Corpus: product] [Corpus: system-spec] [Corpus: deploy-integration] [Corpus: data]
[Corpus: journeys] [Corpus: api] [Corpus: acceptance] [Corpus: tests] [Corpus: adr]

## Next

**05-verify-tech** → Gate B→C → **06-tech-tooling** → **07-build** (Phase 30).

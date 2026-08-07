---
session_id: S028-chat-source-ux
type: feature
status: in_progress
branch: feat/S028-chat-source-ux
started_at: 2026-08-06
intent: "GitHub #222 #223 #224 chat source UX (URL validation display, dynamic relevance sources, operator display names) via 16-evolve; feature preset routing; prod-only deploy — be careful"
orchestrator: 16-evolve
evolve_cycle_id: EV-026
github_issue: 222
github_issues: [222, 223, 224]
context_briefs: []
standing_docs_touched: []
---

# Session S028 — Chat source UX (#222 #223 #224)

## Intent

Ship chat source UX improvements for GitHub issues **#222**, **#223**, and **#224**:

| Issue | Theme (intake) |
|-------|----------------|
| #222 | URL validation display |
| #223 | Dynamic relevance sources |
| #224 | Operator display names |

Route via **16-evolve** with the **feature preset** routing plan. Live DigitalOcean/Modal is **production** — deploy carefully.

## Scope (Phase 0 — open)

**In (candidate; 01/16 will lock Fn):**

- ChatRAG / admin UX for source URL validation display
- Dynamic relevance / source presentation
- Operator-facing display names for sources

**Out (until explicitly expanded):**

- Casual prod promote / corpus mutation without AskQuestion
- New guardrail frameworks (03 skipped — reconfirm Phase 1)
- New dependency stacks (06 skipped — reconfirm Phase 1)

## Routing plan

See [routing-plan.md](./routing-plan.md). Preset: **feature** (lean + tech verify + build/QA/e2e/deploy/smoke).

## Roadmap

See [roadmap.md](./roadmap.md) (Phase 29 M123–M126).

## Evolve

- Orchestrator: **16-evolve**
- Cycle: **EV-026** (Phase 0 intake)
- Decisions: **S028-D1** (routing/open 1a/2a), **S028-D2** (prod-careful), **S028-D3** (EV start)
- Branch: `feat/S028-chat-source-ux` → planned `evolve/EV-026-chat-source-ux` at Phase 1 / code start
- Candidate Fn: **F72–F74** (allocate after Phase 0 approval)

## Prod-careful (S028-D2)

User: *"there is only one deploy that is prod so please be careful"*

Interpretation:

- Treat live DigitalOcean / Modal as **production**
- No casual promote
- Stages **12–13** require **explicit AskQuestion** before any prod deploy or corpus mutation
- Prefer verify on tip + careful smoke
- Staging-as-shadow (if infra still exists) is **optional evidence only** — live cutover is prod

[Corpus: sessions] [Spec: docs/staging-runbook.md §EV-025 prod cutover]

## Links

- https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/222
- https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/223
- https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/224

## Decisions (session open)

| ID | Decision |
|----|----------|
| S028-D1 | Approvals 1a / 2a — open S028 + feature preset routing |
| S028-D2 | Prod-careful — AskQuestion before 12–13 prod deploy / corpus mutation |

## 01-requirements handoff

Load first: [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md)

## Next

1. **Approve Phase 29** (AskQuestion in chat) → mark 04 complete
2. **05-verify-tech** (delta)
3. Do **not** run 12–13 without AskQuestion (S028-D2/D7)

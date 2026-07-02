---
session_id: S008-eval-ux-playground
type: feature
status: in_progress
branch: feat/S008-eval-ux-playground
started_at: 2026-07-02
intent: "Evaluation UX polish (run list refresh, jobs tab integration, dashboard charts) + isolated eval playground with versioned configs, super-admin runtime promote to ChatRAG"
orchestrator: 16-evolve
evolve_cycle_id: EV-009
context_briefs:
  - docs/context/eval-ux-playground.md
standing_docs_touched: []
linked_issues: []
prior_session: S007-rag-eval
---

# Session S008 — eval UX + playground

## Intent

Follow-on to F36 (S007/EV-008): fix evaluation page UX nits, show eval runs on the Jobs tab,
enrich dashboard charts, and deliver an admin evaluation playground for RAG + judge configuration
with per-user versioned presets and super-admin runtime promotion to production ChatRAG.

## Scope

**In scope**

- Item 1: Immediate eval run appearance in history (no manual refresh)
- Item 2: `job_type=eval` in unified jobs API + Jobs tab
- Item 3: Chart scatter + time-range presets (FE on existing timeseries API)
- Item 4: Playground (golden + ad-hoc), config schema, per-user share-read presets, super-admin promote via runtime config switch

**Out of scope (v1)**

- Langfuse / Phoenix observability platforms
- In-app Modal/DO redeploy button (runtime switch instead)
- Changing live ChatRAG without super-admin promote action
- MFA / bulk CSV (S005 deferred items)

## Routing plan

See [routing-plan.md](./routing-plan.md).

## Links

- Prior: [S007 session brief](../S007-rag-eval/session-brief.md)
- Context: [eval-ux-playground.md](../../context/eval-ux-playground.md)
- F36 baseline: [rag-eval.md](../../context/rag-eval.md)

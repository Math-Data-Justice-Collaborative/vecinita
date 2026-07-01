# 04-tech-plan delta — Eval interactive dashboard (S007 / EV-008)

**Date:** 2026-07-01  
**Session:** S007-rag-eval  
**Parent report:** [04-tech-plan.md](./04-tech-plan.md)  
**Scope doc:** [scope-addition-dashboard.md](./scope-addition-dashboard.md)  
**Requirements delta:** [01-requirements-dashboard-delta.md](./01-requirements-dashboard-delta.md)  
**Status:** Complete

## User request

Expand S007 / Phase 14 (R68, same session) with interactive eval dashboards:

- Time-series plots of metrics over time
- Minimizable / customizable chart panels
- Pivot-style explore table with user-selected axes
- Admin-defined evaluation criteria
- Comprehensive operator views for regression analysis

## Technical decisions (TP-S007-17–25)

| ID | Decision |
|----|----------|
| TP-S007-17 | Tabbed **Dashboard / Explore / Criteria** on `/evaluation` (Run/History unchanged) |
| TP-S007-18 | **shadcn/ui Chart + recharts** — `EvalTrendCharts`, threshold reference lines |
| TP-S007-19 | `GET /internal/v1/eval/runs/timeseries` from `metrics_summary` |
| TP-S007-20 | `eval_criteria` migration + CRUD API + `packages/eval` runner hook (`llm_rubric`) |
| TP-S007-21 | Client-side pivot (&lt;500 rows) via `@tanstack/react-table` |
| TP-S007-22 | Layout prefs in device-local `localStorage` only |
| TP-S007-23 | CORS preflight tests for timeseries + criteria routes |
| TP-S007-24 | Same branch/PR-113; redeploy: migration → API → FE |
| TP-S007-25 | **recharts** new FE dependency; no new Python deps |

## Execution plan delta

**M64** appended to Phase 14 — 10 tasks (T64.1–T64.10). Phase 14 gate extended for TC-117–TC-122,
AC-E17–AC-E21.

## Artifacts produced

| Artifact | Path |
|----------|------|
| ADR | `docs/adr/ADR-034-ev008-eval-interactive-dashboard.md` |
| Decisions | `docs/decisions.md` — TP-S007-17–25 |
| Dependency inventory | `docs/dependency-inventory.md` — recharts |
| Execution plan | `docs/execution-plan.md` — M64, Current State |
| API contract | `docs/api-contract.md` — timeseries + criteria (01-requirements delta) |

## Handoff

**Next stage:** 07-build — start **T64.1** (Vitest TC-117 red).

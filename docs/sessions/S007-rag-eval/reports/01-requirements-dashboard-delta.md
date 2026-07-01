# 01-requirements delta — Eval interactive dashboard (S007 / EV-008)

**Date:** 2026-07-01  
**Session:** S007-rag-eval  
**Parent report:** [01-requirements.md](./01-requirements.md)  
**Scope doc:** [scope-addition-dashboard.md](./scope-addition-dashboard.md)  
**Status:** Complete (delta)

## User request

Expand S007 / Phase 14 (same session, R68) with **interactive eval dashboards**:

1. Time-series plots of evaluation metrics over time
2. Minimizable and customizable evaluation plot panels
3. Ability to add new evaluation criteria (admin-configurable)
4. Pivot-style explore table with user-selected row/column/value axes
5. Dashboard axis customization (locale, domain, metric, run date, pass/fail, etc.)
6. Additional UX to support comprehensive, operator-friendly regression analysis

## Document manifest (delta)

| Document | Action |
|----------|--------|
| feature-list.md | Delta — F36 dashboard bullets extended |
| user-journeys.md | Delta — **UJ-041**, **UJ-042**, **UJ-043** |
| test-plan.md | Delta — **TC-117–TC-122** |
| acceptance-criteria.md | Delta — **AC-E17–AC-E21** (pending M64 build) |
| api-contract.md | Delta — timeseries + criteria CRUD routes |
| decisions.md | Delta — **RD-114–RD-122** |

Skipped: spec.md (no new components beyond F36 row), config-spec (no new env vars v1), README.

## Interview decisions (dashboard)

| ID | Decision |
|----|----------|
| RD-114 | Scope stays in **S007 / EV-008 / M64** — F36 extended, not new feature |
| RD-115 | Three dashboard views: **Dashboard**, **Explore**, **Criteria** on `/evaluation` |
| RD-116 | Timeseries API + line/area charts; user selects metrics and date/run filters |
| RD-117 | Client-side pivot v1 (&lt;500 rows); user picks row/column/value axes |
| RD-118 | Collapsible panels; layout in `localStorage` only |
| RD-119 | `eval_criteria` table + CRUD + runner hook |
| RD-120 | shadcn/ui Chart + **recharts** (new FE dep) |
| RD-121 | Stretch: run overlay compare, CSV export from explore |
| RD-122 | Threshold reference lines; pass/fail coloring; date/run filters |

## Test requirements summary

| Layer | Artifacts |
|-------|-----------|
| E2E journey | UJ-041 (trends), UJ-042 (pivot), UJ-043 (criteria) |
| Vitest | TC-117, TC-118, TC-119, TC-121 |
| Integration | TC-120 (criteria CRUD), TC-122 (timeseries API) |

## Handoff

**Next stage:** 04-tech-plan delta (TP-S007-17+, ADR-033 amend or ADR-034) → **07-build** M64 (T64.1–T64.10+).

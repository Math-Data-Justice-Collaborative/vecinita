# Scope addition — Eval interactive dashboard (S007 / EV-008)

**Date:** 2026-07-01  
**Session:** S007-rag-eval  
**Evolve cycle:** EV-008  
**Feature:** F36 (extended)  
**Issue:** [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)  
**PR:** [#113](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/113)

## User request

Expand the current session (Phase 14) to include **interactive dashboards** for the eval service:

1. **Time-series plots** — evaluation metrics over time (per run)
2. **Minimizable / collapsible** chart panels with layout persistence
3. **Customizable evaluation plots** — user selects metrics, chart type, date/run filters
4. **Add new evaluation criteria** — extensible metric/criterion definitions (admin-configurable)
5. **Pivot-style explore table** — user picks row/column/value axes (like a lightweight pivot table)
6. **Dashboard axis customization** — group/slice by locale, domain, metric, run date, pass/fail, etc.
7. **General UX** — comprehensive, operator-friendly views for regression analysis

## Baseline (M59–M63 — delivered)

The v1 eval tab (`EvaluationPage`) provides:

- Run trigger + polling
- Aggregate metric summary cards (retrieval, faithfulness, answer relevancy, latency)
- Run history list + per-question drill-down table
- Threshold highlighting (&lt;0.70)

**Gap:** No charts, no trend visualization, no pivot/explore views, no user-defined criteria, no layout customization.

## Proposed scope (M64)

### UI — Dashboard views (`data-management-frontend`)

| Capability | Description |
|------------|-------------|
| **Trend charts** | Line/area charts of aggregate metrics across `eval_runs` (x = run time or run id; y = selected metrics) |
| **Chart widgets** | Multiple chart panels; collapse/minimize; drag-resize optional v1.1 |
| **Layout prefs** | Persist panel visibility, selected metrics, and axis choices in **device-local `localStorage`** (ADR-004 — no PII) |
| **Explore table** | Pivot-like grid: user selects row axis (e.g. locale, domain), column axis (e.g. metric), aggregation (mean, pass rate) |
| **Criteria manager** | Admin UI to define additional eval criteria (name, scorer type, threshold, enabled); stored server-side |
| **Run compare** | Overlay or side-by-side two runs on same chart (stretch if time permits) |

### API / data (`internal-write-api` + Postgres)

| Capability | Description |
|------------|-------------|
| **Timeseries endpoint** | `GET /internal/v1/eval/runs/timeseries` — compact series for charts (or extend list endpoint with `?include_aggregates=true`) |
| **Criteria CRUD** | `GET/POST/PATCH /internal/v1/eval/criteria` — admin-only; viewer → 403 |
| **Extensible scoring** | `eval_criteria` table + runner hook to compute custom criteria per row; results in `eval_run_items.metrics` JSON |
| **Explore aggregation** | Server-side or client-side pivot from `eval_run_items` — prefer client for v1 if row count &lt; 500 |

### Dependencies

| Dep | Action |
|-----|--------|
| **recharts** | Add to `data-management-frontend` (shadcn/ui Chart pattern) — back-add to `dependency-inventory.md` |
| **@tanstack/react-table** | Already used in admin — reuse for explore/pivot table |

### Out of scope (this addition)

- Public/end-user dashboards
- Langfuse/Phoenix external viz
- Real-time streaming metrics (WebSocket)
- ML auto-tuning from dashboard

## Decisions

| ID | Decision |
|----|----------|
| R68 | Scope expansion stays in **S007 / Phase 14 / EV-008** — not a new session |
| R69 | Charting: **shadcn/ui Chart + recharts** (new FE dependency) |
| R70 | Custom criteria: **Postgres `eval_criteria` + admin CRUD**; runner computes at eval time |
| R71 | Pivot/explore: **client-side** aggregation from run detail API for v1; layout prefs in `localStorage` |
| R72 | Downstream: **01-requirements delta** (UJ/TC/AC) + **04-tech-plan delta** (ADR-034) — **complete**; **07-build** M64 next |

## Requirements artifacts (01-requirements delta — complete)

| Artifact | IDs |
|----------|-----|
| user-journeys.md | UJ-041, UJ-042, UJ-043 |
| test-plan.md | TC-117–TC-122 |
| acceptance-criteria.md | AC-E17–AC-E21 |
| api-contract.md | timeseries + criteria CRUD |
| decisions.md | RD-114–RD-122 |

Report: `docs/sessions/S007-rag-eval/reports/01-requirements-dashboard-delta.md`

## Milestone

**M64: Eval interactive dashboard** — see `docs/execution-plan.md` Phase 14.

## Routing impact

- **00-context:** partial re-run (this document + `docs/context/rag-eval.md` §Dashboard scope)
- **01-requirements:** in-place delta — UJ-041+, TC-117+, AC-E17+
- **04-tech-plan:** in-place delta complete — ADR-034, TP-S007-17–25
- **07-build:** M64 tasks T64.1–T64.10 (**in progress**)
- **08–13:** unchanged sequence after M64

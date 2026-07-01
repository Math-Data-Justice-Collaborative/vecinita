# ADR-034: EV-008 interactive eval dashboard (M64)

**Status:** Accepted  
**Date:** 2026-07-01  
**Stage:** 07-build  
**Session:** S007-rag-eval · **Evolve cycle:** EV-008 · **Feature:** F36 (scope extension)  
**Issue:** [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)

## Context

F36 baseline (M59–M63) delivers admin eval run trigger, per-metric summary cards, run history,
and per-question drill-down. Operators need richer analytics: time-series trends, customizable
pivot exploration, collapsible chart panels, and admin-defined evaluation criteria that flow into
runs and visualizations.

## Decision

Extend Phase 14 / EV-008 in-place (no new feature ID) with **M64 — Interactive eval dashboard**:

| Area | Choice |
|------|--------|
| Charts | **recharts** in `data-management-frontend` (new FE dep); line/area charts with threshold reference lines |
| Layout prefs | Device-local `localStorage` key `vecinita.eval.dashboard.v1` (ADR-004 safe — no server persistence) |
| Pivot explore | Client-side aggregation over fetched run items (&lt;500 rows v1) |
| Custom criteria | Postgres `eval_criteria` table + admin CRUD API; `llm_rubric` scorer via extended `JudgeClient.rubric_score` |
| Timeseries API | `GET /internal/v1/eval/runs/timeseries` — completed runs ordered by `completed_at` |
| Auth | Admin-only (same as existing eval routes); viewer → 403 |

## Schema

```text
eval_criteria
  id uuid PK
  slug varchar(64) UNIQUE
  label varchar(128)
  description text NULL
  scorer_type varchar(32)  -- 'llm_rubric'
  rubric text
  enabled boolean
  created_at timestamptz
  updated_at timestamptz
```

Custom criterion scores stored in `eval_run_items.metrics.custom_scores` (JSON map slug → float).

## API additions

- `GET /internal/v1/eval/runs/timeseries` — `EvalTimeseriesResponse`
- `GET /internal/v1/eval/criteria` — list
- `POST /internal/v1/eval/criteria` — create
- `PATCH /internal/v1/eval/criteria/{criterion_id}` — update (label, rubric, enabled)

## UI

`/evaluation` gains Radix tabs:

1. **Runs** — existing M62 content
2. **Dashboard** — time-series charts, minimizable panels, metric/axis selectors
3. **Explore** — pivot-style table (row/column/value axes)
4. **Criteria** — create/edit/disable custom rubrics

## Tests

TC-117–TC-122, UJ-041–UJ-043, AC-E17–AC-E21.

## Consequences

- **recharts** back-added to `docs/dependency-inventory.md` (FE only).
- Privacy: `eval_criteria` has no operator identity columns; rubrics are admin-authored text only.
- Runner loads enabled criteria per run; aggregate custom scores in `metrics_summary.custom_scores`.

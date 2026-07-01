# Scope addition — R68 interactive eval dashboard

**Session:** S007-rag-eval · **Evolve cycle:** EV-008 · **Date:** 2026-07-01  
**Issue:** [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)  
**ADR:** [ADR-034](../../adr/ADR-034-ev008-eval-interactive-dashboard.md)

## Summary

Extends F36 baseline (M59–M63) within Phase 14 with **M64 — Interactive eval dashboard**:

| Capability | Journey | Tests |
|------------|---------|-------|
| Time-series metric charts | UJ-041 | TC-117 |
| Collapsible chart panels + layout prefs (`localStorage`) | — | TC-119 |
| Pivot-style explore table (row/column/value axes) | UJ-042 | TC-118 |
| Admin-defined eval criteria (`eval_criteria` + CRUD API) | UJ-043 | TC-120, TC-121 |
| Timeseries API | — | TC-122 |

## API

- `GET /internal/v1/eval/runs/timeseries`
- `GET/POST/PATCH /internal/v1/eval/criteria`

## UI

`/evaluation?tab={runs|dashboard|explore|criteria}` — tab state in URL for deep links.

## Dependencies

- **recharts** (FE only) — back-added to `docs/dependency-inventory.md`

## Acceptance

AC-E17–AC-E21 (dashboard scope); baseline AC-E12–E16 unchanged.

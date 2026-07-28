# 01-requirements — Unified Admin Jobs (EV-012 / #116)

**Session:** S013-unified-job-monitoring  
**Date:** 2026-07-28  
**Mode:** delta (extend F32/F36; no new Fn)

## Summary

Product requirements locked for unified Admin Dashboard job monitoring: Modal owns all
long-running job lifecycles (including eval); DO Postgres stores metrics/data; Supabase is
auth-only; Jobs UI gets detail, SSE, status filter, retag document context, and admin CRUD.

## Architecture (RD-174 / RD-175 / ADR-038)

| Concern | Owner |
|---------|--------|
| Job lifecycle (ingest/retag/eval/…) | **Modal** ([job queue](https://modal.com/docs/guide/job-queue)) |
| Durable storage + metrics | **DO Postgres** |
| Operator identity | **Supabase Auth only** |
| Admin Jobs list | Modal `GET /jobs` (primary; not dual-list FE federation) |

Amends ADR-033 (eval leaves DO BackgroundTasks).

## Decisions

| ID | Decision |
|----|----------|
| RD-173 | SSE + 4s poll fallback + SSE retry |
| RD-174 | Modal all long-running jobs incl. eval |
| RD-175 | DO storage SoT; Supabase auth-only |
| RD-176 | Admin-only full job CRUD |
| RD-177 | Failed job call id + copy + dashboard link |
| RD-178 | Playwright T0-ui list→detail |

Phase 0 S013-D1…D22 confirmed; S013-D8 amended (Modal-primary list).

## Documents updated

- `docs/feature-list.md` — F32/F36 EV-012 deltas
- `docs/user-journeys.md` — UJ-023, UJ-044, UJ-050
- `docs/test-plan.md` — TC-146–TC-151 (+ TC-124 note)
- `docs/acceptance-criteria.md` — AC-J1–AC-J10
- `docs/decisions.md` — RD-173–RD-178
- `docs/api-contract.md` — EV-012 jobs deltas
- `docs/adr/ADR-038-modal-job-lifecycle-storage-split.md`
- `docs/decisions/evolve-decisions.md` — scope note refresh

## Open for 04-tech-plan

- Exact OpenAPI paths for SSE / cancel / retry / delete
- Eval enqueue bridge (internal-write → Modal)
- Modal Dict vs Postgres dual-write during migration
- Poll fallback details when both SSE streams (if any remain) fail

## Next

**02-verify-plan** (consistency pass on touched specs).

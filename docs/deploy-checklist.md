# Deploy Checklist

> **Generated**: 2026-08-03 (S023 / EV-020 delta)  
> **Status**: **ready** (12 signed S023-D21)  
> **Session**: S023-retrieval-topk-packing  
> **Features**: F50 top_k=8 · F51 default P3

Full checklist: [sessions/S023-retrieval-topk-packing/reports/deploy-checklist.md](sessions/S023-retrieval-topk-packing/reports/deploy-checklist.md)

Prior: [sessions/S022-ingest-resilience/reports/deploy-checklist.md](sessions/S022-ingest-resilience/reports/deploy-checklist.md)

## Standing — Modal / DM job types (BUG-2026-07-31)

When adding a new `job_type` (Admin enqueue → Modal `run_job`):

- [ ] Register an explicit handler in `apps/data-management-backend/.../jobs.py` (no ingest fall-through)
- [ ] Unknown types fail closed with `ValueError` / job `failed`
- [ ] Add or extend `tests/bugs/` coverage; husky pre-commit runs `scripts/ci/pre_commit_job_dispatch.sh`
- [ ] Update this checklist / session deploy notes if the type is user-facing

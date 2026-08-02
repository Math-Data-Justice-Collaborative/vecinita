# Deploy Checklist

> **Generated**: 2026-08-01 (S019 / EV-016 delta)  
> **Status**: **ready**  
> **Session**: S019-retrieval-quality  
> **Feature**: F42 H7+P1 retrieval quality (Hy1 on E0)

Full checklist: [sessions/S019-retrieval-quality/reports/deploy-checklist.md](sessions/S019-retrieval-quality/reports/deploy-checklist.md)

Prior: [sessions/S017-corpus-reembed-migration/reports/deploy-checklist.md](sessions/S017-corpus-reembed-migration/reports/deploy-checklist.md)

## Standing — Modal / DM job types (BUG-2026-07-31)

When adding a new `job_type` (Admin enqueue → Modal `run_job`):

- [ ] Register an explicit handler in `apps/data-management-backend/.../jobs.py` (no ingest fall-through)
- [ ] Unknown types fail closed with `ValueError` / job `failed`
- [ ] Add or extend `tests/bugs/` coverage; husky pre-commit runs `scripts/ci/pre_commit_job_dispatch.sh`
- [ ] Update this checklist / session deploy notes if the type is user-facing

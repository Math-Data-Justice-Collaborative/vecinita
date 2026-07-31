# Deploy Checklist

> **Generated**: 2026-07-30 (S017 / EV-015 delta)  
> **Status**: **ready**  
> **Session**: S017-corpus-reembed-migration  
> **Feature**: F41 corpus rebuild / shadow promote (#167)

Full checklist: [sessions/S017-corpus-reembed-migration/reports/deploy-checklist.md](sessions/S017-corpus-reembed-migration/reports/deploy-checklist.md)

Prior: [sessions/S002-admin-job-management/reports/deploy-checklist.md](sessions/S002-admin-job-management/reports/deploy-checklist.md)

## Standing — Modal / DM job types (BUG-2026-07-31)

When adding a new `job_type` (Admin enqueue → Modal `run_job`):

- [ ] Register an explicit handler in `apps/data-management-backend/.../jobs.py` (no ingest fall-through)
- [ ] Unknown types fail closed with `ValueError` / job `failed`
- [ ] Add or extend `tests/bugs/` coverage; husky pre-commit runs `scripts/ci/pre_commit_job_dispatch.sh`
- [ ] Update this checklist / session deploy notes if the type is user-facing

# Deploy Checklist

> **Generated**: 2026-08-18 (S031 standing pointer — EV-027 job types)  
> **Status**: standing index (latest session: S030 flags-off ready)  
> **Session**: S031-docs-gapfill (gap-fill); S030-corpus-automations (F75–F77)  
> **Features**: F75 catch-up · F76 freshness · F77 LoRA FT (in-tree; live enable deferred)

Latest cycle checklist: [sessions/S030-corpus-automations/reports/deploy-checklist.md](sessions/S030-corpus-automations/reports/deploy-checklist.md)

Prior: [sessions/S024-website-scrape-crawl/reports/deploy-checklist.md](sessions/S024-website-scrape-crawl/reports/deploy-checklist.md) · [sessions/S023-retrieval-topk-packing/reports/deploy-checklist.md](sessions/S023-retrieval-topk-packing/reports/deploy-checklist.md)

## Standing — Modal / DM job types (BUG-2026-07-31)

When adding a new `job_type` (Admin enqueue → Modal `run_job`):

- [ ] Register an explicit handler in `apps/data-management-backend/.../jobs.py` (no ingest fall-through)
- [ ] Unknown types fail closed with `ValueError` / job `failed`
- [ ] Add or extend `tests/bugs/` coverage; husky pre-commit runs `scripts/ci/pre_commit_job_dispatch.sh`
- [ ] Update this checklist / session deploy notes if the type is user-facing

Registered EV-027 types (handlers in-tree; live flags off):

| `job_type` | Feature | Notes |
|------------|---------|-------|
| `automation_catchup` | F75 | Residual catch-up only; shared schedule |
| `freshness_refresh` | F76 | Hash-aware; bump `last_checked_at` |
| `finetune_train` | F77 | Requires `POST /jobs/{id}/approve`; not on default CD path (S030-D59) |

CD omit: `vecinita-llm-finetune` may be absent from `modal.sh` / deploy-modal until an explicit follow-on. Flags-off 13-smoke is the standing posture.

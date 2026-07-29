# E2E report — EV-012 / S013 unified job monitoring

**Session:** S013-unified-job-monitoring  
**Cycle:** EV-012  
**Branch:** `evolve/EV-012-unified-job-monitoring`  
**Date:** 2026-07-29  
**HEAD:** `a6094dc` (after 08-verify)  
**Mode:** delta (UJ-023, UJ-044, UJ-050)

## Result

**PASS** at **T0** (API TestClient + Playwright T0-ui). **T1** skipped (no local Docker). **T2/T3** deferred to **13-deploy-smoke** / live.

## Tier matrix

| Tier | Status | Evidence |
|------|--------|----------|
| **T0** API (`tests/e2e`) | **PASS** 12/12 | UJ-023 (6), UJ-044 (2), UJ-050 (4) |
| **T0-ui** Playwright | **PASS** 9/9 | `uj023`/`uj044`/`uj050` under `--project=data-management` |
| **T1** integration | **SKIPPED** | Docker/`docker compose` unavailable on this host |
| **T2** connectivity (H1–H5) | **PENDING** | Owner: **13-deploy-smoke** |
| **T3** live UJ | **PENDING** | Owner: 13 / 15-service-health |

## Journey coverage (EV-012)

| Journey | Feature | T0 module | T0 | T0-ui | T2/T3 |
|---------|---------|-----------|----|-------|-------|
| UJ-023 Jobs tab | F32 | `test_uj023_job_management.py` | PASS | PASS | deferred |
| UJ-044 Eval on Jobs | F36/F32 | `test_uj044_eval_jobs_tab.py` | PASS | PASS | deferred |
| UJ-050 Job detail CRUD | F32 | `test_uj050_job_detail_crud.py` | PASS | PASS | deferred |

TC mapping: TC-146–151, TC-124 (per Phase 19 gate / test-plan).

## Commands

```bash
uv run pytest tests/e2e/test_uj023_job_management.py \
  tests/e2e/test_uj044_eval_jobs_tab.py \
  tests/e2e/test_uj050_job_detail_crud.py -v
# → 12 passed

npx playwright test --project=data-management \
  tests/ui/admin/uj023-jobs-tab.spec.ts \
  tests/ui/admin/uj044-eval-jobs-tab.spec.ts \
  tests/ui/admin/uj050-job-detail.spec.ts
# → 9 passed (DM preview; ChatRAG stub only for webServer port)
```

## Connectivity note

Mocks/TestClient **T0 ≠** production UI connected. H4–H5 and live Admin Jobs against staging remain **13-deploy-smoke**.

## Blockers for next stage

| Item | Impact |
|------|--------|
| **ISS-004** (NC playground Qwen 3B) | Listed as blocking **13-deploy-smoke** in workflow-state |
| PR #153 | Open; merge policy **do_not_merge** until deploy + user approval |
| Local Docker | Cannot re-run T1 here; rely on GitHub CI for integration |

## Next

Invoke **13-deploy-smoke** after resolving or waiving ISS-004; record H1–H5 (and H0c already covered in 08).

# E2E Behavior Report

> **Generated**: 2026-06-26 (S002 delta)  
> **Mechanism**: API + Frontend  
> **Session**: S002-admin-job-management

## Summary

| Tier | Status |
|------|--------|
| T0 local | **PASS** — 45 e2e tests |
| T1 integration | **PASS** — 35 tests |
| T3 live (UJ-023) | **FAIL** — production `GET /jobs` 405 until Modal redeploy |
| Frontend Vitest | **PASS** — 283 tests |

**New journeys:** UJ-023 (4 tests PASS T0); UJ-002 #88 tag resilience (PASS T0).

Full detail: [sessions/S002-admin-job-management/reports/e2e-report.md](sessions/S002-admin-job-management/reports/e2e-report.md)

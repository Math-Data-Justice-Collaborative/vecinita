# E2E Behavior Report

> **Generated**: 2026-06-29 (S004 delta — EV-005 F34)  
> **Mechanism**: API + Frontend  
> **Session**: S004-supabase-auth

## Summary

| Tier | Status |
|------|--------|
| T0 local | **PASS** — 59 e2e tests |
| T1 integration | **PASS** — 35 tests |
| T3 live | **NOT RUN** — staging env unset; auth not deployed |
| Frontend Vitest | **PASS** — 366 tests (admin 226, chat 134, packages 6) |

**New journeys (F34):** UJ-026–UJ-029 — all **PASS** at T0 (14 new API tests + Vitest auth suite).

**Regression:** UJ-001–UJ-025 — no T0 regressions.

Full detail: [sessions/S004-supabase-auth/reports/e2e-report.md](sessions/S004-supabase-auth/reports/e2e-report.md)

## Prior sessions

- [S002-admin-job-management/reports/e2e-report.md](sessions/S002-admin-job-management/reports/e2e-report.md) — UJ-023 F32; T3 live FAIL (GET /jobs 405 until Modal redeploy)

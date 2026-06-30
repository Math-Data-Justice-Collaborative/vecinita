# E2E Behavior Report

> **Generated**: 2026-06-30 (S006 delta — EV-007 F35 ext)  
> **Mechanism**: API + Frontend  
> **Session**: S006-invite-acceptance

## Summary

| Tier | Status |
|------|--------|
| T0 local | **PASS** — 69 e2e tests |
| T1 integration | **PASS** — 62 tests |
| Supabase contract | **PASS** — 17 tests |
| T3 live | **NOT RUN** — S006 not deployed; deferred to 13-deploy-smoke |
| Frontend Vitest | **PASS** — 500 tests (admin 329, chat 142, packages 29) |

**EV-007 delta (F35 ext):** UJ-031 invite `redirect_to` + accept-invite callback (TC-104, TC-106); UJ-033 reset-password callback (TC-107) — all **PASS** at T0.

**Regression:** UJ-001–UJ-038 — no T0 regressions vs S005 baseline.

Full detail: [sessions/S006-invite-acceptance/reports/e2e-report.md](sessions/S006-invite-acceptance/reports/e2e-report.md)

## Prior sessions

- [S005-user-mgmt-auth/reports/e2e-report.md](sessions/S005-user-mgmt-auth/reports/e2e-report.md) — UJ-030–UJ-038 F35
- [S004-supabase-auth/reports/e2e-report.md](sessions/S004-supabase-auth/reports/e2e-report.md) — UJ-026–UJ-029 F34
- [S002-admin-job-management/reports/e2e-report.md](sessions/S002-admin-job-management/reports/e2e-report.md) — UJ-023 F32

# QA Report

> **Project**: Vecinita  
> **Date**: 2026-06-26  
> **Skill**: 09-qa (S002 partial rerun)  
> **Scope**: S002 — F32 Job Management + #88 ingest tag resilience + 14-hotfix  
> **Branch**: `main` @ `6b72ba0`  
> **Session**: [S002-admin-job-management](sessions/S002-admin-job-management/reports/qa-report.md)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files
  Typecheck:      FAIL — 2 errors (reportAny, uncommitted bug test)
  Tests (Python): FAIL — 549 passed, 38 skipped, 1 failed (live GET /jobs deploy gap)
  Tests (FE):     PASS — 283 passed
  Coverage gate:  PASS — FE branch ≥95%
  Security:       PASS
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
```

**Overall: FAIL** — see [full S002 report](sessions/S002-admin-job-management/reports/qa-report.md) for details and QA-S002-001..006 findings.

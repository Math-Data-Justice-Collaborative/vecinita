# QA Report

> **Project**: Vecinita  
> **Date**: 2026-06-29  
> **Skill**: 09-qa — S004 / EV-005 / F34 (delta)  
> **Branch**: `feat/S004-supabase-auth`  
> **Session**: [S004-supabase-auth](sessions/S004-supabase-auth/reports/qa-report.md)

```text
QA Results:
  Lint:           PASS
  Format:         PASS
  Typecheck:      PASS
  Tests (Python): PASS — 546 passed, 38 skipped
  Tests (FE):     FAIL — admin 1 failed (chat 134/134)
  Coverage gate:  FAIL
  Security:       PASS
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
```

**Overall: pass_with_advisories** (remediated 2026-06-29) — blocking QA-S004-001/002 resolved. See [remediation section](sessions/S004-supabase-auth/reports/qa-report.md#qa-remediation-2026-06-29).

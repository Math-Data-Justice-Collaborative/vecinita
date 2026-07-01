# QA Report

> **Project**: Vecinita  
> **Date**: 2026-07-01  
> **Skill**: 09-qa — S007 / EV-008 / F36 (#99)  
> **Branch**: `feat/S007-rag-eval`  
> **Session**: [S007-rag-eval](sessions/S007-rag-eval/reports/qa-report.md)

```text
QA Results:
  Lint:           FAIL — 1 issue
  Format:         FAIL — 1 file
  Typecheck:      FAIL — 3 errors
  Tests (Python): FAIL — 768 passed, 41 skipped, 1 failed
  Tests (FE):     PASS — chat 142/142; admin 360/360; i18n 17/17; ui 12/12
  Coverage gate:  FAIL — privacy unit test
  Security:       PASS (1 gitleaks false positive — advisory)
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 verified; workspace vecinita
  H0c CORS:       PASS
  H4/H5 live:     SKIPPED — no staging env
```

**Overall: fail** — four blocking Python issues (lint, format, typecheck, stale privacy test). Frontends pass.

Full report: [docs/sessions/S007-rag-eval/reports/qa-report.md](sessions/S007-rag-eval/reports/qa-report.md)

Previous pass: [S006 / EV-007](sessions/S006-invite-acceptance/reports/qa-report.md) (2026-06-30).

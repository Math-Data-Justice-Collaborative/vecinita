# QA Report

> **Project**: Vecinita  
> **Date**: 2026-07-01 (rerun)  
> **Skill**: 09-qa — S007 / EV-008 / F36 (#99)  
> **Branch**: `feat/S007-rag-eval` @ `9361e4a`  
> **Session**: [S007-rag-eval](sessions/S007-rag-eval/reports/qa-report.md)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files
  Typecheck:      PASS — 0 errors
  Tests (Python): PASS — 769 passed, 41 skipped, 0 failed
  Tests (FE):     PASS — chat 142/142; admin 360/360; i18n 17/17; ui 12/12
  Tests (UI):     PASS — Playwright 20 passed, 2 skipped
  Coverage gate:  FAIL — internal-write-api + data-management-frontend < 95%
  Security:       PASS (gitleaks clean — advisories resolved)
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 verified; workspace vecinita
  H0c CORS:       PASS
  H4/H5 live:     SKIPPED — no staging env
```

**Overall: fail** — one blocking area: unit-test coverage gate (QA-S007-B05). Prior blockers B01–B04 resolved.

Full report: [docs/sessions/S007-rag-eval/reports/qa-report.md](sessions/S007-rag-eval/reports/qa-report.md)

Previous pass: first run 2026-07-01 (B01–B04); [S006 / EV-007](sessions/S006-invite-acceptance/reports/qa-report.md) (2026-06-30).

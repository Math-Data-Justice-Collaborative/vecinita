# QA Report

> **Project**: Vecinita  
> **Date**: 2026-06-30  
> **Skill**: 09-qa — S005 / EV-006 / F35 (delta)  
> **Branch**: `feat/S005-user-mgmt-auth`  
> **Session**: [S005-user-mgmt-auth](sessions/S005-user-mgmt-auth/reports/qa-report.md)

```text
QA Results (after 2026-06-30 remediation):
  Lint:           PASS
  Format:         PASS
  Typecheck:      PASS
  Tests (Python): PASS — 703 passed, 39 skipped
  Tests (FE):     PASS — chat 142/142; admin 312/312 (Node 24)
  Coverage gate:  PASS — FE branches 97.1% (≥95% gate)
  Security:       PASS
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
  H0c CORS:       PASS
  Node runtime:   24.18.0 (fnm; matches CI/.nvmrc)
  Outdated PyPI:  15 remain (intentional llama-index 0.13.x pins)
```

**Overall: pass_with_advisories** — QA-S005-004/005/008 resolved; staging/D7 advisories remain.

Full report: [docs/sessions/S005-user-mgmt-auth/reports/qa-report.md](sessions/S005-user-mgmt-auth/reports/qa-report.md)

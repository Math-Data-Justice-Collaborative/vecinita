# QA Report

> **Project**: Vecinita  
> **Date**: 2026-06-30 (remediated)  
> **Skill**: 09-qa — S006 / EV-007 / F35 ext (#109)  
> **Branch**: `feat/S006-invite-acceptance`  
> **Session**: [S006-invite-acceptance](sessions/S006-invite-acceptance/reports/qa-report.md)

```text
QA Results (after 2026-06-30 remediation):
  Lint:           PASS
  Format:         PASS
  Typecheck:      PASS
  Tests (Python): PASS — 729 passed, 39 skipped
  Tests (FE):     PASS — chat 142/142; admin 329/329 (Node 24 auto)
  Coverage gate:  PASS — FE branches 96.6% (≥95% gate)
  Security:       PASS
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 verified; workspace vecinita
  H0c CORS:       PASS
  H4/H5 live:     PASS — 19 connectivity tests
  Node runtime:   ensure_node24.sh (fnm → 24.18.0)
  Outdated PyPI:  16 accepted (intentional pins)
```

**Overall: pass** — 6/7 advisories resolved or accepted; QA-S006-004 partial (live invite T3 → 13-deploy-smoke).

Full report: [docs/sessions/S006-invite-acceptance/reports/qa-report.md](sessions/S006-invite-acceptance/reports/qa-report.md)

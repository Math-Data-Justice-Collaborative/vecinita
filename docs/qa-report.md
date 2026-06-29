# QA Report

> **Project**: Vecinita  
> **Date**: 2026-06-29  
> **Skill**: 09-qa — S004 / EV-005 / F34 (delta)  
> **Branch**: `feat/S004-supabase-auth`  
> **Session**: [S004-supabase-auth](sessions/S004-supabase-auth/reports/qa-report.md)

```text
QA Results (after 2026-06-29 remediation):
  Lint:           PASS
  Format:         PASS
  Typecheck:      PASS
  Tests (Python): PASS — 603 passed, 33 skipped
  Tests (FE):     PASS — chat 142/142; admin 242 passed (exit 0)
  Coverage gate:  PASS — combined 100% (1278/1278 branches)
  Security:       PASS
  Cross-file:     PASS
  Template:       PASS
  Data / Modal:   D6 verified; D7 staged_procedure; workspace vecinita
  H0c CORS:       PASS
  Node runtime:   24 LTS (CI + .nvmrc + engines) — TP-S004-11
```

**Overall: pass_with_advisories** — blocking QA-S004-010 resolved; QA-S004-011 (Node 24) and QA-S004-003 done. Remaining advisories (QA-S004-005/006/007/008/009) deferred (env/GPU/ops).

Full report: [docs/sessions/S004-supabase-auth/reports/qa-report.md](sessions/S004-supabase-auth/reports/qa-report.md)

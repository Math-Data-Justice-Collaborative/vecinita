# S002 — Routing Plan (evolve-lite)

Approved by user 2026-06-26 (AskQuestion: routing=evolve_lite, scope=full).

| Stage | Status | Note |
|---|---|---|
| 00-context | completed | This session opener; #88 + #89 issues created |
| 01-requirements | pending | Delta — add Fn for Job Management tab (#89); #88 is a bug (no new requirement) |
| 04-tech-plan | pending | Delta — GET /jobs + list_jobs store method, /jobs admin page, state lifting, tag graceful degradation |
| 07-build | pending | #88 bug-investigation TDD fix + #89 feature tasks |
| 09-qa | pending | Full-repo QA |
| 10-e2e | pending | New UJ for Job Management tab |
| 12-verify-deploy | pending | Pre-deploy gate |
| 13-deploy-smoke | pending | Deploy + H1–H5 smokes |

## Skipped stages

| Stage | Reason |
|---|---|
| 02-verify-plan | Evolve-lite — small, well-understood delta |
| 03-plan-tooling | No new tooling/guardrails needed |
| 05-verify-tech | Evolve-lite — small tech delta |
| 06-tech-tooling | No new tooling/guardrails needed |
| 11-verify-impl | Evolve-lite — covered by 09-qa + 10-e2e + 13 smoke |

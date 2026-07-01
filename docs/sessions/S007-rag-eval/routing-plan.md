# Routing plan — S007-rag-eval

| Stage | Required | Mode | Skip rationale |
|-------|----------|------|----------------|
| 00-context | yes | scoped delta | Issue #99 + eval framework comparison — **completed 2026-07-01** |
| 01-requirements | yes | delta | F36 interview + eval curation Blocks A–F — **completed 2026-07-01** (RD-099–RD-113) |
| 02-verify-plan | no | — | Skipped — evolve-lite; standing docs sufficient |
| 04-tech-plan | yes | delta | ADR for R63, schema, API contract, cost estimate |
| 05-verify-tech | no | — | Skipped — evolve-lite |
| 07-build | yes | full | Implementation |
| 08-verify-build | yes | full | Milestone verify |
| 09-qa | yes | full | Full-repo QA |
| 10-e2e | yes | full | Admin eval journey + harness |
| 11-verify-impl | no | — | Skipped — evolve-lite |
| 12-verify-deploy | yes | full | Deploy checklist |
| 13-deploy-smoke | yes | full | Staging smoke |

## Approved

User approval recorded: 2026-07-01

- Park S006-invite-acceptance
- Open S007-rag-eval on `feat/S007-rag-eval`
- Eval tooling: LlamaIndex + custom (R63)

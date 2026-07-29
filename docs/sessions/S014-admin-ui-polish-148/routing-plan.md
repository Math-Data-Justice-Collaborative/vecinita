# S014 routing plan — Lean+build (S014-D3)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; early UI preview; Phase 0 intake done |
| 16-evolve | yes | in_progress | Orchestrator EV-013 |
| 01-requirements | yes | completed | RD-179–182; UJ-051; TC-152–155; AC-U1–U7 |
| 02-verify-plan | yes | completed | Gate A→B passed; M1 Playwright required |
| 07-build | yes | completed | TruncatedText + CorpusList + shared tables; Vitest + uj051 Playwright green |
| 08-verify-build | yes | completed | PASS — report `reports/verification-report.md`; personas ADVISORY (0 🔴) |
| 10-e2e | yes | completed | PASS T0/T0-ui UJ-051; T1 skip; T2/T3 → 13; report `reports/e2e-report.md` |
| 13-deploy-smoke | yes | in_progress | Path A FE pin ACTIVE; H1–H5 PASS; PR #154 open; report `reports/deploy-smoke.md` |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new guardrails |
| 04-tech-plan | FE-only density/truncation; layout notes fold into 01/07 |
| 05-verify-tech | Lean — fold checks into 02/08 |
| 06-tech-tooling | No new runtime deps |
| 09-qa | Lean — rely on 08 + 10 |
| 11-verify-impl | Lean — sign-off via 10/13 |
| 12-verify-deploy | Lean — 13-deploy-smoke |

## Preset

**Lean+build** = Lean (`01 → 02 → 10 → 13`) + `07` + `08` (no `04`).

## UI preview

Early non-deployed local Admin (`apps/data-management-frontend`, port 5174) — accepted (S014-D5).

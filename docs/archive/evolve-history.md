# Evolve history

Archived evolve cycle reports.

## EV-023 — CI / local quality + release automation (F62–F63)

**Cycle:** EV-023  
**Completed:** 2026-08-04  
**Session:** S025-ci-release-automation  
**Status:** completed (deploy gate S025-D16)  
**Features:** F62 (#182), F63 (#103) · Epic #194  
**Preset:** Lean+build (`01 → 02 → 07 → 08 → 10 → 13`)  
**PRs:** [#195](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/195) feature @ `58e52c8` · [#196](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/196) release git identity · [#197](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/197) docs closeout @ `e78e418`  
**Release:** [v0.4.1](https://github.com/Math-Data-Justice-Collaborative/vecinita/releases/tag/v0.4.1) @ `5fa370a`  
**Report:** [evolve-summary](../sessions/S025-ci-release-automation/reports/evolve-summary.md) · [deploy-smoke](../sessions/S025-ci-release-automation/reports/deploy-smoke.md)  
**Notes:** Infra-only; product H1–H5 waived. First live automated semver tag after DO CD.

## EV-019 — Ingest resilience (F47–F49)

**Cycle:** EV-019  
**Completed:** 2026-08-02  
**Session:** S022-ingest-resilience  
**PR:** [#179](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/179) @ `bd6bb00`  
**Report:** [evolve-summary](../sessions/S022-ingest-resilience/reports/evolve-summary.md) · [deploy-smoke](../sessions/S022-ingest-resilience/reports/deploy-smoke.md)  
**Notes:** Path A ship PASS; Path B store-backed `mode=rechunk` waived to follow-up (S022-D-path-b-waive).

## EV-012 — Unified Admin Jobs (F32/F36)

**Cycle:** EV-012  
**Completed:** 2026-07-29  
**Session:** S013-unified-job-monitoring  
**PR:** [#153](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/153) @ `6940770`  
**Report:** [evolve-report-EV-012.md](../evolve-report-EV-012.md) · [evolve-summary](../sessions/S013-unified-job-monitoring/reports/evolve-summary.md)

## EV-003 — Strict typing (no Any/any)

**Cycle:** EV-003  
**Completed:** 2026-05-27  
**Feature:** F30 — Strict static typing (no `Any` / `any`)

## Summary

Synchronized documentation, Cursor rules, skills, and CI references with the enforced no-`Any`/`any` toolchain already in the repo.

## Deliverables

| Artifact | Purpose |
|----------|---------|
| `docs/typing-policy.md` | Canonical typing policy and commands |
| `docs/adr/ADR-018-strict-typing-no-any.md` | Architecture decision |
| `.cursor/rules/strict-typing.mdc` | Agent guardrail (always apply) |
| `docs/decisions.md#evolve-cycle-decisions` | Cycle scope record |
| Updated specs | `execution-plan`, `test-plan`, `dependency-inventory`, `feature-list` F30 |
| Updated skills/rules | `09-qa`, `14-hotfix`, `06-tech-tooling`, `verify-build`, `ci-after-push` |

## Enforcement (unchanged config, now documented)

**Python:** Ruff `ANN401` + basedpyright `reportExplicitAny`  
**TypeScript:** ESLint `no-explicit-any` + `no-unsafe-*`; `strict` + `noImplicitAny`

## Verification

```bash
uv run ruff check apps packages tests
uv run basedpyright apps packages tests
cd apps/chat-rag-frontend && npm run lint
cd apps/data-management-frontend && npm run lint
```

## Tier 2 (completed in follow-up)

- **basedpyright `reportAny`** — enabled; SQL/HTTP boundaries use `db_mapping` + `json_types` helpers
- **ESLint `strictTypeChecked`** — enabled on production `src/**`; tests use relaxed overlay

See `docs/typing-policy.md`.

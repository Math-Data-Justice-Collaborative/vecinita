# Evolve cycle decisions

## EV-004 — Per-component unit coverage gate (F31)

**Date:** 2026-06-13  
**Status:** 04-tech-plan complete — 05-verify-tech next  
**Type:** Cross-cutting quality / CI

### Scope (approved)

Raise unit-test coverage to **≥95% line and ≥95% branch** on **each** of twelve monorepo components (`packages/*`, `apps/*`). Unit tests only. **Blocking CI.** Single milestone (all components before merge).

Baseline (2026-06-13): combined **61.0%** lines, **~42.9%** branches — largest gaps in backends and `data-management-frontend`.

### Artifacts

- `docs/feature-list.md` — F31
- `docs/test-plan.md` — Metrics, CI step, component baseline table
- `docs/acceptance-criteria.md` — AC-Q1–Q3
- `docs/requirements-decisions.md` — RD-053–RD-060
- `docs/adr/ADR-019-per-component-coverage-95.md`

### Routing

| Stage | Required |
|-------|----------|
| 01-requirements | Delta — complete |
| 02-verify-plan | Verify F31 statements vs ADR-019 | Complete 2026-06-13 |
| 04-tech-plan | Phase 9 tasks (T32–T36), TP-030–033 | Complete 2026-06-13 |
| 05-verify-tech | Verify tech statements vs execution plan | Next |
| 07-build | Tests + gate wiring |
| 08-verify-build | Confirm all twelve components pass |

Skipped unless drift: 03, 06, 12–13 (no deploy change).

---

## EV-003 — Strict typing (no Any/any)

**Date:** 2026-05-27  
**Status:** In progress  
**Type:** Cross-cutting tooling + documentation

### Scope (approved)

Align **documentation**, **Cursor rules/skills**, and **CI parity commands** with the enforced no-`Any`/`any` policy:

- Python: Ruff `ANN401` + basedpyright `reportExplicitAny`
- TypeScript: ESLint `no-explicit-any` + `no-unsafe-*`; `strict` / `noImplicitAny`

Out of scope: enabling basedpyright `reportAny` or ESLint `strictTypeChecked` preset (documented as deferred in typing-policy).

### Artifacts

- `docs/typing-policy.md` (canonical)
- `docs/adr/ADR-018-strict-typing-no-any.md`
- `.cursor/rules/strict-typing.mdc`
- Updates to `execution-plan.md`, `test-plan.md`, `dependency-inventory.md`, CI/skills references

### Routing

| Stage | Required |
|-------|----------|
| 01-requirements | Delta — F30 in feature-list |
| 02-verify-plan | Light — typing-policy statements |
| 04-tech-plan | Delta — tech stack row |
| 06-tech-tooling | Cursor rule + skill command sync |
| 07-build | Config already landed; doc sync only |
| 09-qa | Verify commands in qa skill |
| Deploy | Not required (docs/tooling only) |

# Evolve cycle decisions

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

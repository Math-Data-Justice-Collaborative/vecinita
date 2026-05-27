# Evolve report — EV-003 strict typing

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
| `docs/evolve-decisions.md` | Cycle scope record |
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

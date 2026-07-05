# 04-tech-plan — S008 eval UX + playground (EV-009 / F37)

**Session:** S008-eval-ux-playground  
**Evolve cycle:** EV-009 (F36 follow-ons + F37)  
**Date:** 2026-07-02  
**Status:** Complete — Phase 15 T2 gate PASS (2026-07-03, T70.8)

## Intent

Delta technical plan for four evaluation-page improvements from staging feedback: optimistic run
list, unified Jobs tab, dashboard chart controls, and eval Playground with super-admin runtime
promote.

## Interview resolutions (04-tech-plan batch)

| Topic | Decision | ID |
|-------|----------|-----|
| Items 1–3 scope | Approved as scoped in 01-requirements | RD-131 |
| Model v1 | Fixed Modal LLM; hyperparams + prompts only | RD-132 |
| Guardrails UI | Single `system_prompt` textarea | RD-133 |
| ChatRAG config read | Direct Postgres `rag_production_config` | RD-134 |
| Promote rollback | Forward-only; re-promote older preset/run | RD-135 |
| Playground layout | Two-column (config left, run/results right) | RD-136 |
| Default form values | Hardcoded defaults matching ChatRAG env | RD-137 |
| Jobs click nav | `/evaluation?run=<id>` | RD-138 |

## Technical decisions (TP-S008-01–16)

| ID | Decision |
|----|----------|
| TP-S008-01 | Build order M65→M70 on `feat/S008-eval-ux-playground` |
| TP-S008-02 | Optimistic prepend + in-place poll status (FE only) |
| TP-S008-03 | Unified jobs via DM backend HTTP aggregation of eval runs |
| TP-S008-04 | Dashboard scatter + time presets — FE filter on existing timeseries |
| TP-S008-05 | `eval_config_presets` + `rag_production_config` tables; `EvalConfig` validation bounds |
| TP-S008-06 | No model picker v1 — Qwen2.5 Modal LLM only |
| TP-S008-07 | Sandbox overrides in eval runner only until promote |
| TP-S008-08 | Presets private default; share-read clone for other admins |
| TP-S008-09 | Playground `?tab=playground` two-column UI |
| TP-S008-10 | `super-admin` role seeded from `VECINITA_SUPER_ADMIN_EMAIL` |
| TP-S008-11 | Forward-only promote with `config_version` history |
| TP-S008-12 | ChatRAG reads `rag_production_config` via `DATABASE_URL` |
| TP-S008-13 | Eval job row → `/evaluation?run=<id>` |
| TP-S008-14 | TC-123–TC-133 + Playwright uj044/uj045 |
| TP-S008-15 | No new Python runtime deps |
| TP-S008-16 | Deploy: migration → write-api → DM backend → chat-rag → admin FE |

## Execution plan delta

**Phase 15** appended — 6 milestones, 38 tasks (T65.1–T70.8):

| Milestone | Focus | Feature |
|-----------|-------|---------|
| M65 | Optimistic run list + poll UX | F36 follow-on |
| M66 | Unified jobs API + Jobs tab `eval` | F36 follow-on |
| M67 | Dashboard scatter + time-range presets | F36 follow-on |
| M68 | Config schema + preset API + DB | F37 |
| M69 | Playground UI (golden + ad-hoc + compare) | F37 |
| M70 | Super-admin promote + ChatRAG config reader | F37 |

## Artifacts produced

| Artifact | Path |
|----------|------|
| ADR | `docs/adr/ADR-035-ev009-eval-playground-production-config.md` |
| Execution plan | `docs/sessions/S000-internal-docs-archive/execution-plan.md` — Phase 15, Current State, PR-51 |
| Decisions log | `docs/decisions.md` — TP-S008-01–16, RD-131–138 |
| Config spec | `docs/config-spec.md` — `EvalConfig` validation bounds |
| Staging secrets | `docs/staging-secrets-matrix.md` — `VECINITA_SUPER_ADMIN_EMAIL` |
| Context brief | `docs/sessions/S000-internal-docs-archive/context/eval-ux-playground.md` — gaps closed |

## Phase 15 gate close-out (T70.8 — 2026-07-03)

| Gate item | Result |
|-----------|--------|
| M65–M70 tasks | Complete (T65.1–T70.8) |
| TC-123–TC-133 / UJ-044–047 | Green at T2 |
| AC-E22–AC-E26 | Met at T2 |
| Migrations + privacy | `eval_config_presets`, `rag_production_config` — green |
| Python deps | No new runtime deps (ADR-035 §178) |
| CORS EV-009 | Preflight tests for presets, rag/config, ollama routes |
| Lint / typecheck / tests | Backend + DM-frontend suites green |

Full evidence: [phase-15-gate-check.md](./phase-15-gate-check.md).

**T3 pending:** live promote smoke (13-deploy-smoke); PR-51 merge + CI on `main`.

## Handoff

**Next stage:** **08-verify-build** (formal phase verify) → 09-qa → 10-e2e → re-invoke 11-verify-impl for M70/UJ-047.

**Coordinate:** S007 deploy stages 12–13 remain deferred on S007 backlog; S008 does not block.

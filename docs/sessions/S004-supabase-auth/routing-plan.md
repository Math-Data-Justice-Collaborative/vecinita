# S004 — Routing Plan (evolve, lite)

Approved by user 2026-06-28 (AskQuestion: routing=lite, first_step=handoff to 01-requirements).

Cycle **EV-005** · Feature **F34** (Supabase admin auth) · Issue **#75**.

| Stage | Status | Note |
|-------|--------|------|
| 00-context | in_progress | Session opener; 5 gating decisions resolved; context-brief §15 delta; S003 closed |
| 01-requirements | pending | F34 spec, user journeys (admin login / invite), AC, **superseding ADR** for ADR-004 auth clause |
| 04-tech-plan | pending | Supabase Auth integration, JWT verify middleware (FastAPI), invite flow, role model, env branching, secrets, CORS, cost estimate |
| 07-build | pending | Implement across DM frontend + DM backend + internal-write-api; Supabase migrations/config |
| 08-verify-build | pending | Milestone verify (lint/type/test/coverage) |
| 09-qa | pending | Full QA: authn/authz unit + integration; privacy tests (corpus DB still PII-free) |
| 10-e2e | pending | E2E: login, protected route redirect, invite acceptance, role gating, 401/403 at APIs |
| 12-verify-deploy | pending | Pre-deploy gate: Supabase secrets, CORS preflight (Authorization), env branching |
| 13-deploy-smoke | pending | Deploy + H1–H5 smokes with auth gates |

## Skipped stages (lite path — user-approved 2026-06-28)

| Stage | Reason |
|-------|--------|
| 02-verify-plan | Lite path |
| 03-plan-tooling | Lite path — auth guardrail rules folded into 04 + 07 |
| 05-verify-tech | Lite path |
| 06-tech-tooling | Lite path |
| 11-verify-impl | Lite path — covered by 09-qa + 10-e2e |

## Approved
User approval recorded: 2026-06-28

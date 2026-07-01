# Routing plan — S006-invite-acceptance

| Stage | Required | Mode | Skip rationale |
|-------|----------|------|----------------|
| 00-context | yes | scoped delta | Issue #109 analysis + scoped brief — **this session** |
| 01-requirements | yes | delta | Revise AC-U3, extend UJ-031, new TCs, api-contract `redirect_to` |
| 04-tech-plan | yes | delta | ADR-032; TP-S006-01–16; Phase 13 M54–M58 — **completed** ([report](./reports/04-tech-plan.md)) |
| 07-build | yes | full | Backend redirect_to, FE callback hook, revoke endpoint, config.toml, template polish |
| 08-verify-build | yes | full | Milestone gate |
| 09-qa | yes | full | Full-repo QA |
| 10-e2e | yes | full | Invite-accept e2e (hash error + happy path) |
| 12-verify-deploy | yes | full | Supabase config push + `VECINITA_ADMIN_FRONTEND_URL` |
| 13-deploy-smoke | yes | full | Live invite smoke (T3 deferred from S005) |
| 02-verify-plan | no | — | Evolve-lite; standing specs mature |
| 03-plan-tooling | no | — | Evolve-lite; no new tooling |
| 05-verify-tech | no | — | Evolve-lite |
| 06-tech-tooling | no | — | Evolve-lite |
| 11-verify-impl | no | — | Evolve-lite; 10-e2e + 13-deploy-smoke cover impl verify |

## Orchestrator

**16-evolve** (EV-007 — F35 extension from EV-006)

## Branch

`feat/S006-invite-acceptance`

## Approved

User approval recorded: 2026-06-30

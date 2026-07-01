# 01-requirements — S006 invite acceptance (EV-007 / #109)

**Session:** S006-invite-acceptance  
**Evolve cycle:** EV-007 (F35 extension)  
**Date:** 2026-06-30  
**Status:** Complete

## Intent

Delta requirements interview for GitHub [#109](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/109) — complete the production invite acceptance flow that S005/EV-006 scaffolded but did not verify end-to-end.

## Document manifest

| Document | Action |
|----------|--------|
| feature-list.md | Delta — F35.12–F35.15 |
| user-journeys.md | Delta — UJ-030, UJ-031, UJ-033 |
| test-plan.md | Delta — TC-104–TC-110 |
| acceptance-criteria.md | Delta — AC-U3/U5 revised; AC-U17–AC-U21 added |
| api-contract.md | Delta — `redirect_to`, `POST /admin/users/{id}/revoke-invite` |
| config-spec.md | Delta — `VECINITA_ADMIN_FRONTEND_URL` on Modal DM |
| deployment-integration.md | Delta — §EV-007 redirect chain + redeploy order |

Skipped: spec.md (no architecture change), dependency-inventory (no new deps), README (no greenfield).

## Interview decisions

| ID | Decision |
|----|----------|
| RD-091 | Keep Supabase SMTP for invite/recovery mail (R60) |
| RD-092 | `POST /admin/users/{id}/revoke-invite` + distinct UI (R61) |
| RD-093 | Backend `redirect_to` on invite/resend/admin recovery |
| RD-094 | Staging-first `site_url` strategy |
| RD-095 | Explicit auth callback handling on accept/reset pages |
| RD-096 | Show `invited_at` + "~1h expiry" on pending rows |
| RD-097 | Template copy/branding polish in this cycle |
| RD-098 | T2 mocked callback + T3 live smoke at 13-deploy-smoke |

## Key gaps closed

- AC-U3 was API-only verified — now requires full browser journey (T2 + T3).
- ADR-030 §5 assumption (`detectSessionInUrl` sufficient) invalidated — noted for 04-tech-plan (ADR-032 amend).

## Handoff

**Next stage:** 04-tech-plan (evolve-lite — 02/03/05/06 skipped per routing plan).

Artifacts: ADR-032 or ADR-030 amend; execution-plan Phase 13 tasks; Modal secrets matrix update for `VECINITA_ADMIN_FRONTEND_URL`.

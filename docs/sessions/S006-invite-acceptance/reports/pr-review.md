# PR review — S006 / PR #110

**Date:** 2026-06-30  
**Reviewer:** 18-pr-review (agent)  
**PR:** [#110 — Phase 13: EV-007 Invite acceptance flow](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/110)  
**Branch:** `feat/S006-invite-acceptance` → `main`  
**Head SHA:** `1817c2a`  
**Verdict:** **Request changes** (1 blocker, 3 advisories)

## Summary

Strong EV-007 delivery: server-built `redirect_to`, revoke-invite with audit, bilingual callback UX, ADR-032, and broad TC-104–TC-110 coverage. Remote CI green on HEAD. One confirmed PKCE race in `useAuthLinkCallback` can show invalid-link UI on valid invite emails.

## CI

| Workflow | Result |
|----------|--------|
| `ci.yml` @ `1817c2a` | success (python, frontend×2, packages×2, coverage) |

## Subagents

| Agent | Result |
|-------|--------|
| Bugbot | 1 high — PKCE / `detectSessionInUrl` race |
| Security review | No medium+ findings |

## Blockers

1. **PKCE double-exchange race** (`useAuthLinkCallback.ts:67-76`) — manual `exchangeCodeForSession` can fail after singleton client already consumed the code via `detectSessionInUrl`, overwriting a valid `ready` state with `invalid`.

## Advisories

1. **🟡 [Staff Frontend]** Vitest PKCE tests use isolated `renderHook`; add coverage with `AuthProvider` mounted to catch the race.
2. **🟡 [Senior DevOps]** AC-U17–U21 staging checks deferred to 13-deploy-smoke (acknowledged in PR body).
3. **🟡 [CTO]** Large `workflow-state.yaml` churn in PR — consider separating session bookkeeping from feature commits in future.

## Praise

- Server-side `redirect_to` from `VECINITA_ADMIN_FRONTEND_URL` closes the localhost redirect gap (#109).
- Revoke-invite is invited-only with audit `user.invite_revoked` and OpenAPI/CORS coverage.
- ADR-032 and session artifacts trace requirements through implementation.
- TDD discipline: TC-104–TC-110 with e2e `redirect_to` assertion on invite outbound.

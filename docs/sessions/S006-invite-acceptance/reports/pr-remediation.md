# PR remediation — S006 / PR #110 (PRM-010)

**Date:** 2026-06-30  
**Cycle:** PRM-010 (linked PRR-012)  
**PR:** [#110 — Phase 13: EV-007 Invite acceptance flow](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/110)  
**Branch:** `feat/S006-invite-acceptance` → `main`

## Findings backlog

| ID | Severity | Item | Status |
|----|----------|------|--------|
| F-001 | 🔴 blocker | PKCE double-exchange race (`useAuthLinkCallback.ts`) | fixed (local) |
| F-002 | 🟡 advisory | AuthProvider + SetPasswordPage integration test for race | fixed (local) |
| F-003 | 🟡 advisory | AC-U17–U21 staging checks deferred to 13-deploy-smoke | pending triage |
| F-004 | 🟡 advisory | Large `workflow-state.yaml` churn — separate commits in future | pending triage |

## F-001 fix

**Approach:** Session re-check — skip manual exchange when session already exists; on exchange error, call `getSession()` before marking `invalid`.

**Files:**
- `apps/data-management-frontend/src/auth/useAuthLinkCallback.ts`
- `docs/bug-reports/BUG-2026-06-30-pkce-double-exchange-race.md`
- `apps/data-management-frontend/src/test/test_bug_2026_06_30_pkce_double_exchange_race.test.tsx`
- `apps/data-management-frontend/src/test/test_auth_link_callback.test.tsx` (happy-path mock adjusted)

## Verification

- Vitest: `test_bug_2026_06_30_pkce_double_exchange_race.test.tsx` — 2/2 pass
- Vitest: `test_auth_link_callback.test.tsx` — 10/10 pass
- ESLint: pass

## CI

- `ci.yml` @ `b334f77`: success (python, frontend×2, packages×2, coverage)

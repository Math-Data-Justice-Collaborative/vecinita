# 08-verify-build — S006 / EV-007 (#109)

> **Generated:** 2026-06-30  
> **Scope:** Phase 13 — Invite acceptance flow (F35 ext, M54–M58)  
> **Branch:** `feat/S006-invite-acceptance`  
> **Session:** S006-invite-acceptance

## Summary

| Check | Status | Notes |
|-------|--------|-------|
| Ruff lint + format (Python) | **PASS** | 0 errors |
| basedpyright (Python) | **PASS** | 0 errors |
| ESLint (admin FE) | **PASS** | 0 errors |
| pytest (unit/integration/e2e/smoke/bugs) | **PASS** | full suite green |
| Vitest (admin FE) | **PASS** | 329 tests |
| Coverage gate (admin FE branches) | **PASS** | 95.21% (after TC-106 hook coverage) |
| CORS H0c (`test_cors_policy.py`) | **PASS** | includes revoke-invite preflight |
| Integration H0i | **PASS** | user admin routes + redirect_to |

**Overall: PASS**

## Phase 13 gate (T2 — merge-blocking)

- [x] T54.1–T54.24 implemented with atomic commits
- [x] TC-104–TC-110 covered in pytest + Vitest
- [ ] AC-U17–U21 live verify — **deferred to 13-deploy-smoke** (requires staging Supabase config push + live invite)

## Deliverables (#109)

1. **Redirect URLs** — `VECINITA_ADMIN_FRONTEND_URL` + `redirect_to` on invite/resend/recovery; staging-first `supabase/config.toml`
2. **Auth callback** — `useAuthLinkCallback` gates password form; bilingual expired/denied/invalid UX
3. **Admin lifecycle** — `POST /admin/users/{id}/revoke-invite` + UsersPage retract + invite metadata
4. **Templates / runbook** — TC-110 contract; EV-007 redeploy order in staging runbook

## Next

- **09-qa** → **12-verify-deploy** → **13-deploy-smoke** (live invite acceptance on staging)

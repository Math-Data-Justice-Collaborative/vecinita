# E2E Behavior Report — S005 Admin User Management + Auth UX

> **Generated**: 2026-06-30  
> **Session**: S005-user-mgmt-auth  
> **Mechanism**: API + Frontend (pytest `TestClient`; Vitest)  
> **Branch**: `feat/S005-user-mgmt-auth`  
> **Scope**: EV-006 / F35 — UJ-030–UJ-038 (admin user management + auth UX) + regression on UJ-001–UJ-029  
> **Journeys tested**: 38 (full index through UJ-038)

## Summary

| Tier | Command | Result |
|------|---------|--------|
| **T0** | `uv run pytest tests/e2e/ -m "e2e and not live"` | **68 passed**, 0 failed |
| **T1** | `uv run pytest tests/integration/` | **62 passed**, 0 failed |
| **Supabase contract** | `uv run pytest tests/smoke/test_supabase_ci_contract.py` | **14 passed**, 0 failed |
| **T3 live** | `tests/smoke/test_staging_*.py -m live` | **NOT RUN** — F35 not deployed; `VECINITA_STAGING_*` unset |
| **FE Vitest** | both frontends + shared packages | **483 passed** (admin 312, chat 142, i18n 17, ui 12) |

| # | Journey | Mechanism | T0 | T3 | Status |
|---|---------|-----------|----|----|--------|
| 30 | **UJ-030 Admin user management** | API + Vitest | **PASS** | pending | List/role/resend/disable/revoke/reset; viewer 403 |
| 31 | **UJ-031 Invite from page** | API | **PASS** | pending | Invite endpoint + audit; live email at 13 |
| 32 | **UJ-032 Remember-me** | Vitest | **PASS** | waived | localStorage/sessionStorage routing |
| 33 | **UJ-033 Password reset** | Vitest | **PASS** | pending | Forgot password + in-app reset |
| 34 | **UJ-034 Idle timeout** | Vitest | **PASS** | waived | Warning modal + local signOut |
| 35 | **UJ-035 Log out all devices** | Vitest | **PASS** | waived | Global vs local signOut scope |
| 36 | **UJ-036 Force sign-out** | API + Vitest | **PASS** | pending | Admin 202; viewer 403; RPC-absent 503 |
| 37 | **UJ-037 Test email send** | API + Vitest | **PASS** | pending | Resend mocked; live at 13 |
| 38 | **UJ-038 Audit user events** | Vitest | **PASS** | waived | Users filter + per-user link |
| 1–29 | UJ-001–UJ-029 | mixed | **PASS** | pending/waived | No regressions vs S004 baseline |

**Overall T0: PASS** — 68/68 API e2e + 62 integration + 483 Vitest + 14 Supabase contract  
**Overall T3: NOT RUN** — deferred to 13-deploy-smoke / 15-service-health post-deploy

---

## EV-006 delta journeys (F35)

### UJ-030: Admin manages operators from the User Management page

- **Feature**: F35.1, F35.9
- **Test modules**: `tests/e2e/test_uj030_user_management.py` (3 tests); `test_users_page.test.tsx`, `test_users_viewer_blocked.test.tsx`, `test_users_search.test.tsx`
- **Steps verified (T0)**:
  1. Admin list + role/resend/disable/revoke/reset → Supabase Admin API — **PASS**
  2. Viewer 403 on all `/admin/users*` writes — **PASS**
  3. Audit attribution opaque UUID + role — **PASS**
  4. Search (`q` ≥3 chars) + pagination — **PASS** (Vitest)

### UJ-031: Admin invites an operator from the User Management page

- **Feature**: F35.1
- **Test module**: `tests/e2e/test_uj031_invite_from_page.py` (2 tests)
- **Steps verified (T0)**:
  1. `POST /admin/users/invite` → role assignment + audit — **PASS**
  2. Public self-signup remains disabled (extends UJ-027) — **PASS**
- **T3**: Live invite email via Resend deferred to 13-deploy-smoke

### UJ-032: Stay signed in with "Remember me"

- **Feature**: F35.2
- **Test module**: `test_remember_me.test.tsx`
- **Steps verified (T0)**: Default checked; localStorage vs sessionStorage; `vecinita.auth.remember` — **PASS**

### UJ-033: Operator resets a forgotten password

- **Feature**: F35.3
- **Test module**: `test_password_reset.test.tsx`
- **Steps verified (T0)**: Forgot password form; reset page; generic confirmation — **PASS**

### UJ-034: Idle timeout

- **Feature**: F35.7
- **Test module**: `test_idle_timeout.test.tsx`
- **Steps verified (T0)**: Warning at threshold; activity reset; `signOut({scope:"local"})` — **PASS**

### UJ-035: Log out of all devices

- **Feature**: F35.8
- **Test module**: `test_logout_all_devices.test.tsx`
- **Steps verified (T0)**: Global vs local signOut — **PASS**

### UJ-036: Admin force-signs-out another operator

- **Feature**: F35.8
- **Test modules**: `tests/e2e/test_uj036_force_signout.py` (2); `test_force_signout.test.tsx`
- **Steps verified (T0)**: Admin 202 + audit; viewer 403; RPC-absent 503 + UI fallback — **PASS**

### UJ-037: Deliverability test-send

- **Feature**: F35.11
- **Test modules**: `tests/e2e/test_uj037_email_test_send.py` (2); `test_email_test_send_ui.test.tsx`
- **Steps verified (T0)**: Admin 202 + message_id; viewer 403; unconfigured 503; rate limit 429; audit domain-only — **PASS**

### UJ-038: Audit viewer for user events

- **Feature**: F35.10
- **Test module**: `test_audit_user_events.test.tsx`
- **Steps verified (T0)**: Users entity filter; friendly labels; per-user link — **PASS**

---

## Regression spot-check (UJ-001–UJ-029)

All prior API e2e modules pass without change. Notable F34 auth modules still green:

| Module | Tests | Journey |
|--------|-------|---------|
| `test_uj028_unauthenticated_admin.py` | 9 | UJ-028 |
| `test_uj029_role_gating.py` | 4 | UJ-029 |
| `test_uj027_invite_only_registration.py` | 1 | UJ-027 |
| `test_uj023_job_management.py` | 4 | UJ-023 |

---

## Connectivity Matrix

| Column | Status | Evidence |
|--------|--------|----------|
| T0 in-process | **PASS** | 68 e2e + 62 integration + 483 Vitest + 14 Supabase contract |
| T2 connectivity (H4–H5) | **NOT RUN** | Staging env vars unset; F35 not deployed |
| T3 browser | **NOT RUN** | Deferred to 13-deploy-smoke / 15-service-health |

**Important:** T0 PASS does **not** prove live Supabase invite emails, Resend delivery, or production JWT flows — T3 required after deploy.

---

## Commands run

```bash
uv run pytest tests/e2e/ -m "e2e and not live" -v          # 68 passed
uv run pytest tests/integration/ -v                         # 62 passed
uv run pytest tests/smoke/test_supabase_ci_contract.py -v   # 14 passed
cd apps/data-management-frontend && npm test -- --run       # 312 passed
cd apps/chat-rag-frontend && npm test -- --run              # 142 passed
npm test -w vecinita-frontend-i18n && npm test -w vecinita-frontend-ui  # 17 + 12
```

**Environment:** `feat/S005-user-mgmt-auth`; no `VECINITA_STAGING_*` env vars set.

## Handoff

- **11-verify-impl**: User approved UJ-030–UJ-038 + F35; formal 10-e2e now complete.
- **12-verify-deploy**: Resend SMTP secrets, Supabase config push, staging URL refresh.
- **13-deploy-smoke**: Live invite/recovery email, T3 auth journeys, H4–H5 connectivity.

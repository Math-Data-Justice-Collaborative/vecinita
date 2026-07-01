# E2E Behavior Report — S006 Invite Acceptance Flow

> **Generated**: 2026-06-30  
> **Session**: S006-invite-acceptance  
> **Mechanism**: API + Frontend (pytest `TestClient`; Vitest)  
> **Branch**: `feat/S006-invite-acceptance`  
> **Scope**: EV-007 / F35 ext (#109) — invite acceptance redirect, auth callback, revoke-invite + regression on UJ-001–UJ-038  
> **Journeys tested**: 38 (full index through UJ-038)

## Summary

| Tier | Command | Result |
|------|---------|--------|
| **T0** | `uv run pytest tests/e2e/ -m "e2e and not live"` | **69 passed**, 0 failed |
| **T1** | `uv run pytest tests/integration/` | **62 passed**, 0 failed |
| **Supabase contract** | `uv run pytest tests/smoke/test_supabase_ci_contract.py` | **17 passed**, 0 failed |
| **T3 live** | `tests/smoke/test_staging_*.py -m live` | **NOT RUN** — S006 not deployed; live invite/recovery email deferred to 13-deploy-smoke |
| **FE Vitest** | both frontends + shared packages | **500 passed** (admin 329, chat 142, i18n 17, ui 12) |

| # | Journey | Mechanism | T0 | T3 | Status |
|---|---------|-----------|----|----|--------|
| 31 | **UJ-031 Invite from page + accept callback** | API + Vitest | **PASS** | pending | `redirect_to=/accept-invite` (TC-104); hash/code session + `#error=otp_expired` UX (TC-106) |
| 33 | **UJ-033 Password reset callback** | Vitest | **PASS** | pending | Forgot password + `/reset-password` callback (TC-107); admin reset `redirect_to` (TC-105) |
| 30 | **UJ-030 Admin user management** | API + Vitest | **PASS** | pending | Includes revoke-invite (TC-108); no regressions |
| 1–29, 32, 34–38 | UJ-001–UJ-029, UJ-032, UJ-034–UJ-038 | mixed | **PASS** | pending/waived | No regressions vs S005 baseline |

**Overall T0: PASS** — 69/69 API e2e + 62 integration + 500 Vitest + 17 Supabase contract  
**Overall T3: NOT RUN** — deferred to 13-deploy-smoke / 15-service-health post-deploy

---

## EV-007 delta journeys (F35 ext)

### UJ-031: Admin invites from User Management; invitee accepts

- **Feature**: F35.12–F35.15 (EV-007)
- **Test modules**:
  - `tests/e2e/test_uj031_invite_from_page.py` (3 tests)
  - `apps/data-management-frontend/src/test/test_auth_link_callback.test.tsx` (TC-106)
- **Steps verified (T0)**:
  1. `POST /admin/users/invite` → role assignment + audit — **PASS** (TC-090)
  2. Outbound GoTrue call includes `redirect_to=…/accept-invite` — **PASS** (TC-104, **new in S006**)
  3. Public self-signup remains disabled — **PASS** (TC-080 regression)
  4. `/accept-invite` gates password form until session from hash/code — **PASS** (TC-106)
  5. `#error=otp_expired` shows bilingual actionable error (not blank page) — **PASS** (TC-106)
- **T3**: Live invite email via Resend + cross-origin redirect chain deferred to **13-deploy-smoke**

### UJ-033: Operator resets a forgotten password

- **Feature**: F35.3 (callback polish in EV-007)
- **Test modules**:
  - `apps/data-management-frontend/src/test/test_auth_link_callback.test.tsx` (TC-107)
  - `apps/data-management-frontend/src/test/test_password_reset.test.tsx`
- **Steps verified (T0)**:
  1. Forgot-password form calls `resetPasswordForEmail` with `redirectTo={origin}/reset-password` — **PASS**
  2. `/reset-password` waits for session before password form — **PASS** (TC-107)
  3. Expired/invalid link shows bilingual error — **PASS**
  4. Generic confirmation (no email enumeration) — **PASS**
- **T3**: Live recovery email delivery deferred to **13-deploy-smoke**

### UJ-030: Admin user management (regression + revoke)

- **Feature**: F35.1, F35.9
- **Test modules**: `tests/e2e/test_uj030_user_management.py`; Vitest user-management suite
- **Steps verified (T0)**: List/role/resend/**revoke-invite**/disable/reset; viewer 403; audit non-PII — **PASS** (TC-108 revoke covered in build/QA; no T0 regression)

---

## Regression spot-check (UJ-001–UJ-029, UJ-032, UJ-034–UJ-038)

All prior API e2e modules pass without change. Notable modules still green:

| Module | Tests | Journey |
|--------|-------|---------|
| `test_uj031_invite_from_page.py` | 3 | UJ-031 (+1 vs S005) |
| `test_uj030_user_management.py` | 3 | UJ-030 |
| `test_uj028_unauthenticated_admin.py` | 9 | UJ-028 |
| `test_uj029_role_gating.py` | 4 | UJ-029 |
| `test_uj036_force_signout.py` | 2 | UJ-036 |
| `test_uj037_email_test_send.py` | 2 | UJ-037 |

---

## Connectivity Matrix

| Column | Status | Evidence |
|--------|--------|----------|
| T0 in-process | **PASS** | 69 e2e + 62 integration + 500 Vitest + 17 Supabase contract |
| T2 connectivity (H4–H5) | **PASS (QA)** | H4/H5 live 19 passed during 09-qa (`verify_connectivity.sh`); not re-run in 10-e2e |
| T3 browser / live auth | **NOT RUN** | S006 branch not deployed; invite/recovery email E2E deferred to 13-deploy-smoke |

**Important:** T0 PASS does **not** prove live Supabase invite emails, Resend delivery, or production redirect allowlist — T3 required after deploy + `supabase config push`.

---

## Commands run

```bash
uv run pytest tests/e2e/ -m "e2e and not live" -q          # 69 passed
uv run pytest tests/integration/ -q                         # 62 passed
uv run pytest tests/smoke/test_supabase_ci_contract.py -q   # 17 passed
cd apps/data-management-frontend && npm test -- --run       # 329 passed
cd apps/chat-rag-frontend && npm test -- --run              # 142 passed
npm test -w vecinita-frontend-i18n && npm test -w vecinita-frontend-ui  # 17 + 12
# S006 focus:
npm test -- --run test_auth_link_callback.test.tsx test_password_reset.test.tsx  # 19 passed
```

**Environment:** `feat/S006-invite-acceptance@b81a019`; no `VECINITA_STAGING_*` live auth env vars set for T3.

## Handoff

- **12-verify-deploy**: Supabase `config push` (`site_url`, redirect allowlist), `VECINITA_ADMIN_FRONTEND_URL`, Resend SMTP.
- **13-deploy-smoke**: Live invite smoke (TC-104 live, TC-109), recovery email, T3 auth journeys, H4–H5 regression on redeployed admin frontend.

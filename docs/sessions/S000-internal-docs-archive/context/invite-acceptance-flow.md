# Context Brief — Invite Acceptance Flow (S006 / #109)

**Stage:** 00-context (scoped delta)  
**Session:** S006-invite-acceptance  
**Evolve cycle:** EV-007 (F35 extension from EV-006)  
**Date:** 2026-06-30  
**Status:** Complete  
**Issue:** [GitHub #109](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/109)

---

## 1. Executive Summary

S005/EV-006 (F35) delivered the **scaffold** for operator user management — invite API,
`/users` admin UI, Resend SMTP wiring, and bilingual Supabase email templates — but the
**end-to-end invite acceptance flow fails in staging/production**. Invitee email links redirect
to `http://localhost:3000/#error=access_denied&error_code=otp_expired` instead of the admin
frontend `/accept-invite` page, and invitees cannot set a password.

Root causes are confirmed in code: backend never passes `redirect_to` on GoTrue invite/resend/recovery
calls; live Supabase `site_url` may still default to `localhost:3000`; frontend `SetPasswordPage`
calls `updateUser({ password })` without establishing a session from the email link hash/code.
S005 marked UJ-031 / AC-U3 verified at the **API layer only**; live browser onboarding was
deferred to 13-deploy-smoke and never executed.

This brief scopes EV-007 work to close the production onboarding gap per #109.

---

## 2. Multi-App Topology & Browser Integration Risk

| Deployable | Host (staging) | Role in invite flow |
|------------|----------------|---------------------|
| **Admin frontend** | `vecinita-admin-frontend-*.ondigitalocean.app` | `/accept-invite`, `/reset-password` — **email link landing** |
| **DM backend (Modal)** | `*.modal.run` | `POST /admin/users/invite`, resend, revoke, recovery — **must pass `redirect_to`** |
| **Supabase GoTrue** | `*.supabase.co` | Sends invite email; builds `ConfirmationURL` from `site_url` + `redirect_to` |
| **Resend SMTP** | External | Delivers GoTrue-generated mail (R60: keep SMTP, not REST API) |

**Browser integration risk (HIGH):** Invite flow is a **cross-origin redirect chain**:
GoTrue → admin frontend hash fragment (`#access_token=…` or `#error=otp_expired`). Unlike API
CORS (already configured for admin FE → Modal), this flow depends on:

1. Correct `site_url` and redirect allowlist on the **live Supabase project** (not just repo `config.toml`)
2. Backend `redirect_to={ADMIN_FRONTEND_URL}/accept-invite` on every invite/resend
3. Frontend explicit callback handling — `detectSessionInUrl: true` alone is insufficient when
   redirect URL or host is wrong (ADR-030 §5 assumption invalidated)

**Connectivity gates:** H4/H5 prove API reachability; **H6 browser UJ** required for invite accept
(T3 deferred from S005 → S006 13-deploy-smoke).

---

## 3. Resolution Log (S006)

| ID | Category | Issue | Resolution |
|----|----------|-------|------------|
| R60 | Decision | Invite mail channel | **Supabase-managed mail via Resend SMTP** (`config.toml`) — not Resend REST API |
| R61 | Decision | Retract invitation | **New `POST /admin/users/{id}/revoke-invite`** + distinct UI + audit `user.invite_revoked` |
| R62 | Decision | Context brief location | **Scoped brief** at `docs/sessions/S000-internal-docs-archive/context/invite-acceptance-flow.md` (this file) |
| R63 | Assumed | `additional_redirect_urls` shape | Include **full paths** (`…/accept-invite`, `…/reset-password`) plus dev origins — verify after backend `redirect_to` wired |
| R64 | Assumed | Feature ID | **F35 extension** under EV-007 (not new F36) — extends UJ-031 / AC-U3 |

---

## 4. Source Analysis — Issue #109

### Problem statement

- Email link lands on `localhost:3000` (wrong host)
- Hash shows `otp_expired` / `access_denied` even on fresh invites
- `/accept-invite` exists but no session established before password form
- Admins cannot retract pending invitations or see invite lifecycle clearly

### Proposed scope (from issue)

1. Redirect URL wiring (backend + Supabase config)
2. Frontend invite/recovery callback pages
3. Email template improvements (low priority)
4. Admin invitation lifecycle (retract, resend with correct URLs)
5. Email verification behavior with `enable_confirmations = true`

### Acceptance criteria (#109)

- Fresh invite opens staging admin `/accept-invite`, not `localhost:3000`
- Invitee sets password and logs in with assigned role
- Expired link shows in-app bilingual error + actionable next step
- Admin can retract pending invite and resend with working link
- Supabase `site_url` + redirect allowlist match deployed URLs
- Tests cover backend `redirect_to`, frontend callback, e2e invite-accept

---

## 5. Codebase Gap Analysis

### 5.1 Backend — `user_admin_routes.py`

**Path:** `apps/data-management-backend/vecinita_data_management_backend/user_admin_routes.py`

| Endpoint | Current | Gap |
|----------|---------|-----|
| `POST /admin/users/invite` | `invite_user_by_email(body.email)` | No `redirect_to` |
| `POST /admin/users/{id}/resend-invite` | `invite_user_by_email(target.email)` | No `redirect_to` |
| `POST /admin/users/{id}/reset-password` | `send_password_recovery(target.email)` | No `redirect_to` |

**Reference pattern:** `ForgotPasswordPage.tsx` correctly uses
`window.location.origin + '/reset-password'` for self-service recovery.

**Infra gap:** `VECINITA_ADMIN_FRONTEND_URL` exists in `infra/do/.env.example` (internal-write-api
health only) but **not** on Modal DM backend secrets.

### 5.2 GoTrue client — `supabase_admin.py`

**Path:** `packages/shared-schemas/vecinita_shared_schemas/supabase_admin.py`

Client **supports** optional `redirect_to` on `invite_user_by_email`, `send_password_recovery`,
and `generate_link` — call sites simply never pass it. Unit test passes `redirect_to` but does
not assert query param on outbound request.

### 5.3 Frontend — `SetPasswordPage.tsx` + `App.tsx`

**Paths:**

- `apps/data-management-frontend/src/pages/SetPasswordPage.tsx`
- `apps/data-management-frontend/src/App.tsx`

| Capability | Status |
|------------|--------|
| Routes `/accept-invite`, `/reset-password` public | Done |
| Parse hash/query (`access_token`, `code`, `#error=…`) | Missing |
| Wait for session before password form | Missing |
| Bilingual expired-link UX | Missing |
| `updateUser({ password })` on submit | Done (but runs without session) |

Auth stack: `detectSessionInUrl: true` in `supabaseClient.ts`; `AuthContext` uses `getSession()` +
`onAuthStateChange` — no invite-specific callback logic.

### 5.4 Supabase config — `supabase/config.toml`

| Setting | Repo value | Production risk |
|---------|------------|-----------------|
| `site_url` | `http://127.0.0.1:5173` | Live project may still be `localhost:3000` |
| `additional_redirect_urls` | Staging DO origin + local dev | May need full `/accept-invite` paths |
| `otp_expiry` | `3600` (1 h) | Resend is operator workaround (ADR-030 §7) |
| `enable_confirmations` | `true` | Invite flow should confirm email — verify in staging |

CI: `.github/workflows/supabase.yml` runs `config push` on `main` when token set.

### 5.5 Email template — `supabase/templates/invite.html`

Template uses `{{ .ConfirmationURL }}` and "expires in 1 hour" copy. **Adequate for v1**; broken
links are upstream (wrong `site_url`, missing `redirect_to`), not template HTML.

### 5.6 Tests — coverage gaps

| Test | Proves | Does not prove |
|------|--------|----------------|
| `test_uj031_invite_from_page.py` | API invite + audit | Email link, redirect, frontend accept |
| `test_password_reset.test.tsx` | Form validation + `updateUser` | Hash callback, `#error=otp_expired` |
| `test_supabase_admin.py` invite | POST `/auth/v1/invite` | `redirect_to` query param asserted |
| S005 e2e-report | UJ-031 PASS at T0 | T3 live invite **deferred** |

**AC-U3 is overstated:** marked verified via API tests only; #109 acceptance requires full journey.

### 5.7 Admin UI — retract invitation

`UsersPage.tsx` has "Delete" for all users. No distinct "Retract invitation" for `status=invited`.
R61: new revoke endpoint + UI label.

---

## 6. Cross-Reference Matrix

| Topic | Issue #109 | Code | ADR-030 | S005 e2e | Align? |
|-------|------------|------|---------|----------|--------|
| `redirect_to` on invite | Required | Missing | Not specified | N/A | Gap |
| `detectSessionInUrl` sufficient | Insufficient | Assumed yes | §5 says yes | N/A | Gap |
| AC-U3 full journey | Required | API only | — | T3 deferred | Gap |
| Supabase SMTP invites | Required | Configured | §9 | PASS | OK |
| Retract invite | Required | Delete only | — | N/A | Gap |
| OTP 1h + resend | Documented | config.toml | §7 | N/A | OK |

---

## 7. Data & Asset Requirements

| Asset | Source | Auth | Used by |
|-------|--------|------|---------|
| Supabase project `cfuvghdsuwactfeamtym` | prod.env | CLI token / Dashboard | config push, live auth |
| Resend verified domain | Operator | DNS SPF/DKIM/DMARC | SMTP delivery |
| `VECINITA_ADMIN_FRONTEND_URL` | DO deploy / infra | Modal secret (new) | Backend `redirect_to` |
| Invite template | `supabase/templates/invite.html` | config push | GoTrue mail |

**Operator prerequisite:** BUG-2026-06-30-email-test-send-provider-error — Resend domain
verification must be complete for mail to deliver.

---

## 8. Unresolved Gaps (downstream)

| Gap | Owner stage | Notes |
|-----|-------------|-------|
| Revise AC-U3 to require browser journey | 01-requirements | Currently API-only verified |
| ADR-032 or ADR-030 amend for callback pattern | 04-tech-plan | Invalidate `detectSessionInUrl`-only assumption |
| Phase 13 execution-plan tasks | 04-tech-plan | M54 or extend Phase 12 |
| `site_url` per environment (staging vs prod) | 04-tech-plan / 12-verify-deploy | Single `config.toml` — may need env-specific push strategy |
| S005 deploy stages 12/13 | Backlog or post-S006 | Paused with S005 |

---

## 9. Suggested Implementation Order (#109 validated)

1. **Supabase `site_url` + redirect allowlist** — `config push` + Dashboard verification
2. **Backend `redirect_to`** — `VECINITA_ADMIN_FRONTEND_URL` → Modal DM + route changes
3. **Frontend callback** — session bootstrap + hash error UX on accept/reset pages
4. **Admin retract** — `POST /admin/users/{id}/revoke-invite` + UI
5. **Tests + template polish + live smoke** — 10-e2e + 13-deploy-smoke

---

## 10. Affected Files (quick index)

| Area | Path |
|------|------|
| Invite routes | `apps/data-management-backend/vecinita_data_management_backend/user_admin_routes.py` |
| GoTrue client | `packages/shared-schemas/vecinita_shared_schemas/supabase_admin.py` |
| Accept UI | `apps/data-management-frontend/src/pages/SetPasswordPage.tsx` |
| Routing | `apps/data-management-frontend/src/App.tsx` |
| Self-service reference | `apps/data-management-frontend/src/pages/ForgotPasswordPage.tsx` |
| Supabase client | `apps/data-management-frontend/src/auth/supabaseClient.ts` |
| Supabase config | `supabase/config.toml` |
| Invite template | `supabase/templates/invite.html` |
| CI sync | `.github/workflows/supabase.yml` |
| Env / secrets | `infra/do/.env.example`, Modal DM secrets |
| Specs | `docs/user-journeys.md` (UJ-031), `docs/api-contract.md`, `docs/acceptance-criteria.md` |
| ADR baseline | `docs/adr/ADR-030-ev006-user-mgmt-implementation.md` |

---

## 11. Related Sessions & Issues

- **S005-user-mgmt-auth** (paused) — F35 scaffold; deploy 12/13 deferred
- **EV-006** → **EV-007** — F35 extension for #109
- **PR #102** — Phase 12 F35 merge
- **#75** — umbrella auth (closed; superseded by F34/F35)
- **BUG-2026-06-30-gotrue-multiple-instances-login** — separate login warning fix

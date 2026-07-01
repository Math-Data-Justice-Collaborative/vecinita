# ADR-032: EV-007 invite acceptance — redirect URLs, auth callback, retract invitation

**Status:** Accepted  
**Stage:** 04-tech-plan (S006, EV-007)  
**Date:** 2026-06-30  
**Feature:** F35.12–F35.15 — Invite acceptance flow extension  
**Issue:** [#109](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/109)  
**Builds on:** [ADR-030](ADR-030-ev006-user-mgmt-implementation.md) §5 (superseded in part), [ADR-029](ADR-029-admin-user-management-and-auth-ux.md), RD-091–RD-098

## Context

S005/EV-006 (F35) scaffolded operator user management — invite API, `/users` UI, Resend SMTP,
and bilingual email templates — but the **end-to-end invite acceptance flow fails in
staging/production**. Invitee email links redirect to `localhost:3000` with `#error=otp_expired`
instead of the deployed admin frontend `/accept-invite` route.

01-requirements (EV-007) identified three root causes:

1. Backend never passes `redirect_to` on GoTrue invite/resend/recovery calls despite client support.
2. Live Supabase `site_url` / redirect allowlist may still default to `localhost:3000`.
3. Frontend `SetPasswordPage` calls `updateUser({ password })` without waiting for a session
   established from the email link — **ADR-030 §5 assumption (`detectSessionInUrl` alone is
   sufficient) is invalidated** when redirect host is wrong or session detection is async.

Requirements decisions RD-091–RD-098 are locked. This ADR resolves the remaining **technical**
choices for 07-build.

## Decision

### 1. New ADR-032 (not ADR-030 amend) (TP-S006-01)

Author **ADR-032** for EV-007 implementation decisions. ADR-030 §5 remains historical;
add a supersession note in ADR-030 pointing here for auth-callback behaviour.

### 2. `VECINITA_ADMIN_FRONTEND_URL` on Modal DM backend (TP-S006-02)

| Property | Value |
|----------|-------|
| Env var | `VECINITA_ADMIN_FRONTEND_URL` |
| Host | **Modal data-management ASGI only** (same secret bundle as `SUPABASE_SECRET_KEY`) |
| Format | Origin **without trailing slash**, e.g. `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app` |
| Usage | Build `{origin}/accept-invite` and `{origin}/reset-password` for GoTrue `redirect_to` |

When unset, user-management routes that send auth emails return **`503 Service Unavailable`**
(same pattern as missing `SUPABASE_SECRET_KEY`). Do **not** fall back to `window.location.origin`
server-side — the backend has no browser context.

Already present on internal-write-api for health aggregation; **add to Modal DM** for redirect
building (config-spec §Modal DM).

### 3. Shared redirect URL builder (TP-S006-03)

Add `build_auth_redirect_path(origin: str, path: Literal["accept-invite", "reset-password"]) -> str`
in `vecinita_data_management_backend` (or `vecinita_shared_schemas` if reused). Validates:

- Origin is `https://` in non-local environments (warn-only in dev).
- Path is one of the two allowed suffixes.
- No double slashes; strips trailing slash from origin.

All three call sites use the helper:

| Route | GoTrue method | Redirect path |
|-------|---------------|---------------|
| `POST /admin/users/invite` | `invite_user_by_email` | `/accept-invite` |
| `POST /admin/users/{id}/resend-invite` | `invite_user_by_email` | `/accept-invite` |
| `POST /admin/users/{id}/reset-password` | `send_password_recovery` | `/reset-password` |

Self-service forgot-password continues using `window.location.origin + '/reset-password'` in the
browser (existing `ForgotPasswordPage` pattern — no backend env needed).

### 4. Staging-first Supabase `site_url` (TP-S006-04, RD-094)

Update `VITE`-free `supabase/config.toml`:

| Key | Value |
|-----|-------|
| `[auth] site_url` | Staging admin frontend URL (`https://vecinita-admin-frontend-ef4ob.ondigitalocean.app`) |
| `[auth] additional_redirect_urls` | Full paths for staging + prod admin origins (`…/accept-invite`, `…/reset-password`); local dev origins (`http://127.0.0.1:5173`, `http://localhost:5173`) |

**Single shared Supabase project** — staging-first until prod cutover. Prod admin origin lives in
`additional_redirect_urls` until operator flips `site_url` at prod launch (document in runbook).

Local dev (`supabase start`) keeps `127.0.0.1:5173` in allowlist; developers run admin FE on that port.

Sync via existing `.github/workflows/supabase.yml` `sync-production` job on merge to `main`.
Operator verifies Dashboard → Authentication → URL Configuration after every push (TC-109).

### 5. Auth callback hook — explicit session gate (TP-S006-05, RD-095)

Replace the ADR-030 assumption with a shared React hook `useAuthLinkCallback()` in
`apps/data-management-frontend/src/auth/`:

**On mount (both `/accept-invite` and `/reset-password`):**

1. Parse `window.location.hash` and `window.location.search`:
   - `#error=…&error_code=otp_expired` → **expired** state (show bilingual error UI).
   - `#error=access_denied` → **denied** state.
   - `?code=` (PKCE) → call `supabase.auth.exchangeCodeForSession(code)` if hash tokens absent.
2. Subscribe to `onAuthStateChange` + call `getSession()` — `detectSessionInUrl: true` still
   enabled on the client singleton; the hook **waits** for a non-null session before exposing the
   password form (loading spinner meanwhile).
3. Timeout (default **10 s**): if no session and no hash error → **invalid link** state.

**Password form** renders only when `status === "ready"` (session established). `updateUser({ password })`
unchanged; on success redirect to `/login` (or optional auto-sign-in — defer to v1 `/login` link).

Extract hook so `SetPasswordPage` stays thin; Vitest mocks hook states for TC-106/TC-107.

### 6. Bilingual expired-link UX (TP-S006-06, RD-095, AC-U20)

Dedicated error panel (not blank page, not wrong-host redirect):

| State | EN copy (i18n key) | Action |
|-------|-------------------|--------|
| `otp_expired` | Link expired; contact your administrator | Link to `/login` |
| `access_denied` | Link invalid or already used | Link to `/login` |
| `timeout` | Could not verify link; try again or contact admin | Link to `/login` |

Add keys under `admin.auth.inviteLinkExpired`, `admin.auth.inviteLinkInvalid`, etc. in
`packages/frontend-i18n`.

### 7. Retract invitation = delete pending identity (TP-S006-07, RD-092)

GoTrue has no "revoke invite" API. For `status=invited` users only:

- New route: `POST /admin/users/{user_id}/revoke-invite` → `delete_user(user_id)`.
- Reject with `409` if target is `active` or `disabled` (not pending invite).
- Audit: `user.invite_revoked` (distinct from `user.deleted`).
- UI: **"Retract invitation"** button visible only when `status === "invited"`; **"Delete user"**
  remains for active/disabled operators.

No lockout-guard changes — retracting a pending invite cannot remove the last admin (they never
logged in).

### 8. Resend refreshes OTP with correct redirect (TP-S006-08)

`POST /admin/users/{id}/resend-invite` continues calling `invite_user_by_email` (GoTrue re-issues
OTP) but **must** pass `redirect_to={origin}/accept-invite`. No `generate_link` fallback in v1 —
resend is the operator workaround for expiry (ADR-030 §7 unchanged).

### 9. Invite metadata UI — client-side expiry hint (TP-S006-09, RD-096)

Users list shows for `status=invited` rows:

- **`invited_at`**: map from GoTrue `created_at` (already on `UserSummary`).
- **"Expires ~1h"** hint: client-side label referencing global `otp_expiry = 3600` (no per-invite
  API). Optional future: surface `email_confirmed_at` when queryable.

### 10. Keep Supabase SMTP for invite/recovery mail (TP-S006-10, RD-091)

Do **not** send invite/recovery mail via Resend REST API. Resend REST remains for
`POST /admin/email/test` only (ADR-031). Invite/recovery consistency via GoTrue + Resend SMTP.

### 11. CORS + OpenAPI for revoke-invite (TP-S006-11)

- Add `POST /admin/users/{user_id}/revoke-invite` to CORS allowed methods (cors-browser-methods).
- Update `openapi/data-management.yaml` per api-contract.

### 12. Git strategy (TP-S006-12)

- Branch: `feat/S006-invite-acceptance` (already open).
- PR-49: Phase 13 / S006 (EV-007) → `main`, linked to #109.

### 13. Redeploy order (TP-S006-13)

Per `deployment-integration.md` §EV-007 — **order matters**:

1. `supabase config push` — `site_url` + redirect allowlist + template polish.
2. Set `VECINITA_ADMIN_FRONTEND_URL` on Modal DM secret.
3. `modal deploy` data-management ASGI (backend `redirect_to`).
4. Redeploy admin frontend (callback hook — no new `VITE_*` required).
5. Operator: Dashboard Auth URL verification + live invite smoke (13-deploy-smoke T3).

### 14. Email template polish (TP-S006-14, RD-097)

Minor copy/branding updates to `supabase/templates/invite.html` and `recovery.html`:

- Clearer CTA button text.
- Expiry notice aligned with `otp_expiry = 3600` ("1 hour").
- Vecinita branding header (existing stacked EN/ES pattern).

Broken links are upstream (redirect config); templates are polish only.

### 15. E2E tier (TP-S006-15, RD-098)

| Tier | Coverage | Gate |
|------|----------|------|
| **T2** | Vitest callback tests (TC-106/107) + backend redirect assertions (TC-104/105/108) + config smoke (TC-109) | **Merge-blocking** (07-build / 08-verify-build) |
| **T3** | Live invite link in staging (13-deploy-smoke) | **Deploy sign-off** — not merge-blocking |

### 16. No new dependencies (TP-S006-16)

Existing stack covers all work: `httpx`, `supabase-js`, Supabase CLI, Resend SMTP. No new packages.

## Consequences

### Positive

- Closes production onboarding gap tracked in #109.
- Explicit callback hook prevents password form race with async session detection.
- Staging-first `site_url` fixes wrong-host redirects immediately after config push.
- Retract invitation gives operators clear lifecycle control without conflating delete.

### Negative / trade-offs

- Single Supabase project with staging-first `site_url` means prod cutover requires a manual
  Dashboard/`config.toml` update (documented).
- Client-side "~1h expiry" hint is approximate (global OTP knob, not per-invite).
- Retract = delete — re-inviting the same email creates a fresh identity (acceptable for v1).

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Amend ADR-030 in place | EV-007 is a distinct cycle; ADR-032 keeps S005 history intact |
| Resend REST for invite mail | RD-091 — consistency with GoTrue templates + SMTP path |
| `generate_link(type=invite)` for resend | Resend endpoint already re-issues OTP; extra complexity |
| Frontend-only fix (no backend `redirect_to`) | GoTrue builds `ConfirmationURL` from backend param + `site_url`; both required |
| Per-invite OTP extension API | Not available in GoTrue config; resend is operator workaround |

## References

- `docs/context/invite-acceptance-flow.md` — gap analysis
- `docs/deployment-integration.md` §EV-007
- `docs/test-plan.md` TC-104–TC-110
- `docs/user-journeys.md` UJ-031, UJ-033

# ADR-029: Admin user management, remember-me, and repo-versioned Resend SMTP emails

**Status:** Accepted
**Stage:** 01-requirements (S005, EV-006)
**Date:** 2026-06-29
**Feature:** F35 — Admin user management + auth UX
**Issue:** [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75) (auth umbrella)
**Builds on:** [ADR-026](ADR-026-supabase-admin-auth.md) (Supabase admin auth), [ADR-027](ADR-027-supabase-auth-verification-and-env-sync.md) (verification + env sync), [ADR-028](ADR-028-supabase-jwt-es256-jwks.md) (ES256/JWKS)

## Context

[ADR-026](ADR-026-supabase-admin-auth.md) (F34, merged via PR #100) added Supabase Auth for the
admin surfaces: invite-only registration, `admin`/`viewer` roles, JWT verification, and a login
screen. Operator lifecycle management (invite/list/role/disable/delete) was deferred to the
**Supabase Dashboard** (F34 AC-A10 operator runbook), the login screen had **no remember-me
control**, and production invite-email delivery was left as an operator prerequisite (custom SMTP,
TP-S004-08) with no repo-versioned templates.

The 2026-06-29 request (EV-006) asks for three operator-facing enhancements so the team no longer
depends on the Supabase Dashboard for day-to-day user management or hand-edited email templates:

1. A **User Management page** in the admin dashboard (invite, list, change role, resend invite,
   disable, revoke, admin-triggered password reset).
2. A **"Remember me"** control on the login screen that persists the session in the browser.
3. **Production email delivery via Resend** with **versioned, bilingual HTML templates** in the
   repo, synced to Supabase as part of CI/CD.

## Decision

### 1. Admin user management via the Supabase Admin API, server-side only (RD-080, RD-081)

A new **admin-only `/admin/users*` API namespace** wraps the Supabase **Admin API**
(`auth.admin.inviteUserByEmail`, `listUsers`, `updateUserById`, `deleteUser`, ban via
`updateUserById({ ban_duration })`, `generateLink`/recovery for reset). The Supabase
**secret key** (`SUPABASE_SECRET_KEY`) is used **only server-side** and is **never** exposed to
the browser. All routes require an `admin` JWT; `viewer` receives `403`.

Operator email/role/status are read from **Supabase** and returned to the admin UI **in transit
only** — they are **never written to the Vecinita corpus DB** (ADR-026 identity residency holds).
The corpus DB continues to store only the opaque Supabase user UUID + role on `audit_log`.

Which backend hosts `/admin/users*` (Data Management Modal ASGI vs internal-write API on DO) and
the exact placement/scope of `SUPABASE_SECRET_KEY` in a *running* service (it was previously
operator-shell/seed-only) are resolved in **04-tech-plan**.

### 2. Remember-me via a storage-routing adapter chosen before `createClient` (RD-084)

supabase-js has **no native remember-me flag**; the storage backend must be chosen at client
construction. The DM frontend reads a persisted preference from `localStorage` key
**`vecinita.auth.remember`** and constructs the Supabase client with a `storage` adapter that
routes to:

- **`localStorage`** when remember-me is **on** (default) → session survives browser restart.
- **`sessionStorage`** when **off** → session clears when the tab/browser closes.

Toggling the checkbox updates the preference and re-initialises the client/session storage. This
is device-local browser state only; it sends nothing extra to the server (consistent with the
F33 client-local-state precedent).

### 3. Self-service password reset in-app (RD-083)

The login screen gains a **"Forgot password?"** link that triggers Supabase
`resetPasswordForEmail` (recovery email), and an in-app reset page that completes the flow via
`updateUser`. Admins can also trigger a reset for any user from the User Management page
(RD-082).

### 4. Resend SMTP via repo-versioned `config.toml` — "hybrid" sourcing (RD-085)

Resend is used to **provision the API key and verify the sender domain** (operator convenience),
but the SMTP configuration itself is **encoded in `supabase/config.toml`** under
`[auth.email.smtp]` with `pass = "env(SUPABASE_SMTP_PASS)"`, so **`supabase config push` is the
single source of truth** for both SMTP and templates. This avoids the conflict where
Dashboard-managed SMTP would be overwritten by a `config push` of repo templates. Credentials:
host `smtp.resend.com`, port `465`, user `resend`, pass = Resend API key (secret).

### 5. Versioned, stacked-bilingual email templates synced via CI/CD (RD-086, RD-087)

All six auth email surfaces are versioned as HTML under `supabase/templates/` and referenced by
`content_path`:

| Type | config.toml block |
|------|-------------------|
| Invite | `[auth.email.template.invite]` |
| Recovery (password reset) | `[auth.email.template.recovery]` |
| Confirmation | `[auth.email.template.confirmation]` |
| Magic link | `[auth.email.template.magic_link]` |
| Email change | `[auth.email.template.email_change]` |
| Security notifications (`password_changed`, `email_changed`, MFA) | `[auth.email.notification.*]` |

Because Supabase serves **one template per type with no native per-recipient locale switching**,
templates are **stacked bilingual** — each HTML file contains an **English section followed by a
Spanish section** (consistent with the F31 EN/ES product posture; the email *chrome* is bilingual
while dynamic Supabase variables stay as-is).

CI sync uses the existing `.github/workflows/supabase.yml`: the `validate` job lints template
paths offline; the `sync-production` job runs `supabase config push` (uploading template HTML per
CLI [PR #5686](https://github.com/supabase/cli/pull/5686), merged 2026-06-25). The Supabase CLI
version is **pinned** in the workflow so template-HTML push is guaranteed (RD-088).

**Known CLI path-resolution gotcha** ([issue #5124](https://github.com/supabase/cli/issues/5124)):
`auth.email.template.*` `content_path` resolves from the **project root**, while
`auth.email.notification.*` resolves from the **`supabase/`** directory. Template paths in
`config.toml` must follow these two conventions; `config push` is run from the repo root. The
exact path strings + pinned CLI version are finalised in 04-tech-plan.

## Scope boundaries

- **In:** admin user lifecycle (invite/list/role/resend/disable/revoke/admin-reset), remember-me,
  self-service password reset, Resend SMTP + 6 bilingual templates, CI sync.
- **Out (unchanged from ADR-026):** OAuth/social login; RBAC beyond `admin`+`viewer`; visitor
  (ChatRAG) authentication; operator PII in the corpus DB; bulk CSV user import; MFA/2FA (deferred
  — may be a later cycle); failed-login lockout beyond Supabase's built-in rate limits.

## Consequences

- New admin-only API surface (`/admin/users*`) and a new DM frontend route (`/users`). No change
  to ChatRAG or existing corpus/admin contracts.
- `SUPABASE_SECRET_KEY` moves from operator-shell/seed-only into a running backend — its host and
  least-privilege handling are an explicit 04-tech-plan decision and a deploy-secrets change.
- New operator prerequisite: a **verified Resend sending domain** + sender address, and the
  `SUPABASE_SMTP_PASS` (Resend API key) secret in GitHub/Supabase. Captured in
  `staging-secrets-matrix.md`.
- Supabase email **rate limits** (`auth.rate_limit.email_sent`) and **invite link expiry** become
  config-spec'd, documented values (previously implicit).
- User-management actions (invite/role-change/disable/delete/reset) are recorded in `audit_log`
  with `actor_id` (UUID) + `actor_role` — no PII (extends ADR-016).

## References

- Builds on: [ADR-026](ADR-026-supabase-admin-auth.md), [ADR-027](ADR-027-supabase-auth-verification-and-env-sync.md), [ADR-028](ADR-028-supabase-jwt-es256-jwks.md)
- Feature: `docs/feature-list.md` §F35
- Session: `docs/sessions/S005-user-mgmt-auth/session-brief.md`
- Decisions: `docs/decisions.md` §EV-006 resolutions (RD-080–RD-088)
- Journeys: `docs/user-journeys.md` UJ-030–UJ-033
- Acceptance: `docs/acceptance-criteria.md` AC-U1–AC-U9
- API: `docs/api-contract.md` §Admin user management (F35)
- Config: `docs/config-spec.md` §Admin user management + email (EV-006 F35)
- Research: Supabase Admin API; Resend↔Supabase SMTP (`smtp.resend.com:465`); supabase-js `storage` option (no native remember-me, auth-elements #7); CLI PR #5686 + issue #5124
- Related: ADR-016 (audit log no IP), F31 (bilingual UI), F33 (client-local browser state)

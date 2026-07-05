# ADR-031: EV-006 auth UX hardening — idle timeout, log-out-everywhere, deliverability test-send, audit viewer

**Status:** Accepted  
**Stage:** 04-tech-plan (S005, EV-006 — scope addition)  
**Date:** 2026-06-29  
**Feature:** F35 — Admin user management + auth UX  
**Builds on:** [ADR-029](ADR-029-admin-user-management-and-auth-ux.md), [ADR-030](ADR-030-ev006-user-mgmt-implementation.md), [ADR-007](ADR-007-modal-do-database-write-boundary.md), [ADR-016](ADR-016-audit-log-no-ip.md)

## Context

After the F35 tech plan ([ADR-030](ADR-030-ev006-user-mgmt-implementation.md), TP-S005-01–16, Phase 12
M48–M52) was accepted, the user reviewed it (2026-06-29) and asked to **extend the scope** with four
operator-experience and security items that were not in the original plan. MFA/2FA and bulk CSV
import remain explicitly **deferred** (ADR-029 scope out).

The four additions and the design decisions taken (after research + a focused interview) are below.
Two of them reuse infrastructure that already exists: the audit log read path
(`GET /internal/v1/audit`, EV-002/F29) + the admin **AuditPage**, and user-list pagination
(`page`/`page_size` already in the `/admin/users` contract). The remaining work is therefore smaller
than it first appears.

## Decision

### TP-S005-17 — Idle/session timeout (frontend-only)

A **client-side inactivity timer** signs the operator out of the **current device** after **30
minutes** of inactivity, with a **1-minute warning modal** ("Stay signed in" / "Log out now"). No
native Supabase idle-timeout exists; this is a UX/security layer on top of the 1h JWT expiry
(`jwt_expiry = 3600`).

- Implemented as a `useIdleTimeout` hook mounted in the **always-mounted admin shell**
  (`AdminLayout` / inside `ProtectedRoute`), per `.cursor/rules/frontend-session-state-lifting.mdc`
  — the timer must not live in a route-unmounted component.
- Activity listeners (throttled): `mousemove`, `keydown`, `click`, `scroll`, `visibilitychange`.
- On timeout: `supabase.auth.signOut({ scope: "local" })` → redirect to `/login` with a
  "signed out due to inactivity" notice.
- Configurable via build-time env: `VITE_VECINITA_IDLE_TIMEOUT_MIN` (default `30`) and
  `VITE_VECINITA_IDLE_WARNING_SEC` (default `60`). Device-local only; sends nothing extra to the
  server (consistent with the F33 client-local-state precedent).

### TP-S005-18 — Self "log out of all devices" (frontend-only)

The account menu gains a **"Log out of all devices"** action calling `supabase.auth.signOut()` with
the **default `global` scope**, which revokes **all refresh tokens** for the operator across devices.
The ordinary logout uses `{ scope: "local" }`. **Caveat (documented):** already-issued access tokens
remain valid until `exp` (≤ 1h here) — acceptable given the short `jwt_expiry`.

### TP-S005-19 — Admin force-logout of another operator

New admin-only route **`POST /admin/users/{user_id}/signout`** on the DM Modal backend revokes a
**target** operator's sessions (keeping the account enabled — distinct from disable/ban). Emits a
`user.signed_out` audit event.

**Server mechanism (verify in build):** GoTrue's Admin REST API has **no first-class "revoke another
user's sessions" endpoint** (the `signOut(jwt)` path needs the target's own JWT; `POST /auth/v1/logout`
acts on the bearer's session). The chosen mechanism is a **`SECURITY DEFINER` RPC**
(`admin_delete_user_sessions(uid uuid)`) that deletes the user's rows from `auth.sessions` on the
**Supabase project DB**, invoked by the backend via
`POST {SUPABASE_URL}/rest/v1/rpc/admin_delete_user_sessions` with the **service key**.

- The RPC is committed under `supabase/migrations/` for review and applied to the Supabase project
  as a **one-time, operator-run** step (documented in the staging runbook) — **no new CI `db push`
  capability is introduced** in this cycle.
- **Fallback** if the RPC is not yet applied: the route returns `503 mechanism_unavailable` with a
  runbook pointer; **disable/ban** (existing) remains the guaranteed lockout for urgent cases.
- **Caveat (documented):** the target's current access token stays valid until `exp` (≤ 1h).
- **Lockout guards** (extend TP-S005-04): force-logout of self is allowed (no-op-safe); force-logout
  of the **sole remaining admin** is permitted (it does not de-privilege them).

### TP-S005-20 — User list search + pagination (server-side)

`GET /admin/users` gains an optional **`q`** query param. The backend forwards it to the GoTrue Admin
API **`filter`** query param (partial/full email match). Per supabase-js
[PR #1741](https://github.com/supabase/supabase-js/pull/1741), `filter` must be **≥ 3 characters**;
the backend returns **`400 invalid_search`** for shorter non-empty `q` (empty `q` = unfiltered).
Pagination uses the existing `page`/`page_size`; the UI consumes the shared
`PaginationControls` component (`packages/frontend-ui`). Performance caveat (large-DB) is irrelevant
for the small operator team.

### TP-S005-21 — Audit viewer enhancement (reuse F29 infrastructure)

User-management mutations already emit audit events (ADR-030 §3). This decision standardises and
surfaces them:

- All `/admin/users*` mutations emit with **`entity_type = "user"`** and **`entity_id = <target
  UUID>`** (event types `user.invited`, `user.role_changed`, `user.disabled`, `user.enabled`,
  `user.deleted`, `user.reset_password`, `user.signed_out`, plus `email.test_sent` with
  `entity_type = "email"`).
- The admin **AuditPage** gains an **`entity_type` quick-filter** (incl. a "Users" option) — the
  `GET /internal/v1/audit` endpoint already supports the `entity_type` query param, so this is a
  frontend wiring change only.
- **i18n labels** are added for the new `user.*` / `email.*` event types (admin EN/ES bundles).
- Each **Users-page** row gets a **"View activity"** link that opens the Audit page pre-filtered by
  that user's `entity_id`.
- **No PII**: audit payloads keep only opaque UUIDs + role + event metadata (extends ADR-016) — no
  email/name in the stored payload.

### TP-S005-22 — Deliverability "send test email" via Resend REST

New admin-only route **`POST /admin/email/test`** (`{ "to": "<email>" }`) sends a branded test email
through the **Resend REST API** (`POST https://api.resend.com/emails`, bearer = Resend API key) from
the verified sender domain. Rationale: it proves the **Resend domain + DNS (SPF/DKIM/DMARC) + key**
end-to-end **without** creating spurious Supabase users, and shares the same Resend account/domain as
the Supabase SMTP path (so a passing test strongly implies SMTP works).

- **Auth/secret:** uses a dedicated env **`RESEND_API_KEY`** on the **Modal DM** secret bundle (same
  value as `SUPABASE_SMTP_PASS`; named separately to keep the "backend reads it" vs "Supabase CLI
  reads it" concerns distinct). Sender from **`RESEND_SENDER_EMAIL`** (the verified `admin_email`).
- **Rate limit:** 5 test sends/hour per admin JWT (same sliding-window helper as invite).
- **Response:** `202 { "message_id": "<resend id>" }`; `503 email_unconfigured` if
  `RESEND_API_KEY`/`RESEND_SENDER_EMAIL` are unset.
- Emits `email.test_sent` audit event (payload: recipient **domain** only + success — no full
  address).

### TP-S005-23 — SPF / DKIM / DMARC operator checklist (docs)

A deliverability checklist (DNS records to add at the Resend-verified domain: SPF `TXT`, DKIM
`CNAME`/`TXT`, DMARC `TXT`) is added to the **staging runbook** + `staging-secrets-matrix.md`
operator prerequisites. No code; the test-send button (TP-S005-22) is the verification tool.

### TP-S005-24 — Config + secrets delta

| Key | Where | Value / note |
|-----|-------|--------------|
| `VITE_VECINITA_IDLE_TIMEOUT_MIN` | DM frontend build env | default `30` |
| `VITE_VECINITA_IDLE_WARNING_SEC` | DM frontend build env | default `60` |
| `RESEND_API_KEY` | Modal DM secret | Resend API key (same value as `SUPABASE_SMTP_PASS`) |
| `RESEND_SENDER_EMAIL` | Modal DM secret | verified Resend sender (`admin_email`) |
| Test-send rate limit | DM backend | `5/hour/admin JWT` |

## Consequences

- **Three new admin-only endpoints** on the DM backend: `POST /admin/users/{user_id}/signout`,
  `POST /admin/email/test`, and a `q` param on `GET /admin/users`. OpenAPI `data-management.yaml`
  grows accordingly.
- **Frontend:** `useIdleTimeout` + warning modal; "log out of all devices" action; search box +
  `PaginationControls` on the Users page; AuditPage `entity_type` filter + per-user "View activity"
  link; new i18n keys (EN/ES).
- **Supabase project:** one new committed RPC migration (`admin_delete_user_sessions`) applied
  **once by the operator** (runbook); no new CI `db push` step this cycle.
- **Secrets:** `RESEND_API_KEY` + `RESEND_SENDER_EMAIL` added to the Modal DM secret bundle (added to
  `staging-secrets-matrix.md`).
- **No change** to ChatRAG, corpus contracts, or the Modal→DB write boundary (ADR-007 preserved —
  audit still flows through `POST /internal/v1/audit/event`).
- Plan grows by one milestone (**M53**) appended to Phase 12.

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| Client-only user search (filter current page) | Misses users on other pages; GoTrue `filter` gives real server-side search cheaply |
| Test-send via Supabase recovery email to self | Only works for existing users; doesn't isolate domain/DNS; Resend REST proves deliverability directly |
| New dedicated audit page for users | Duplicates F29 AuditPage; reuse + filter is lower-risk |
| Automate `admin_delete_user_sessions` via CI `db push` | Adds a new CI capability touching the auth schema — deferred; one-time operator apply is sufficient for a small team |
| Ban-cycle for force-logout | Hacky; doesn't reliably purge active sessions; disable/ban already covers urgent lockout |

## References

- [ADR-029](ADR-029-admin-user-management-and-auth-ux.md), [ADR-030](ADR-030-ev006-user-mgmt-implementation.md)
- `docs/sessions/S000-internal-docs-archive/execution-plan.md` Phase 12 **M53**
- `docs/api-contract.md` §Admin user management (F35) — `q`, `/signout`, `/admin/email/test`
- `docs/user-journeys.md` UJ-034–UJ-038; `docs/test-plan.md` TC-096–TC-103; `docs/acceptance-criteria.md` AC-U10–AC-U16
- Research (verified 2026-06-29): supabase-js `signOut` scopes (global/local/others); GoTrue Admin
  `listUsers` `filter` ≥3 chars (PR #1741); GoTrue `POST /logout` revokes refresh tokens; Supabase
  sessions live in `auth.sessions` (Supabase Auth sessions guide); Resend REST `POST /emails`

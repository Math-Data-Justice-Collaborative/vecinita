# ADR-030: EV-006 user management — backend placement, Admin API client, audit wiring

**Status:** Accepted  
**Stage:** 04-tech-plan (S005, EV-006)  
**Date:** 2026-06-29  
**Feature:** F35 — Admin user management + auth UX  
**Builds on:** [ADR-029](ADR-029-admin-user-management-and-auth-ux.md), [ADR-007](ADR-007-modal-do-database-write-boundary.md), [ADR-027](ADR-027-supabase-auth-verification-and-env-sync.md)

## Context

[ADR-029](ADR-029-admin-user-management-and-auth-ux.md) (01-requirements) defined *what* F35 delivers:
admin `/admin/users*` API, remember-me, Resend SMTP + versioned bilingual templates, and CI
`config push` sync. Four items were explicitly deferred to **04-tech-plan**:

1. Which backend hosts `/admin/users*` and where `SUPABASE_SECRET_KEY` lives at runtime.
2. Exact `content_path` strings + pinned Supabase CLI version.
3. supabase-js storage-adapter pattern for remember-me.
4. `auth.rate_limit.email_sent` + invite/recovery link expiry values.

Additional gaps surfaced during technical planning: cross-service **audit_log** writes (ADR-007),
**last-admin / self-lockout** guards, **invite-acceptance** frontend route, application-level
**invite abuse** protection, **CORS verb** coverage for new routes, and **password policy** in
Supabase config.

## Decision

### 1. Host `/admin/users*` on the Data Management Modal backend (TP-S005-01)

The **Data Management Modal ASGI** (`apps/data-management-backend`) hosts all `/admin/users*`
routes. Rationale:

- DM frontend already calls this backend (`VITE_VECINITA_ADMIN_API_URL`) with
  `X-Vecinita-Proxy-Key` + `Authorization: Bearer`.
- JWT admin-role gating is already wired on `/jobs*`.
- **Least privilege:** `SUPABASE_SECRET_KEY` stays out of the internal-write-api, which is the
  sole `DATABASE_URL` holder (ADR-007). Concentrating both secrets in one DO service increases
  blast radius.
- Modal cold-start latency is acceptable for infrequent admin user-management operations.

`SUPABASE_SECRET_KEY` is added to the **Modal data-management** secret bundle only (not DO
internal-write-api, not browser builds).

### 2. Raw `httpx` GoTrue Admin REST client with typed Pydantic models (TP-S005-02)

The backend calls Supabase Auth Admin API via **`httpx`** against
`{SUPABASE_URL}/auth/v1/admin/*` and `/auth/v1/invite`, with request/response models in
`vecinita_shared_schemas.supabase_admin` (new submodule). **Do not** add `supabase-py` — it
pulls postgrest/storage/realtime and complicates strict typing (ADR-018).

Methods wrapped: `list_users`, `invite_user_by_email`, `update_user_by_id` (role + ban),
`delete_user`, `generate_link` (recovery).

### 3. Audit via service-to-service ingest on internal-write-api (TP-S005-03)

User-management mutations emit `audit_log` rows by **POST**ing to a new
**`POST /internal/v1/audit/event`** route on internal-write-api, authenticated with
`VECINITA_INTERNAL_API_KEY` (service-to-service only). Payload: `event_type`, `entity_type`,
`entity_id`, `payload` (no email/PII), `actor_id`, `actor_role`.

This preserves ADR-007 (only internal-write-api holds `DATABASE_URL`) while satisfying RD-089.

Event types (examples): `user.invited`, `user.role_changed`, `user.disabled`, `user.enabled`,
`user.deleted`, `user.reset_password`.

### 4. Full lockout guards (TP-S005-04)

The user-mgmt service rejects:

- **Self-actions:** admin cannot delete, disable, or demote **their own** account.
- **Last-admin:** cannot delete, disable, or demote the **sole remaining** `admin`.

Returns `409 Conflict` with a clear error code. Counts admins via Supabase Admin API `list_users`
(filter `app_metadata.role=admin`, not banned).

### 5. Dedicated frontend routes for invite accept + password reset (TP-S005-05)

| Route | Purpose |
|-------|---------|
| `/accept-invite` | New operator sets initial password after invite email link |
| `/reset-password` | Self-service + recovery-link completion (`updateUser`) |
| `/forgot-password` | Triggers `resetPasswordForEmail` |

All three are **public** (outside `ProtectedRoute`) but require a valid Supabase session/hash
from the email link (`detectSessionInUrl`).

> **Superseded in part by [ADR-032](ADR-032-ev007-invite-acceptance-implementation.md) (EV-007):**
> `detectSessionInUrl` alone is **insufficient** when redirect host is wrong or session detection
> is async. `/accept-invite` and `/reset-password` must use the explicit `useAuthLinkCallback`
> hook (hash/code/error parsing + session gate before password form). Backend must pass
> `redirect_to` via `VECINITA_ADMIN_FRONTEND_URL` on Modal DM.

### 6. Remember-me: preference at login, client rebuild before sign-in (TP-S005-06)

1. Login form includes **"Remember me"** checkbox (default **checked** per RD-084).
2. On submit: persist `vecinita.auth.remember` (`true`|`false`) to `localStorage`.
3. Call `resetSupabaseClient()` which clears the singleton and builds a new client with
   `auth.storage` routing to `localStorage` or `sessionStorage`.
4. Then `signInWithPassword`.

**Out of scope v1:** mid-session storage migration when toggling the checkbox while logged in.

Implementation: `createRoutingStorage(remember: boolean)` adapter in
`apps/data-management-frontend/src/auth/supabaseClient.ts`.

### 7. Email rate limits and OTP expiry (TP-S005-07)

`supabase/config.toml` values (synced via `config push`):

| Key | Value | Notes |
|-----|-------|-------|
| `[auth.rate_limit] email_sent` | `30` | Per hour; requires custom SMTP (Resend) |
| `[auth.email] otp_expiry` | `3600` | 1 hour — applies to recovery, magic link, **and** invite acceptance tokens (single knob in CLI config) |
| `[auth.email] max_frequency` | `60s` | Per-user resend cooldown |

**Invite link longer than 1h:** not independently configurable in `config.toml`; operators use
**Resend invite** from the User Management page when links expire. Document in operator runbook.

Application-level: **invite endpoint** rate-limited to **10 invites/hour per admin JWT**
(in-memory sliding window in DM backend; sufficient for small operator team).

### 8. Template `content_path` convention + pinned CLI (TP-S005-08, TP-S005-09)

Per CLI issue [#5124](https://github.com/supabase/cli/issues/5124) (verified still present
2026-06-29):

| Block | `content_path` pattern | Example |
|-------|------------------------|---------|
| `[auth.email.template.*]` | from **repo root** | `supabase/templates/invite.html` |
| `[auth.email.notification.*]` | from **`supabase/`** | `templates/password-changed.html` |

**Pin Supabase CLI** in `.github/workflows/supabase.yml`: **`>=2.70,<3`** (guarantees template
HTML upload via [PR #5686](https://github.com/supabase/cli/pull/5686), merged 2026-06-25).

`scripts/check_supabase_config.sh` extended to assert path existence + convention (TC-094, TC-095).

### 9. Resend operator prerequisite + template styling (TP-S005-10)

Resend domain verification remains an **operator prerequisite** (RD-090). v1 templates:
**text-forward stacked bilingual HTML** (EN block + ES block) with Vecinita branding placeholders
(sender name `Vecinita Admin`, neutral layout). Operator replaces `admin_email` in `config.toml`
after domain verification.

### 10. Additional safeguards (TP-S005-11–14)

| ID | Item | Decision |
|----|------|----------|
| TP-S005-11 | Password policy | `[auth] minimum_password_length = 8` in `config.toml` |
| TP-S005-12 | MFA/2FA | Explicitly **deferred** (ADR-029 scope out) |
| TP-S005-13 | Local email E2E | `supabase start` + Mailpit smoke in `supabase.yml` validate job when templates change |
| TP-S005-14 | Git | Single branch `feat/S005-user-mgmt-auth`; one PR to `main` (PR-48) |
| TP-S005-15 | CORS | Extend `configure_cors` + H0c tests for `PATCH`, `DELETE` on `/admin/users*` |
| TP-S005-16 | Secret rotation | Document `SUPABASE_SECRET_KEY` + `SUPABASE_SMTP_PASS` rotation in staging runbook |

## Consequences

- Modal data-management gains `SUPABASE_SECRET_KEY` — deploy-secrets change + Modal secret update.
- New shared schema module `vecinita_shared_schemas.supabase_admin` + internal-write audit ingest route.
- Six HTML templates + Resend SMTP blocks in `config.toml`; CI validate job grows.
- DM frontend gains four routes (`/users`, `/accept-invite`, `/forgot-password`, `/reset-password`).
- OpenAPI `data-management.yaml` gains `/admin/users*` paths.

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| internal-write-api hosts `/admin/users*` | Concentrates `DATABASE_URL` + `SUPABASE_SECRET_KEY`; violates least-privilege spirit of ADR-007 |
| `supabase-py` Admin API | Heavy transitive deps; typing friction under ADR-018 |
| Audit only in Supabase | Breaks corpus `audit_log` continuity (RD-089, ADR-016) |
| Mid-session remember-me migration | Complex; low value vs login-time selection |

## References

- [ADR-029](ADR-029-admin-user-management-and-auth-ux.md) — product decisions RD-080–RD-090
- `docs/execution-plan.md` Phase 12 (M48–M52)
- `docs/sessions/S005-user-mgmt-auth/reports/04-tech-plan.md`
- CLI [#5686](https://github.com/supabase/cli/pull/5686), [#5124](https://github.com/supabase/cli/issues/5124)
- Supabase Admin API (GoTrue `/auth/v1/admin/*`); supabase-js `auth.storage` option

---
session_id: S006-invite-acceptance
type: feature
status: paused
branch: feat/S006-invite-acceptance
started_at: 2026-06-30
intent: "GitHub #109 — complete invite acceptance flow (redirect URLs, auth callback, password setup, invitation admin). F35 gap from S005/EV-006."
orchestrator: 16-evolve
evolve_cycle_id: EV-007
context_briefs:
  - docs/sessions/S000-internal-docs-archive/context/invite-acceptance-flow.md
standing_docs_touched: []
linked_issues:
  - 109
parent_session: S005-user-mgmt-auth
---

# Session S006 — invite acceptance flow

## Intent

Deliver a **working, production-ready operator onboarding flow** for the admin UI. S005/EV-006
(F35) scaffolded invite API, `/users` UI, Resend SMTP, and bilingual email templates, but
staging/production invite links redirect to `localhost:3000` with `otp_expired` errors and
invitees never reach `/accept-invite` to set a password.

Tracked in [GitHub #109](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/109).

## Scope

**In scope**

- Backend `redirect_to` on invite, resend, and admin-triggered password recovery
- `VECINITA_ADMIN_FRONTEND_URL` on Modal DM backend + Supabase `site_url` / redirect allowlist sync
- Frontend auth callback handling on `/accept-invite` and `/reset-password` (hash/code exchange, `#error=` UX)
- Admin retract invitation (`POST /admin/users/{id}/revoke-invite`) + UI distinct from delete
- Tests: backend redirect assertions, Vitest callback coverage, e2e invite-accept journey
- Live invite smoke in 13-deploy-smoke (T3 deferred from S005)

**Out of scope (deferred)**

- MFA/2FA, bulk CSV user import
- Resend REST API for invite mail (R60: keep Supabase SMTP)
- Per-invite OTP extension beyond resend (global 1h `otp_expiry` remains)

## Routing plan

See [routing-plan.md](./routing-plan.md).

## Decisions (session open)

| ID | Decision |
|----|----------|
| R60 | Keep Supabase-managed invite/recovery mail via Resend SMTP |
| R61 | New `POST /admin/users/{id}/revoke-invite` + distinct UI + audit `user.invite_revoked` |
| R62 | Scoped context brief at `docs/sessions/S000-internal-docs-archive/context/invite-acceptance-flow.md` |

## Links

- Context: [invite-acceptance-flow.md](../../sessions/S000-internal-docs-archive/context/invite-acceptance-flow.md)
- Prior session: [S005-user-mgmt-auth](../S005-user-mgmt-auth/session-brief.md) (paused; deploy 12/13 deferred)
- ADR-030 (F35 implementation baseline), ADR-029 (email templates)
- UJ-031, AC-U3 (to be revised in 01-requirements)
- BUG-2026-06-30-email-test-send-provider-error (Resend domain prerequisite)

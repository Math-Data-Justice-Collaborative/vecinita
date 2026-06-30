---
session_id: S005-user-mgmt-auth
stage: 04-tech-plan
evolve_cycle_id: EV-006
feature_ids: [F35]
status: completed
date: 2026-06-29
---

# 04-tech-plan report — EV-006 / F35 (admin user management + auth UX)

Resolved every technical decision 01-requirements deferred for F35, authored **ADR-030**, and
appended **Phase 12 (M48–M52, T48.1–T52.6)** to the execution plan. Implementation captured as
tasks only (no product source written in this planning stage).

## Interview outcome

User skipped the interactive AskQuestion batch; **recommended defaults applied** per research and
ADR-029 alignment (documented as TP-S005-01–16 in ADR-030).

## Pre-built solutions (verified 2026-06-29)

| Need | Solution | Notes |
|------|----------|-------|
| Invite/list/role/ban/delete | GoTrue Admin REST via **httpx** | `SUPABASE_SECRET_KEY` server-side; typed Pydantic models |
| Remember-me | supabase-js **`auth.storage`** adapter | No native flag; rebuild client before `signIn` |
| Email templates | `config.toml` `content_path` + **`supabase config push`** | CLI ≥2.70 (#5686); path split #5124 |
| SMTP | Resend `[auth.email.smtp]` in `config.toml` | Hybrid sourcing RD-085 |
| CI sync | Extend **`.github/workflows/supabase.yml`** | Pin CLI; validate template paths |
| Audit | **POST `/internal/v1/audit/event`** on write API | Preserves ADR-007 |

## Decisions (TP-S005-01–16)

See [ADR-030](../../adr/ADR-030-ev006-user-mgmt-implementation.md). Summary:

| ID | Decision |
|----|----------|
| TP-S005-01 | `/admin/users*` on **DM Modal backend**; `SUPABASE_SECRET_KEY` in Modal secrets only |
| TP-S005-02 | **httpx** GoTrue Admin REST + `vecinita_shared_schemas.supabase_admin` |
| TP-S005-03 | Audit via **service-to-service** ingest on internal-write-api |
| TP-S005-04 | **Full lockout guards** (self + last-admin) |
| TP-S005-05 | **`/accept-invite`** + **`/reset-password`** + **`/forgot-password`** routes |
| TP-S005-06 | Remember-me at **login time**; `resetSupabaseClient()` before sign-in |
| TP-S005-07 | `email_sent=30/h`, `otp_expiry=3600`, app invite limit 10/h/admin |
| TP-S005-08 | Template paths: `supabase/templates/*.html` vs `templates/*.html` (#5124) |
| TP-S005-09 | Pin Supabase CLI **`>=2.70,<3`** |
| TP-S005-10 | Resend domain = operator prerequisite; text-forward bilingual templates v1 |
| TP-S005-11 | `minimum_password_length = 8` |
| TP-S005-12 | MFA deferred |
| TP-S005-13 | Inbucket smoke in validate job |
| TP-S005-14 | Branch `feat/S005-user-mgmt-auth`, PR-48 |
| TP-S005-15 | CORS PATCH/DELETE on `/admin/users*` |
| TP-S005-16 | Secret rotation runbook delta |

## Artifacts produced / updated

- **New**: `docs/adr/ADR-030-ev006-user-mgmt-implementation.md`
- **Updated**: `docs/decisions.md` (TP-S005), `docs/dependency-inventory.md`,
  `docs/config-spec.md` (rate limits, paths, password policy), `docs/staging-secrets-matrix.md`,
  `docs/execution-plan.md` (Phase 12, Current State, Task Tracking, PR-48)

## Execution plan delta

- **Phase 12** — M48 (SMTP/templates/CI), M49 (admin client + audit ingest + guards),
  M50 (DM `/admin/users*`), M51 (DM frontend users + auth UX), M52 (e2e/OpenAPI/gate).
  28 tasks, TDD-ordered, all `pending`.

## Handoff to 07-build

- Operator: verify **Resend domain** + set `SUPABASE_SMTP_PASS` before live invite delivery.
- Modal: add `SUPABASE_SECRET_KEY` to data-management secret; redeploy after 07-build.
- `supabase config push` on `main` after templates land (requires `SUPABASE_ACCESS_TOKEN` in CI).

## Addendum — scope addition (2026-06-29, re-run of 04-tech-plan)

User reviewed the F35 plan and **added four items** via interview (recommended defaults shown were
accepted, except where noted). MFA/2FA and bulk CSV import remain **deferred**. Authored **ADR-031**
(TP-S005-17–24) and appended **M53 (T53.1–T53.22)** to Phase 12.

| Addition | Decision | Interview choice |
|----------|----------|------------------|
| Idle/session timeout | 30-min inactivity + 60s warning modal → local sign-out; `VITE_VECINITA_IDLE_TIMEOUT_MIN/_WARNING_SEC` (TP-S005-17) | `30_warn` |
| Log out everywhere | Self global `signOut()` **+ admin force-logout** `POST /admin/users/{id}/signout` via `admin_delete_user_sessions` RPC (TP-S005-18/19) | `self_plus_admin` |
| Deliverability test-send | `POST /admin/email/test` via **Resend REST** (`RESEND_API_KEY`/`RESEND_SENDER_EMAIL`), 5/h/admin, SPF/DKIM/DMARC checklist (TP-S005-22/23) | `resend_rest` |
| Audit viewer | Reuse F29 AuditPage + `GET /internal/v1/audit`; add `entity_type` "Users" filter, `user.*`/`email.*` i18n labels, per-user "View activity" link (TP-S005-21) | `enhance_existing` |
| User search + pagination | Server-side `q` (≥3 chars → GoTrue `filter`) + `page`/`page_size` + shared `PaginationControls` (TP-S005-20) | `server_filter` |

**Pre-built solutions verified 2026-06-29:** supabase-js `signOut` scopes (global default); GoTrue
`listUsers` `filter` ≥3 chars (PR #1741); GoTrue `POST /logout` revokes refresh tokens (no first-class
"revoke another user" REST endpoint → `auth.sessions` RPC chosen, one-time operator apply); Resend
REST `POST /emails`. **No new dependencies** (httpx + already-pinned supabase-js cover it).

**New artifacts/updates:** ADR-031; execution-plan M53 + Current State + Task Tracking + gate;
api-contract (`q`, `/signout`, `/admin/email/test`); config-spec (idle env, Resend REST secrets,
search rule); user-journeys UJ-034–UJ-038; test-plan TC-096–TC-103; acceptance-criteria AC-U10–AC-U16;
decisions.md TP-S005-17–24; staging-secrets-matrix (`RESEND_API_KEY`/`RESEND_SENDER_EMAIL`, DNS
checklist, RPC apply step); dependency-inventory (no-new-deps note); ADR index.

**New handoff items for 07-build / operator:** apply the `admin_delete_user_sessions` RPC to the
Supabase project (one-time, runbook); add `RESEND_API_KEY` + `RESEND_SENDER_EMAIL` to the Modal DM
secret; verify SPF/DKIM/DMARC on the Resend domain (test-send button is the verifier).

## Next stage

evolve-lite skips 05-verify-tech/06-tech-tooling → **07-build** (Phase 12, M48→**M53**).

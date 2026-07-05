---
session_id: S005-user-mgmt-auth
type: feature
status: in_progress
branch: feat/S005-user-mgmt-auth
started_at: 2026-06-29
intent: "Extend F34 admin auth — user management page (invite/list/role/resend/revoke/disable), remember-me login toggle, Resend SMTP + versioned email templates synced via Supabase CI/CD."
orchestrator: 16-evolve
evolve_cycle_id: EV-006
linked_issues: [75]
context_briefs: [docs/sessions/S000-internal-docs-archive/context-brief.md#16-ev-006-admin-user-mgmt-auth-ux]
standing_docs_touched: [docs/sessions/S000-internal-docs-archive/context-brief.md]
parent_session: S004-supabase-auth
---

# S005 — Admin user management + auth UX — EV-006

## Intent

Extend **F34** (Supabase admin auth, merged via PR #100) with operator-facing auth
enhancements requested 2026-06-29:

1. **User management page** in the admin dashboard — invite, list, change role, resend invite,
   revoke (delete), and disable (ban) users.
2. **"Remember me"** checkbox on the login screen — checked persists session in `localStorage`
   (survives browser restart); unchecked uses `sessionStorage` (cleared when tab closes).
3. **Production email delivery** via **Resend SMTP** + **versioned HTML email templates** in
   repo, synced to Supabase on merge via existing `supabase.yml` CI (`config push`).

## Scope (in)

| Area | Deliverable |
|------|-------------|
| DM UI | `/users` route + sidebar nav; invite form (email + role); user table; role change; resend/revoke/disable actions; admin-only write gates |
| DM API | New admin-only endpoints wrapping Supabase Admin API (`inviteUserByEmail`, `listUsers`, `updateUserById`, `deleteUser`, ban) — **service-role key server-side only** |
| Login UX | Remember-me checkbox; storage adapter chosen before `createClient`; preference persisted in `localStorage` key `vecinita.auth.remember` |
| Supabase config | Enable `[auth.email.smtp]` for Resend; add `[auth.email.template.*]` + `[auth.email.notification.*]` HTML under `supabase/templates/` |
| CI/CD | Extend `scripts/check_supabase_config.sh` + `supabase.yml` validate job to lint template paths; `config push` on main includes template HTML (CLI ≥ PR #5686) |
| Specs | Delta to `feature-list.md` (F35), `user-journeys.md`, `test-plan.md`, `acceptance-criteria.md`, `config-spec.md`, `staging-secrets-matrix.md` |

## Scope (out)

- ChatRAG visitor authentication (unchanged — anonymous).
- OAuth / social login providers.
- RBAC beyond `admin` + `viewer`.
- Operator PII in the Vecinita corpus DB (identity stays in Supabase only).
- Self-service password reset UI (recovery template + SMTP enable delivery; reset flow via email link only unless added in 01-requirements).
- Bulk user import / CSV.

## Key decisions (AskQuestion 2026-06-29)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Session | **Close S004** (defer deploy-verify); **open S005** | F34 merged to main (#100); new work is a clean EV-006 delta |
| 2 | SMTP provider | **Resend** | Modern API, good Supabase integration docs, free tier for small teams |
| 3 | User mgmt ops | invite, list, change_role, resend, revoke, disable | Full admin lifecycle without Supabase Dashboard |
| 4 | Email templates | invite, recovery, confirmation, magic_link, email_change, notifications | Version all auth + security notification templates in repo |
| 5 | Remember me | **Toggle** — `localStorage` vs `sessionStorage` | Standard UX; supabase-js has no native flag (auth-js #571) |

## Pre-built / native solutions (research)

| Need | Solution | Notes |
|------|----------|-------|
| Invite / list / role / ban | Supabase **Admin API** (`auth.admin.*`) via **DM backend** | Service-role key never exposed to browser |
| Remember me | Custom **storage adapter** at `createClient` init | No official supabase-js remember-me API |
| Email templates | **`config.toml` `content_path`** + HTML in `supabase/templates/` | `supabase config push` uploads HTML (CLI PR #5686, 2026-06-25) |
| SMTP | **`[auth.email.smtp]`** in `config.toml` → Resend SMTP credentials | Built-in Supabase email is rate-limited / non-production |
| CI sync | Existing **`.github/workflows/supabase.yml`** | Extend validate + sync-production jobs |

## Dependencies

- **F34 merged** on `main` (PR #100) — login, JWT verify, roles, invite-only config.
- **Resend account** + domain verification (operator — `prod.env` / GitHub secrets).
- **Supabase CLI** recent enough for template HTML push (pin in CI if needed).

## Routing plan

See [routing-plan.md](./routing-plan.md). Lite evolve path. **01-requirements complete**
(2026-06-29, RD-080–RD-090; ADR-029; F35; UJ-030–UJ-033; TC-088–TC-095; AC-U1–AC-U9 —
[report](./reports/01-requirements.md)). **04-tech-plan complete**
(2026-06-29, ADR-030, TP-S005-01–16; Phase 12 M48–M52 —
[report](./reports/04-tech-plan.md)); handoff to **07-build** next.

## Links

- Parent: [S004 session brief](../S004-supabase-auth/session-brief.md)
- Standing: [context-brief.md §16](../../sessions/S000-internal-docs-archive/context-brief.md), [feature-list.md](../../feature-list.md),
  [ADR-026](../../adr/ADR-026-supabase-admin-auth.md), [ADR-027](../../adr/ADR-027-supabase-auth-verification-and-env-sync.md)
- Issue: [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75) (auth umbrella)

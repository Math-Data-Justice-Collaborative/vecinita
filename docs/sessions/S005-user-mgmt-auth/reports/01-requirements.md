---
session_id: S005-user-mgmt-auth
stage: 01-requirements
evolve_cycle_id: EV-006
feature_ids: [F35]
status: completed
date: 2026-06-29
---

# 01-requirements report — EV-006 / F35 (admin user management + auth UX)

Delta requirements interview on the F34 Supabase admin-auth foundation. Confirmed 00-context
decisions R55–R59, researched pre-built solutions, resolved one **[Contradiction]** and one
**[Ambiguity]**, and produced spec deltas across the affected artifacts.

## Research (pre-built / native solutions, verified 2026-06-29)

| Need | Solution | Verification |
|------|----------|--------------|
| Invite/list/role/disable/delete | Supabase **Admin API** (`auth.admin.*`), server-side only | Standard; secret key never in browser |
| Versioned email templates | `[auth.email.template.*]` `content_path` + `supabase config push` | CLI [PR #5686](https://github.com/supabase/cli/pull/5686) merged 2026-06-25; path gotcha [#5124](https://github.com/supabase/cli/issues/5124) |
| SMTP | Resend (`smtp.resend.com:465`, user `resend`) via `[auth.email.smtp]` | Resend↔Supabase docs |
| Remember-me | supabase-js `storage` adapter (no native flag) | auth-elements #7; storage chosen before `createClient` |

## Decisions (RD-080–RD-090)

User-mgmt ops (invite/list/role/resend/disable/revoke/admin-reset); self-service reset (in-app
link); remember-me default **checked** (`localStorage` vs `sessionStorage`, key
`vecinita.auth.remember`); **hybrid** Resend SMTP (config.toml is source of truth) — resolves the
Dashboard-vs-CI contradiction; **6 stacked-bilingual** templates; CI sync via `supabase.yml` with a
**pinned CLI**; audit of user-mgmt actions; operator-supplied verified Resend domain. See
`docs/decisions.md` §EV-006 resolutions.

## Artifacts updated

| Doc | Change |
|-----|--------|
| `docs/adr/ADR-029-admin-user-management-and-auth-ux.md` | **New ADR** |
| `docs/feature-list.md` | New **F35** (summary, matrix, detail, out-of-scope reconciliation) |
| `docs/decisions.md` | **EV-006 resolutions** RD-080–RD-090 |
| `docs/user-journeys.md` | **UJ-030–UJ-033** |
| `docs/test-plan.md` | **TC-088–TC-095** + UJ→test mapping |
| `docs/api-contract.md` | **`/admin/users*`** namespace + auth row |
| `docs/config-spec.md` | SMTP/template config, `SUPABASE_SECRET_KEY`/`SUPABASE_SMTP_PASS`, `vecinita.auth.remember`, validation rules |
| `docs/acceptance-criteria.md` | **AC-U1–AC-U9** |
| `docs/staging-secrets-matrix.md` | **EV-006** secrets + operator prerequisites/runbook delta |

## Handoff to 04-tech-plan (unresolved)

- Host backend for `/admin/users*` (DM Modal ASGI vs internal-write DO) + least-privilege
  placement of `SUPABASE_SECRET_KEY` in a running service.
- Exact `content_path` strings (#5124 root vs `supabase/`) + pinned Supabase CLI version.
- supabase-js storage-adapter pattern for remember-me re-init on toggle.
- Supabase `auth.rate_limit.email_sent` + invite/recovery link expiry values.

## Notes / advisories

- `docs/sessions/S000-internal-docs-archive/execution-plan.md` §Current State is stale (still S004/Phase 11) — should be advanced for
  S005/EV-006 (flagged to workflow-state).
- Commit deferred per the standing commit-only-when-asked override (same as S004).

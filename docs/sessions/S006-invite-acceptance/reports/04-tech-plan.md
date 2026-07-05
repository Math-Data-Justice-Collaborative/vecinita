---
session_id: S006-invite-acceptance
stage: 04-tech-plan
evolve_cycle_id: EV-007
feature_ids: [F35]
status: completed
date: 2026-06-30
linked_issues: [109]
---

# 04-tech-plan report — EV-007 / F35 invite acceptance (#109)

Resolved every technical decision 01-requirements deferred for EV-007, authored **ADR-032**,
and appended **Phase 13 (M54–M58, T54.1–T54.24)** to the execution plan. Implementation
captured as tasks only (no product source written in this planning stage).

## Interview outcome

Requirements interview (01-requirements) locked RD-091–RD-098 on 2026-06-30. Technical
planning applied **recommended defaults** from gap analysis (`docs/sessions/S000-internal-docs-archive/context/invite-acceptance-flow.md`)
and #109 root-cause table — documented as TP-S006-01–16 in ADR-032.

## Pre-built solutions (verified 2026-06-30)

| Need | Solution | Notes |
|------|----------|-------|
| Backend `redirect_to` | Existing `supabase_admin.invite_user_by_email(..., redirect_to=)` | Call sites never passed param |
| Auth callback | supabase-js `detectSessionInUrl` + **explicit `useAuthLinkCallback` hook** | Waits for session; parses `#error=` |
| PKCE `code` param | `exchangeCodeForSession` in hook | Fallback when hash tokens absent |
| Retract invite | GoTrue `delete_user` for `status=invited` only | No native revoke API |
| Supabase redirect config | `config.toml` + `config push` via `supabase.yml` | Staging-first `site_url` (RD-094) |
| Self-service recovery redirect | `window.location.origin + '/reset-password'` | Already in `ForgotPasswordPage` |
| Admin recovery redirect | Backend `redirect_to` via `VECINITA_ADMIN_FRONTEND_URL` | New Modal DM secret |
| Expired link UX | Bilingual i18n error panel | AC-U20 |
| Invite metadata | `created_at` → `invited_at` + client "~1h" hint | RD-096 |

## Decisions (TP-S006-01–16)

See [ADR-032](../../adr/ADR-032-ev007-invite-acceptance-implementation.md). Summary:

| ID | Decision |
|----|----------|
| TP-S006-01 | New ADR-032; ADR-030 §5 superseded for callback behaviour |
| TP-S006-02 | `VECINITA_ADMIN_FRONTEND_URL` on Modal DM; 503 when unset |
| TP-S006-03 | Shared `build_auth_redirect_path` helper for three backend call sites |
| TP-S006-04 | Staging-first `site_url` + full-path `additional_redirect_urls` |
| TP-S006-05 | `useAuthLinkCallback` hook — hash/code/error parsing + session gate |
| TP-S006-06 | Bilingual expired-link error panel (AC-U20) |
| TP-S006-07 | `POST /admin/users/{id}/revoke-invite` → delete invited-only + audit |
| TP-S006-08 | Resend uses `invite_user_by_email` + `redirect_to` (OTP refresh) |
| TP-S006-09 | `invited_at` + client-side "~1h expiry" hint on pending rows |
| TP-S006-10 | Keep Supabase SMTP for invite/recovery (RD-091) |
| TP-S006-11 | CORS + OpenAPI for revoke-invite |
| TP-S006-12 | Branch `feat/S006-invite-acceptance`, PR-49 |
| TP-S006-13 | Redeploy order: config push → Modal secret → modal deploy → FE → smoke |
| TP-S006-14 | Template polish (invite + recovery HTML) |
| TP-S006-15 | T2 merge-blocking; T3 live smoke at 13-deploy-smoke |
| TP-S006-16 | No new dependencies |

## Artifacts produced / updated

- **New**: `docs/adr/ADR-032-ev007-invite-acceptance-implementation.md`
- **Updated**: `docs/decisions.md` (TP-S006), `docs/staging-secrets-matrix.md` (EV-007 section),
  `docs/sessions/S000-internal-docs-archive/execution-plan.md` (Phase 13, Current State, Task Tracking, PR-49),
  `docs/adr/README.md` (ADR-032 index entry)

## Execution plan delta

- **Phase 13** — M54 (Supabase redirect config + env), M55 (backend redirect_to + revoke),
  M56 (frontend auth callback), M57 (admin UI lifecycle), M58 (templates + e2e + runbook).
  24 tasks, TDD-ordered, all `pending`, tagged `evolve_cycle_id: EV-007`.

## Handoff to 07-build

1. **Operator prerequisite:** Resend domain verified (BUG-2026-06-30-email-test-send); SPF/DKIM/DMARC.
2. **Modal secret:** add `VECINITA_ADMIN_FRONTEND_URL` to `vecinita-data-management` before deploy.
3. **Supabase:** merge triggers `config push`; verify Dashboard Auth URLs after sync.
4. **Implementation order:** M54 → M55 → M56 → M57 → M58 (matches #109 suggested order).

## Next stage

evolve-lite skips 05-verify-tech/06-tech-tooling → **07-build** (Phase 13, M54→M58).

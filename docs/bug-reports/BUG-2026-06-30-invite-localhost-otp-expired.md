# BUG-2026-06-30 — Invite email redirects to localhost:3000 with otp_expired

**Status:** fixed (pending user browser verify on fresh invite)
**Severity:** critical (operators cannot onboard invitees)
**Feature:** S006/EV-007 F35 — invite acceptance redirect (ADR-032)
**Reported:** 2026-06-30
**Branch:** (config hotfix — pending)

## Error description

Fresh admin invite email link opens:

```
http://localhost:3000/#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired&sb=
```

instead of the staging admin frontend `/accept-invite`. Invitee cannot set a password.

## Repro

1. Admin sends invite from `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/users`.
2. Invitee opens the link in the email (fresh send, within minutes).
3. **Expected:** `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/accept-invite` with session or bilingual expired UX.
4. **Actual:** Browser lands on `localhost:3000` with `#error=otp_expired`.

## Error logs

User callback URL (2026-06-30):

```
http://localhost:3000/#error=access_denied&error_code=otp_expired&error_description=Email+link+is+invalid+or+has+expired&sb=
```

| Field | Value |
|-------|-------|
| Env | Staging/production (live Supabase project) |
| Entry | Invite email → Accept invitation link |
| Supabase project | `cfuvghdsuwactfeamtym` |
| When | After EV-007 merge (#110); persists on fresh invites |

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-30 | User report: callback still `localhost:3000` + `otp_expired`. |
| 2026-06-30 | Repo `supabase/config.toml` has correct staging `site_url` and redirect allowlist (TC-109). |
| 2026-06-30 | CI run `28484619671` (main, #110): `sync-production` **skipped** — log: `SUPABASE_ACCESS_TOKEN not configured — skipping production sync`. |
| 2026-06-30 | `deploy-modal.yml` `supabase-sync` job also skipped for same reason (run `28486178025`). |
| 2026-06-30 | Live project auth config never received `config push`; Dashboard likely still has default `site_url = http://localhost:3000`. |
| 2026-06-30 | `otp_expired` on wrong host: GoTrue error redirect uses `site_url` when verification fails or token consumed; Resend **link tracking** can prefetch single-use links (Resend KB + Supabase troubleshooting). |
| 2026-06-30 | Backend `redirect_to` + `VECINITA_ADMIN_FRONTEND_URL` fixed separately (BUG-2026-06-30-auth-redirect-unconfigured); Modal secret now includes admin FE URL. |

**Root cause:** Config/infra — `SUPABASE_ACCESS_TOKEN` absent from GitHub secrets and `prod.env`, so live Supabase `site_url` / redirect allowlist were never synced from repo.

**Secondary risk:** Resend link/open tracking on `josephcmcg.com` may consume OTP before user click (disable per Resend Supabase deliverability guide).

**Classification:** Config/infra (primary); possible Resend operator setting (secondary).

## Spec conformance

| Check | Result |
|-------|--------|
| `[Spec: config-spec.md §site_url]` | Repo correct; live project drift — **implementation/deploy drift** |
| `[Spec: ADR-032 §4, §13]` | Redeploy step 1 (`config push`) not executed — operator gap |
| `[Spec: staging-runbook.md §EV-007]` | Requires token + Dashboard verify — pending |
| F35 EV-007 | In scope |

No blocking spec contradiction.

## Repro test

- Path: `tests/smoke/test_supabase_ci_contract.py` — TC-109 (offline contract; proves repo intent, not live drift)
- Live drift guard: `scripts/supabase/verify_live_auth_urls.sh` (pending token)

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 2 | 2026-07-01 | `generate_link` probe with SUPABASE_SECRET_KEY | RED — redirect_to=localhost:3000 |
| 3 | 2026-07-01 | PATCH site_url + `supabase config push` (partial; auth applied) | GREEN — redirect_to=staging /accept-invite |

## Fix

Applied live Supabase auth URL config (2026-07-01):

1. `SUPABASE_ACCESS_TOKEN` added to `prod.env`; synced to GitHub Actions via `sync_github_secrets.sh --apply`.
2. `bash scripts/supabase/ci_sync.sh sync-production` — auth redirect allowlist + site_url synced from `config.toml`.
3. Verified with `scripts/supabase/verify_live_auth_urls.sh` and `scripts/supabase/check_live_invite_redirect.sh` (uses project secret key).

**Note:** `config push` returned a non-blocking Storage schema error at end; auth section applied successfully.

## Verification plan

| Check | Layer | Result |
|-------|-------|--------|
| Live site_url = staging admin | L2 API | pass |
| Live uri_allow_list includes /accept-invite | L2 API | pass |
| generate_link honors redirect_to | L2 API | pass |
| Fresh invite email → staging /accept-invite | L2 browser | **pending user** |
| Password set + login | L2 browser | pending user |

## Interview record

| Question | Answer |
|----------|--------|
| Intent | Config push + verify (user provides token) |
| Symptom | localhost:3000 + otp_expired on invite link |
| Remediation | Local-first — user confirms after config push |

## Prevention & countermeasures

(pending Phase 5)

## Cursor rule

(pending Phase 5.1)

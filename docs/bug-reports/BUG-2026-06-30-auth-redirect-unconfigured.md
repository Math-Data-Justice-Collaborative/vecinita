# BUG-2026-06-30 — auth_redirect_unconfigured on admin invite

**Status:** resolved
**Severity:** critical (invites blocked)
**Feature:** S006/EV-007 F35 — user invite redirect (ADR-032)
**Reported:** 2026-06-30
**Branch:** (config hotfix — no code branch)

## Error description

POST `/admin/users/invite` from the production admin frontend returns HTTP 503 with:

```json
{"detail":{"code":"auth_redirect_unconfigured","message":"VECINITA_ADMIN_FRONTEND_URL is not configured"}}
```

Admin cannot invite users.

## Repro

1. Open `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/` (authenticated as admin).
2. POST invite for a new email (e.g. `joseph.c.mcg@gmail.com`, role `admin`).
3. **Expected:** `201` with invited user; GoTrue email with `redirect_to=…/accept-invite`.
4. **Actual:** `503` `auth_redirect_unconfigured`.

## Error logs

Browser fetch (production):

```
POST https://vecinita--vecinita-data-management-fastapi-app.modal.run/admin/users/invite
Referrer: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/
Response: {"detail":{"code":"auth_redirect_unconfigured","message":"VECINITA_ADMIN_FRONTEND_URL is not configured"}}
```

Modal secret export (2026-06-30):

```
keys=['SUPABASE_SECRET_KEY', 'SUPABASE_URL', 'VECINITA_AUTH_REQUIRED', 'VECINITA_CORS_ORIGINS',
'VECINITA_INTERNAL_API_KEY', 'VECINITA_INTERNAL_WRITE_URL', 'VECINITA_MODAL_EMBED_URL',
'VECINITA_MODAL_LLM_URL', 'VECINITA_MODAL_PROXY_KEY']
```

`VECINITA_ADMIN_FRONTEND_URL` **absent** from live `vecinita-data-management` secret.

| Field | Value |
|-------|-------|
| Env | Production |
| Entry | Admin Users → Invite |
| Modal app | vecinita-data-management-fastapi-app |
| Admin FE origin | `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app` |
| When | After EV-007 deploy; every invite attempt |

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-30 | User report: 503 on invite with `auth_redirect_unconfigured`. |
| 2026-06-30 | Code path: `user_admin_routes._require_auth_redirect()` → `admin_frontend_origin_from_env()` raises when env unset (by design, ADR-032 §2). |
| 2026-06-30 | Live Modal secret export confirms key missing; `prod.env` also lacks `VECINITA_ADMIN_FRONTEND_URL`. |
| 2026-06-30 | T54.4 marked completed in execution plan but operator secret sync was not applied. |
| 2026-06-30 | `sync_modal_secret.sh` lists key under OPTIONAL_KEYS — only pushed when present in shell env. |

**Root cause:** Config/infra — `VECINITA_ADMIN_FRONTEND_URL` never synced to Modal `vecinita-data-management` secret after EV-007 implementation.

**Classification:** Config/infra (not code bug).

## Spec conformance

| Check | Result |
|-------|--------|
| `[Spec: api-contract.md §POST /admin/users/invite]` | 503 when env unset — **pass** (code matches spec) |
| `[Spec: config-spec.md VECINITA_ADMIN_FRONTEND_URL]` | Required at runtime on Modal DM — **implementation drift in deploy** |
| `[Spec: staging-runbook.md §Redeploy order]` | Step 3 secret sync not executed — operator gap |
| F35 EV-007 scope | In scope |

No blocking spec contradiction.

## Repro test

- Path: `tests/unit/data_management/test_user_admin_routes.py::test_invite_returns_503_when_admin_frontend_url_unset` (TC-104)
- Assertion: unset env → POST `/admin/users/invite` → `503`
- Encodes production failure mode (missing env); fix verified by secret sync + live re-invite (not unit test inversion)

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-30 | Run TC-104 existing test | GREEN — confirms 503 when env unset (matches prod symptom) |

## Remediation path

Local-first (user choice 2026-06-30). Prepare secret sync locally; deploy after user approval.

## Verification plan

| Item | Choice |
|------|--------|
| Success criterion | Original 503 gone — invite returns 201 |
| Checks | Unit + user repro (re-POST invite in admin UI) |
| Monitoring | User watches production |

## Fix

Applied 2026-06-30:

1. Added to `prod.env` (gitignored):
   `VECINITA_ADMIN_FRONTEND_URL=https://vecinita-admin-frontend-ef4ob.ondigitalocean.app`
2. `bash scripts/deploy/sync_modal_secret.sh --merge --apply` — secret now includes
   `VECINITA_ADMIN_FRONTEND_URL`, `RESEND_API_KEY`, `RESEND_SENDER_EMAIL`
3. `bash scripts/deploy/modal.sh` — vecinita-data-management redeployed

## Verification

### Layer 1 — Automated
- [x] TC-104 repro test passes (503 when env unset locally)
- [x] Modal secret export confirms `VECINITA_ADMIN_FRONTEND_URL` present post-sync

### Layer 4 — Production
- [x] User re-POST invite in admin UI → 201 (confirmed 2026-06-30)

## Interview record

| Question | Answer |
|----------|--------|
| Intent | New issue |
| Symptom | 503 auth_redirect_unconfigured on invite |
| Where | Production Modal DM + DO admin FE |
| When | After EV-007 deploy |
| Frequency | Every time |
| Severity | Critical |
| Remediation | Local-first |

## Prevention & countermeasures

| Item | Decision |
|------|----------|
| Recurrence risk | Optional Modal secret keys can be missed when task marked complete without operator sync |
| Detection | staging-runbook §Redeploy order step 3 documents sync; verify secret after EV-007-style deploys |
| Follow-up | Deploy preflight check for `VECINITA_ADMIN_FRONTEND_URL` in Modal secret (deferred) |

## Cursor rule

Declined / deferred — config operator gap, not a code pattern.

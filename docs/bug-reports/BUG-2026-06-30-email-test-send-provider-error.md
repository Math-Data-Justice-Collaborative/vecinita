# BUG-2026-06-30 — Send test email returns Email provider error

> Status: **fixing**  
> Feature: **F35** (admin user management — deliverability test-send, ADR-031 TP-S005-22)  
> Component: `apps/data-management-backend/vecinita_data_management_backend/email_test.py`, `user_admin_routes.py`, Resend operator config

## Error description

On the admin **Users** tab, clicking **Send test email** fails with HTTP 502 and body `{"detail":"Email provider error"}` instead of delivering mail or showing an actionable operator message.

Production URL: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/users  
API: `POST https://vecinita--vecinita-data-management-fastapi-app.modal.run/admin/email/test`  
Payload: `{"to":"joseph.c.mcg@gmail.com"}`

## Error logs

```text
# User report (browser fetch) — 502
{"detail":"Email provider error"}

# Agent repro — direct Resend REST (same API key + sender as Modal secret)
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"noreply@vecinita.admin","to":["joseph.c.mcg@gmail.com"],"subject":"test","html":"<p>test</p>"}'

HTTP 403
{"statusCode":403,"message":"The vecinita.admin domain is not verified. Please, add and verify your domain on https://resend.com/domains","name":"validation_error"}
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Wrong output — generic provider error, no deliverability signal |
| Where | Production (DO admin FE → Modal DM → Resend) |
| When | After F35 / M53 deploy (test-send feature live) |
| Frequency | Every time (until domain verified) |
| Repro env | Production; reproducible locally with prod Resend key |
| Severity | High — cannot verify email deliverability; invites may also fail |
| Evidence | User fetch + agent Resend curl |
| Tried | Nothing reported |

## Remediation path

**local-first** — fix locally, PR, deploy after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `RESEND_API_KEY` / `RESEND_SENDER_EMAIL` unset on Modal → `503 email_unconfigured` | **Ruled out** — user got 502, not 503; Resend key works (API responds) |
| H2 | Invalid/expired Resend API key | **Ruled out** — would be 401 from Resend |
| H3 | Sending domain not verified in Resend | **Confirmed** — Resend 403 `validation_error` for `vecinita.admin` |
| H4 | CORS / proxy auth failure | **Ruled out** — request reached backend and Resend |

## Root cause

**Operator prerequisite not met (AC-U9 / RD-090):** the Resend sending domain `vecinita.admin` (sender `noreply@vecinita.admin` per `supabase/config.toml`) is **not verified** in the Resend dashboard. The backend maps all `ResendError` to opaque `502 {"detail":"Email provider error"}`, so the UI cannot guide the operator to DNS verification.

## Spec conformance

| Check | Result |
|-------|--------|
| `[Spec: api-contract.md §POST /admin/email/test]` | Documents 400/503/429; 502 provider errors not structured — **spec ambiguity** for operator-actionable Resend failures |
| `[Spec: staging-secrets-matrix.md §Operator prerequisites]` | Verified Resend domain is required — **implementation matches spec intent**, operator step incomplete |
| `[Spec: acceptance-criteria AC-U9]` | Domain verification documented; **pending operator completion** |

## Repro test

| Field | Value |
|-------|--------|
| Path | `tests/bugs/test_bug_2026_06_30_email_test_send_domain_unverified.py` |
| Status | green |
| Red run | 2026-06-30 — returned 502 `Email provider error` before fix |
| Green run | 2026-06-30 — returns 503 `domain_unverified` with Resend message |

## TDD iteration log

| # | Change | Result |
|---|--------|--------|
| 1 | Repro test + structured `domain_unverified` mapping | green |

## Fix

1. **`email_test.py`**: Parse Resend error JSON (`message`, `name`); add `resend_error_http_detail()` mapping 403 domain-not-verified → `503 domain_unverified`.
2. **`user_admin_routes.py`**: Use structured mapping before generic 502.
3. **Admin FE**: `EmailDomainUnverifiedError` + deliverability checklist alert on Users tab.
4. **Specs**: `api-contract.md`, `openapi/data-management.yaml` — document `domain_unverified`.

**Operator follow-up:** switched sender to verified `noreply@josephcmcg.com` (Resend domain `josephcmcg.com`) in `config.toml`, `prod.env`, and Modal secret sync. Supabase invite SMTP still requires `supabase config push` on the project.

## Verification plan

- **Success:** UI shows actionable domain-unverified message (not generic 502).
- **Checks:** Full local CI parity + PR branch CI after push.
- **Monitoring:** User watches production after deploy.

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] CI parity local (python unit/integration/bugs + DM frontend tests)

### Layer 2 — Reproduction

- [ ] Send test email succeeds after domain verified OR shows actionable error

### Layer 3 — Pre-deploy smoke

- [ ] pending

### Layer 4 — Production

- [ ] pending

## Prevention & countermeasures

_Pending Phase 5._

## Timeline

| When | Event |
|------|-------|
| 2026-06-30 | User report + agent Resend curl confirms unverified domain |

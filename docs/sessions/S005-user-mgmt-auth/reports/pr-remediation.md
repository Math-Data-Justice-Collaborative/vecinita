# PR remediation — PR #102 (PRM-008)

**Session:** S005-user-mgmt-auth  
**Linked review:** PRR-102  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/102  
**Branch:** `feat/S005-user-mgmt-auth`  
**Completed:** 2026-06-30

## Scope

Blockers + actionable advisories (user-selected).

## Findings

| ID | Severity | Path | Status | Commit |
|----|----------|------|--------|--------|
| F-001 | 🔴 blocker | `.github/workflows/supabase.yml` | fixed | `1b86353` |
| F-002 | 🟡 advisory | `user_admin.py` | fixed | `fb195cf` |

### F-001 — Mailpit smoke (CI validate)

Supabase CLI 2.84.2 serves Mailpit on port 54324; Inbucket `/api/v1/mailboxes` returned 404.
Updated validate job to curl `/api/v1/messages`; renamed step; refreshed ADR-030, decisions.md,
supabase/README.md.

### F-002 — count_active_admins pagination

Paginate GoTrue list (per_page=200) until a short page; added
`test_count_active_admins_paginates_beyond_first_page`.

## Deferred / won't fix (review body only)

- Large PR by design — no action
- Post-merge deploy runbook — 13-deploy-smoke
- Audit best-effort swallow — follow-up metrics/alerting

## CI

Post-push watch: `bash scripts/ci/watch_github_ci.sh feat/S005-user-mgmt-auth`

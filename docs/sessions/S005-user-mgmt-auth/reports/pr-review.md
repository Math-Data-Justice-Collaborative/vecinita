# PR review — #102 (18-pr-review)

**Date:** 2026-06-30  
**PR:** [Phase 12: EV-006 — Admin user management + auth UX (F35)](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/102)  
**Head:** `219bd4d` · `feat/S005-user-mgmt-auth` → `main`  
**Verdict:** REQUEST_CHANGES  
**Blockers:** 1 · **Advisories:** 4 · **Praise:** 3

## Summary

Full checklist review of EV-006/F35 (M48–M53). Implementation quality is strong — comprehensive tests, lockout guards, PII-free audit, OpenAPI/ADR coverage. One CI blocker: `supabase.yml` validate fails because the Inbucket API endpoint is obsolete under Supabase CLI 2.84.2 (Mailpit).

## Blocking

| # | Finding | Location |
|---|---------|----------|
| 1 | Inbucket `/api/v1/mailboxes` returns 404; Mailpit API required | `.github/workflows/supabase.yml:63` |

## Advisory

- `count_active_admins()` single-page scan (200 cap)
- Large PR size (by design)
- Post-merge deploy items deferred correctly
- Audit emit best-effort swallow

## CI

- `ci.yml`: green (python, frontend, coverage)
- `supabase.yml validate`: **red**
- Local guards: OpenAPI, operator-spec, Modal DB URL — pass

## Subagents

Bugbot and Security review subagents could not compute branch diff; manual review performed on auth routes, RPC migration, and supabase_admin client.

## Posted

- Inline comments on GitHub (supabase.yml, user_admin.py)
- Review body via `gh pr review --request-changes`

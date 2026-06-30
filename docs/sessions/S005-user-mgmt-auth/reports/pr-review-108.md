# PR review — #108 (18-pr-review)

**Date:** 2026-06-30  
**PR:** [fix(admin): avoid duplicate GoTrueClient on login submit](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/108)  
**Head:** `53131f3` · `fix/BUG-2026-06-30-gotrue-multiple-instances-login` → `main`  
**Verdict:** APPROVE  
**Blockers:** 0 · **Advisories:** 2 · **Praise:** 3

## Summary

Hotfix for BUG-2026-06-30: duplicate GoTrueClient console warning on admin login submit. Targeted singleton lifecycle fix with `useSyncExternalStore` re-bind when remember-me storage routing actually changes. CI green; local auth tests pass (16/16).

## Advisory

| # | Finding | Lens |
|---|---------|------|
| 1 | Regression test covers module singleton, not full AuthProvider→LoginPage submit path | Staff Frontend |
| 2 | PR test plan manual staging verify still unchecked | Community Partner |

## CI

- `ci.yml`: green (python, frontend matrix, coverage) on `53131f3`
- Local: bug regression + remember-me + auth context + supabase client tests — 16/16 pass

## Subagents

- Bugbot: no bugs
- Security: no medium+ issues; optional pre-existing hardening (clear opposite storage on remember toggle) noted out of scope

## Posted

- 1 advisory inline comment (test integration coverage)
- Review body via `gh pr review --approve`

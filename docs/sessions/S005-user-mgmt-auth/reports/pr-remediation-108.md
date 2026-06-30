# PR remediation — PR #108 (PRM-009)

**Session:** S005-user-mgmt-auth  
**Linked review:** PRR-011  
**PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/108  
**Branch:** `fix/BUG-2026-06-30-gotrue-multiple-instances-login`  
**Completed:** 2026-06-30

## Scope

Blockers + advisories (user-selected). No blockers on intake (verdict APPROVE).

## Findings

| ID | Severity | Path | Status | Commit |
|----|----------|------|--------|--------|
| F-001 | 🟡 advisory | `test_bug_2026_06_30_gotrue_multiple_instances_login.test.tsx` | fixed | `30cb9bf` |
| F-002 | 🟡 advisory | review body (staging verify) | deferred | — |

### F-001 — AuthProvider integration coverage

Added `AuthProvider.signIn` integration test with hoisted `createClient` mock. Asserts
only one `createClient` call across mount + signIn when `remember=true` is unchanged —
guards the original login-submit symptom path. GitHub thread resolved.

### F-002 — Manual staging verify

Deferred to post-merge operator spot-check: open staging admin login, submit credentials,
confirm no GoTrueClient duplicate warning in DevTools. Not merge-blocking.

## CI

Post-push watch on `30cb9bf`: `ci.yml` **success** (python, frontend matrix, coverage).

## Follow-up

- Post-merge: staging login console check (F-002)
- Optional: run **18-pr-review** re-review on PR #108

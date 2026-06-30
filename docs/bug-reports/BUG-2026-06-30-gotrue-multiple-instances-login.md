# BUG-2026-06-30 — Multiple GoTrueClient instances on admin login

**Status:** fixed locally (pending user verify + PR)
**Severity:** low (console warning; login succeeds)
**Feature:** S005 — user management / auth (`apps/data-management-frontend`)
**Reported:** 2026-06-30
**Branch:** `fix/BUG-2026-06-30-gotrue-multiple-instances-login`

## Error description

On the admin **Login** page (data-management frontend, staging), submitting the login form
prints a Supabase auth warning in the browser console. Login still works.

```
GoTrueClient@sb-cfuvghdsuwactfeamtym-auth-token:1 (2.108.2) … Multiple GoTrueClient
instances detected in the same browser context. It is not an error, but this should be
avoided as it may produce undefined behavior when used concurrently under the same storage key.
```

Stack trace points at `onSubmit` on the login form (`LoginPage` → `signIn`).

## Repro

1. Open staging admin frontend login (unauthenticated).
2. Open DevTools → Console.
3. Enter valid credentials and click **Sign in**.
4. **Expected:** no GoTrueClient duplicate-instance warning.
5. **Actual:** warning on every submit (before redirect).

## Error logs

```
installHook.js:1 GoTrueClient@sb-cfuvghdsuwactfeamtym-auth-token:1 (2.108.2) 2026-06-30T20:07:23.501Z Multiple GoTrueClient instances detected in the same browser context. It is not an error, but this should be avoided as it may produce undefined behavior when used concurrently under the same storage key.
overrideMethod @ installHook.js:1
…
onSubmit @ index-BgW_0fIy.js:77
```

| Field | Value |
|-------|-------|
| Env | Staging admin FE |
| Entry | Login form submit |
| Supabase project | `cfuvghdsuwactfeamtym` (from storage key) |
| When | First login after deploy |

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-30 | `AuthProvider` mounts → `getSupabaseClient()` creates client A + `onAuthStateChange` subscription. |
| 2026-06-30 | `signIn()` always calls `resetSupabaseClient(remember)` → `createClient()` again → client B. |
| 2026-06-30 | Client A remains alive (subscription closure); both use storage key `sb-<project>-auth-token`. |
| 2026-06-30 | `resetSupabaseClient` was added for remember-me routing (`localStorage` vs `sessionStorage`). |

**Root cause:** Code bug — unconditional client rebuild on every `signIn`, leaving the
mount-time GoTrueClient instance active.

**Classification:** domain / integration (auth client lifecycle), not connectivity.

## Spec conformance

| Check | Result |
|-------|--------|
| S005 auth scope | In scope — admin frontend Supabase auth |
| Remember-me (UJ-032 / TC-091) | Must preserve storage routing behavior |

No blocking spec drift.

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_06_30_gotrue_multiple_instances_login.test.tsx`
- Assertion: `createClient` called once across mount + login when remember preference unchanged.
- Red: current code calls `createClient` twice.
- Green: after skip-rebuild + AuthProvider re-bind when remember changes.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-30 | Unit repro — `resetSupabaseClient(true)` after `getSupabaseClient()` | RED — returned new instance (2× `createClient`) |
| 2 | 2026-06-30 | Skip rebuild when `clientRemember` matches; `useSyncExternalStore` re-bind on real rebuild | GREEN |

## Remediation path

Local-first (user choice 2026-06-30). Frontend patch; staging deploy after PR.

## Fix

- `supabaseClient.ts`: track `clientRemember`; `resetSupabaseClient` no-ops when preference unchanged;
  bump `clientVersion` + notify subscribers only when storage routing actually changes.
- `AuthContext.tsx`: `useSyncExternalStore` on client version so `onAuthStateChange` unsubscribes before rebuild.
- Test: `apps/data-management-frontend/src/test/test_bug_2026_06_30_gotrue_multiple_instances_login.test.tsx`

## Interview record

| Question | Answer |
|----------|--------|
| Intent | New bug |
| Symptom | Console warning only; login works |
| Where | Staging admin frontend |
| When started | First login after deploy |
| Frequency | Every login submit |
| Severity | Low |
| Remediation | Fix locally first |

## Prevention & countermeasures

(pending Phase 5)

## Cursor rule

(pending Phase 5.1)

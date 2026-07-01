# BUG-2026-06-30 — PKCE double-exchange race on invite callback

**Status:** fixed locally (pending PR #110 remediation)
**Severity:** high (valid invite links show invalid-link UI)
**Feature:** S006 / EV-007 — invite acceptance (`useAuthLinkCallback`)
**Reported:** 2026-06-30 (18-pr-review / Bugbot on PR #110)
**Branch:** `feat/S006-invite-acceptance`

## Error description

On `/accept-invite?code=…`, the password form may never appear even when the invite link is
valid. `useAuthLinkCallback` calls `exchangeCodeForSession` while the singleton Supabase client
(`detectSessionInUrl: true`) and `AuthProvider.getSession()` may already have consumed the PKCE
code. The failed second exchange unconditionally sets status to `invalid`.

## Repro

1. Open admin frontend `/accept-invite?code=<valid-pkce-code>` (fresh invite email).
2. Supabase client auto-exchanges the code via `detectSessionInUrl` before the hook's manual exchange.
3. **Expected:** password setup form (`invite-password-form`).
4. **Actual:** invalid-link panel (`invite-link-invalid`).

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-30 | `getSupabaseClient()` uses `detectSessionInUrl: true` (`supabaseClient.ts:84`). |
| 2026-06-30 | `AuthProvider` calls `getSession()` on mount (`AuthContext.tsx:36`). |
| 2026-06-30 | `useAuthLinkCallback` also calls `exchangeCodeForSession(code)` (`useAuthLinkCallback.ts:69-74`). |
| 2026-06-30 | On exchange error, hook sets `invalid` without checking whether a session already exists. |

## Root cause

Race between automatic PKCE handling (`detectSessionInUrl` / concurrent `getSession`) and manual
`exchangeCodeForSession` in `useAuthLinkCallback`. Second exchange fails after code consumption;
error path overwrites a valid `ready` state.

## Fix

Before manual exchange, check `getSession()`. On exchange error, re-check `getSession()` before
marking `invalid`.

## Repro test

- `apps/data-management-frontend/src/test/test_bug_2026_06_30_pkce_double_exchange_race.test.tsx`
- Red: exchange fails but session exists → status was `invalid`
- Green: status `ready`, password form visible with `AuthProvider` mounted

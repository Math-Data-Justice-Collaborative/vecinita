# BUG-2026-07-05 — Intermittent Modal GET /jobs 401 Unauthorized

**Status:** fixing (local patch ready; deploy pending user approval)  
**Severity:** high (paired with eval issue on admin)  
**Feature:** F32 job management / F34 admin JWT  
**Reported:** 2026-07-05  
**Environment:** Production admin frontend → Modal data-management `/jobs`

## Error description

Intermittent `401` when listing jobs from the admin UI:

```json
{"detail":"Unauthorized"}
```

Network capture showed `GET https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs` with `X-Vecinita-Proxy-Key` but **no** `Authorization: Bearer …` header.

## Investigation

1. Modal `/jobs*` requires proxy key **and** Supabase JWT when `VECINITA_AUTH_REQUIRED=true`.
2. `requireAdminConfig()` reads a module-level token set in `AuthProvider` via `useEffect`.
3. React runs **child** `useEffect` hooks before **parent** hooks → first `JobsPage` poll can run before `setOperatorAccessToken()` fires → missing JWT → 401.
4. Subsequent polls (4s interval) often succeed once the parent effect runs → intermittent symptom.

## Root cause

**Code bug:** Auth token sync timing — module-level `operatorAccessToken` updated in parent `useEffect` after child fetch effects.

## Remediation path

Local-first fix → PR → deploy after user approval.

## Verification plan

- **Success:** First jobs list fetch after login includes `Authorization`; no intermittent 401.
- **Checks:** Full main CI parity (local) + PR branch CI.
- **Post-deploy:** User watches production.

## Repro test

- `apps/data-management-frontend/src/test/test_bug_2026_07_05_jobs_auth_token_race.test.tsx`

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-05 | Vitest repro for token available before first jobs fetch | RED |
| 2 | 2026-07-05 | `AuthProvider` syncs token during render (not parent useEffect) | GREEN |

## Fix

- `apps/data-management-frontend/src/auth/AuthContext.tsx` — call `setOperatorAccessToken()` during render so child `useEffect` fetches include `Authorization`

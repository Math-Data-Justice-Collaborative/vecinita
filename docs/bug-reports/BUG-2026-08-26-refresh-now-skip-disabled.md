# BUG-2026-08-26 — Refresh now skip_disabled (internal API key rejected on POST /jobs)

**Status:** fixed (prod deployed; git pending PR)  
**Severity:** high (F79 Refresh now broken on prod)  
**Feature:** F79 freshness / F78 write-API enqueue  
**Reported:** 2026-08-26  
**Environment:** Production — internal-write-api → Modal data-management `POST /jobs`

## Error description

Admin **Refresh now** on a stale document returned success at the write API layer but did not
enqueue a `freshness_refresh` job. Document stayed stale; run history showed no new row.

Operator-visible symptom: refresh action appeared to no-op (`skip_disabled` path in
`freshness_crud` after failed Modal enqueue).

## Error logs

Write-API → Modal enqueue returned **401 Unauthorized** (JWT-only auth on Modal DM
`write_auth_dep`):

```text
POST /jobs → 401 {"detail":"Unauthorized"}
Authorization: Bearer {VECINITA_INTERNAL_API_KEY}
X-Vecinita-Proxy-Key: {VECINITA_MODAL_PROXY_KEY}
```

The 401 was swallowed upstream and surfaced as `skip_disabled` rather than a hard error.

## Investigation

| Step | Finding |
|------|---------|
| 1 | `POST /documents/{id}/refresh` on write API returned 200 |
| 2 | Document `stale=true` unchanged; `freshness_refresh` run history empty |
| 3 | Direct Modal `POST /jobs` with internal key reproduced 401 |
| 4 | `write_auth_dep` used `require_role("admin")` — Supabase JWT only |
| 5 | internal-write-api correctly sends `VECINITA_INTERNAL_API_KEY` as Bearer token |

## Root cause

**Code bug:** Modal DM `write_auth_dep` did not accept the internal service key via
`require_admin_write`, unlike internal-write-api routes. Service-to-service freshness enqueue
always 401'd.

## Fix

- `apps/data-management-backend/vecinita_data_management_backend/app.py` — switch
  `write_auth_dep` to `require_admin_write`; map `ctx.is_service` to admin principal for
  job enqueue paths (F79 Refresh now).

## Repro test

- `tests/bugs/test_bug_2026_08_26_refresh_now_skip_disabled.py`

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-08-26 | Bug test: internal key + proxy on `POST /jobs` freshness_refresh | RED (pre-fix) |
| 2 | 2026-08-26 | `write_auth_dep` → `require_admin_write` | GREEN |
| 3 | 2026-08-26 | Prod verify: refresh 200, stale=false, run history completed | PASS |

## Prod verification (2026-08-26)

| Check | Result |
|-------|--------|
| `POST /documents/{id}/refresh` | 200 — job enqueued |
| Document after refresh | `stale=false`, `last_checked_at=2026-08-26T11:38:50Z` |
| `freshness_refresh` run history | 2 rows, latest `completed` |
| Direct Modal enqueue | OK |

## Prevention

- Regression test at Modal DM app boundary (bugs suite).
- Align DM write auth with internal-write-api (`require_admin_write`) for all service paths.

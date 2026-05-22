# BUG-2026-05-22 — Admin POST /jobs returns 401 Unauthorized

> Status: **verifying** (Modal deployed; admin FE rebuild in progress)  
> Feature: **F8** (data management / ingest jobs)  
> Component: `apps/data-management-backend`, DO `vecinita-admin-frontend`, Modal secret `vecinita-data-management`

## Error description

Submitting a scrape job from the admin frontend returns **401 Unauthorized** on `POST /jobs`
(not browser "Failed to fetch").

Target: `POST https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs`  
Origin: `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/`

## Error logs

```text
# User PowerShell (2026-05-22) — POST with modal-key header and JSON body
# Response: 401 Unauthorized (user report)
# Modal-Key value redacted in report — rotate if exposed in DevTools/network capture

# Agent live probe (invalid key)
curl -X POST 'https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs' \
  -H 'Content-Type: application/json' \
  -H 'Modal-Key: invalid-key-test' \
  -d '{"urls":["https://example.com/"]}'
HTTP 401
{"detail":"Unauthorized"}

# Agent live probe — OPTIONS preflight (same day)
curl -X OPTIONS .../jobs -H 'Origin: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app' \
  -H 'Access-Control-Request-Method: POST' ...
HTTP 200 OK
```

Related: [BUG-2026-05-22-modal-jobs-failed-to-fetch.md](BUG-2026-05-22-modal-jobs-failed-to-fetch.md)
(CORS/preflight — resolved; OPTIONS now 200).

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error — HTTP 401 on POST /jobs |
| Where | Production — admin frontend → Modal data-mgmt |
| When | User report 2026-05-22 (after prior Failed-to-fetch hotfix) |
| Frequency | Every time (per user request) |
| Repro env | Production; local repro via TestClient with wrong key |
| Severity | Critical — cannot submit jobs |
| Evidence | User PowerShell capture (key redacted here) |
| Tried | Nothing |

## Remediation path

**local-first** — align secrets locally; user redeploys admin frontend after approval.

## Interview record (Phase 0)

| Field | Answer |
|-------|--------|
| Symptom | 401 on POST /jobs |
| Where | Production admin → Modal |
| When | After last deploy |
| Frequency | Every time |
| Repro | Production and local |
| Severity | Critical |
| Evidence | PowerShell + more pending in chat |
| Tried | Nothing |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | CORS preflight still blocked (edge 401) | **Ruled out** — live OPTIONS 200 |
| H2 | `Modal-Key` reserved by Modal proxy auth | **Confirmed** — custom key never reaches FastAPI |
| H3 | `VITE_*` ≠ Modal secret key mismatch | **Ruled out** — keys match; POST still 401 with Modal-Key |
| H4 | Empty or stale frontend bundle | **Ruled out** — bundle key matches Modal secret |
| H5 | Header name collision | **Confirmed** — rename to `X-Vecinita-Proxy-Key` |

## Root cause

**Reserved header:** Modal documents `Modal-Key` / `Modal-Secret` for [workspace proxy auth
tokens](https://modal.com/docs/guide/webhook-proxy-auth). The admin UI sent the app proxy
secret in `Modal-Key`, so the ASGI app never received it (always `401`). CORS/preflight
was already fixed (`requires_proxy_auth=False`).

**Fix:** Use `X-Vecinita-Proxy-Key` in FastAPI, CORS allow-headers, admin `jobs.ts`, and OpenAPI.

**Security:** Rotate `VECINITA_MODAL_PROXY_KEY` — value appeared in PowerShell capture.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F8 | In scope |
| `docs/api-contract.md` | 401 for missing/invalid credentials — **expected shape** |
| `connectivity-gates.md` H5 | `VITE_VECINITA_MODAL_PROXY_KEY` must match Modal `VECINITA_MODAL_PROXY_KEY` |
| `docs/staging-secrets-matrix.md` | Documents parity requirement |

**Blocking drift:** none (behavior matches spec when key wrong).

## Repro test

| Test | Path | Status |
|------|------|--------|
| Wrong `X-Vecinita-Proxy-Key` → 401 | `tests/bugs/test_bug_2026_05_22_admin_jobs_401_unauthorized.py` | green |
| Legacy `Modal-Key` not accepted | same | green |
| Lowercase proxy header → 202 | same | green |

User confirmed repro matches symptom (Phase 1.25).

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Repro tests (401 / header) | green |
| 2 | Renamed auth header; Modal deploy | live POST 202 with `X-Vecinita-Proxy-Key` |

## Fix

**Code:**

- `apps/data-management-backend/.../app.py`: `_PROXY_HEADER = "X-Vecinita-Proxy-Key"`.
- `apps/data-management-frontend/src/api/jobs.ts`: same header on fetch.
- Tests, OpenAPI, CORS preflight headers updated.

**Deploy:**

- `modal deploy infra/modal/data_management_app.py` — **done** (2026-05-22).
- `do_apps.py deploy --name vecinita-admin-frontend` — **in progress** (deployment `732e16e3-…`).

**Optional:** Rotate `VECINITA_MODAL_PROXY_KEY` after exposure in intake.

## Verification plan

| Field | Value |
|-------|--------|
| Success | POST /jobs returns 202 in admin UI |
| L1 | `uv run pytest tests/bugs/test_bug_2026_05_22_admin_jobs_401_unauthorized.py` |
| L2 | User PowerShell or browser job submit |
| L3 | Skip unless user approves GPU |
| L4 | After admin FE redeploy — user confirms 202 |

## Timeline

| When | Event |
|------|--------|
| 2026-05-22 | Reported via 14-hotfix; linked to prior CORS bug |
| 2026-05-22 | Root cause: Modal-Key reserved; fix deployed to Modal (live 202) |

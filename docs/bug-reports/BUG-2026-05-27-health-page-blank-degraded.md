# BUG-2026-05-27 — Admin Health page blank after load (degraded API shape)

**Status:** verifying  
**Severity:** high (admin health dashboard unusable)  
**Feature:** EV-002 / F26 — health aggregator UI  
**Reported:** 2026-05-27

## Error description

Admin frontend `/health` shows "Loading…" then a completely blank main content area when
`GET /internal/v1/health/all` returns `status: "degraded"` (e.g. `modal_embedding` down).
Production URL: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/health

## Error logs

```json
{
  "status": "degraded",
  "services": {
    "database": {"status": "up", "latency_ms": 5, "error": null},
    "internal_write_api": {"status": "up", "latency_ms": 0, "error": null},
    "chat_rag_backend": {"status": "up", "latency_ms": 618, "error": null},
    "modal_data_management": {"status": "up", "latency_ms": 3706, "error": null},
    "modal_embedding": {"status": "down", "latency_ms": null, "error": "HTTP 404"},
    "modal_llm": {"status": "up", "latency_ms": 193, "error": null},
    "chat_rag_frontend": {"status": "up", "latency_ms": 140, "error": null},
    "admin_frontend": {"status": "up", "latency_ms": 110, "error": null}
  },
  "checked_at": "2026-05-27T15:36:21.797972Z"
}
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-05-27 | API contract (`docs/api-contract.md` §GET `/internal/v1/health/all`) uses `status` + `services` **object** with per-service `up`/`down`. |
| 2026-05-27 | Frontend `HealthPage` / `admin.ts` expects `overall` + `services` **array** and calls `health.services.map()` — throws on object → React crash → blank page. |
| 2026-05-27 | Unit tests mock the wrong shape (array + `overall`), so CI did not catch drift. |

**Root cause (proposed):** Implementation drift — frontend types/mocks do not match `HealthAggregateResponse` in `packages/shared-schemas` and api-contract.

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/api-contract.md` §health/all | API behavior correct |
| `HealthPage.tsx` / `admin.ts` | **Implementation drift** — wrong response shape |
| F26 scope | In scope for hotfix |

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_05_27_health_page_blank_degraded.test.tsx`
- Red: `TypeError: health.services.map is not a function` at HealthPage.tsx:85
- Green: after `parseHealthAggregate()` in `fetchHealthAggregate`

## Remediation path

**local-first** — PR then deploy admin frontend on user approval.

## Fix

- `apps/data-management-frontend/src/api/admin.ts`: `parseHealthAggregate()` maps api-contract
  `status` + `services` object (`up`/`down`) → UI model with `overall` + service array.

## Verification plan

- Layer 1: admin frontend `npm run lint` + `npm test`
- Layer 2: user reloads `/health` on staging after deploy
- Layer 4: production admin FE after deploy approval

Note: `modal_embedding` HTTP 404 is separate (Modal deploy/URL); Health page should show it as down, not blank.

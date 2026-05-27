# BUG-2026-05-27 — Admin Audit page blank after load (API shape drift)

**Status:** verifying  
**Severity:** high (admin audit log unusable)  
**Feature:** EV-002 / F29 — audit log UI  
**Reported:** 2026-05-27

## Error description

Admin frontend `/audit` shows "Loading…" then a completely blank main content area when
`GET /internal/v1/audit` returns valid data. Production URL:
https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/audit

Same failure class as [BUG-2026-05-27-health-page-blank-degraded.md](BUG-2026-05-27-health-page-blank-degraded.md).

## Error logs

API response (200, truncated):

```json
{
  "items": [
    {
      "id": "8c0d2bef-f472-4674-8090-6c8050622035",
      "event_type": "document.deleted",
      "entity_type": "document",
      "entity_id": "4a435fec-f19f-40ea-a2dd-08417012ecb9",
      "request_id": "44c448e7-7b1c-4cb9-9b6c-4a40b1d87254",
      "payload": {"url": "https://example.com/...", "title": null},
      "created_at": "2026-05-27T21:41:55.326715Z"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total_count": 14
}
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-05-27 | `docs/api-contract.md` §GET `/internal/v1/audit` and `AuditLogResponse` use `items`, `total_count`, `created_at`. |
| 2026-05-27 | Frontend `AuditPage` / `admin.ts` expect `events`, `total`, `timestamp` — calls `data.events.map()` on undefined → React crash → blank page. |
| 2026-05-27 | Unit tests mock wrong shape (`events` / `total`), so CI did not catch drift. |

**Root cause (proposed):** Implementation drift — frontend types/mocks do not match api-contract.

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/api-contract.md` §audit | API behavior correct |
| `AuditPage.tsx` / `admin.ts` | **Implementation drift** — wrong response shape |
| F29 scope | In scope for hotfix |

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_05_27_audit_page_blank.test.tsx`
- Red: `TypeError: Cannot read properties of undefined (reading 'map')` at AuditPage.tsx:136
- Green: after `parseAuditLogResponse()` in `fetchAuditLog` / `fetchDocumentHistory`

## Fix

- `apps/data-management-frontend/src/api/admin.ts`: `parseAuditLogResponse()` maps api-contract
  `items` + `total_count` + `created_at` → UI model with `events` + `total` + `timestamp`.
- Updated audit/doc-history test mocks to api-contract wire shape.

## Remediation path

**local-first** — PR then deploy admin frontend on user approval.

## Verification plan

| Layer | Check |
|-------|-------|
| L1 | admin FE `npm run lint` + `npm test` |
| L2 | User reloads `/audit` on production after deploy |
| L4 | Production admin FE after deploy approval |

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass | 34 admin FE tests; repro test green |
| CI main | pass | https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/26541716359 |
| Deploy preflight | fail (0 jobs) | Pre-existing workflow issue on main — not caused by this hotfix |
| L4 Production | pending | DO auto-deploy from `9b38b57` — reload `/audit` after deploy completes |

**Commit:** `9b38b57` on `main`

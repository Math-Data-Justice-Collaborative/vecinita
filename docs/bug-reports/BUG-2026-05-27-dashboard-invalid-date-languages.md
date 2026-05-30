# BUG-2026-05-27 — Dashboard Recent Activity Invalid Date + empty Languages

**Status:** verifying  
**Severity:** high (admin dashboard misleading / empty widgets)  
**Feature:** EV-002 / F25 — admin summary dashboard  
**Reported:** 2026-05-27

## Error description

Admin dashboard **Recent Activity** shows event types (e.g. `document.deleted`) but every row
displays **Invalid Date** instead of timestamps. The **Languages** stat card shows an empty
value (no count).

Production admin frontend main dashboard (Recent Activity tab).

## Error logs

User-visible UI (production):

```
Recent Activity
document.deleted    Invalid Date
document.tagged     Invalid Date
document.created    Invalid Date
...
Languages card: (empty — no number)
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-05-27 | `docs/api-contract.md` §GET `/internal/v1/stats/summary`: `recent_activity[].created_at`, `language_breakdown` as **object** map, `tag_distribution` with `slug`/`document_count`. |
| 2026-05-27 | `DashboardPage.tsx` uses `event.timestamp` and `new Date(undefined)` → **Invalid Date**. |
| 2026-05-27 | `DashboardPage.tsx` uses `stats.language_breakdown.length` on API **dict** → `undefined` displayed. |
| 2026-05-27 | `fetchStatsSummary` casts JSON directly with no parser (unlike `parseHealthAggregate` / `parseAuditLogResponse`). |
| 2026-05-27 | Vitest mocks wrong wire shape — same class as BUG-2026-05-27-health/audit. |

**Root cause:** Implementation drift — frontend types/mocks do not match api-contract wire format.

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/api-contract.md` §stats/summary | API behavior correct |
| `DashboardPage.tsx` / `admin.ts` | **Implementation drift** |
| F25 scope | In scope for hotfix |

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_05_27_dashboard_invalid_date_languages.test.tsx`
- Red: renders "Invalid Date"; Languages count missing
- Green: after `parseStatsSummary()` in `fetchStatsSummary` (user confirmed repro 2026-05-27)

- **PR:** https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/51 — merged 2026-05-27 (`0b82694` on `main`).
- **CI:** PR branch + main `ci.yml` success; deploy-preflight cancelled (0 jobs, superseded push — non-blocking for FE-only hotfix).
- **Deploy:** `vecinita-admin-frontend` DO deploy triggered 2026-05-27; bundle `index-ButgFDDr.js` includes `parseStatsSummary`.

## Verification

| Layer | Result |
|-------|--------|
| L1 | admin FE `npm run lint` + `npm test` (35 tests) — **pass** |
| L2 | Pending — reload production dashboard after deploy |
| L4 | Pending — deploy admin FE on user approval |

## Remediation path

**local-first** — PR then deploy admin frontend on user approval.

## Verification plan

| Layer | Check |
|-------|-------|
| L1 | admin FE `npm run lint` + `npm test` |
| L2 | User reloads dashboard on production after deploy |

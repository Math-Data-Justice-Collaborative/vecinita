# BUG-2026-07-28 — Spanish “Sign out all devices” overflows sidebar

**Status:** fixing  
**Severity:** low (layout / i18n; logout still works)  
**Feature:** F35 — Admin auth UX  
**GitHub:** [#105](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/105)  
**Session:** S012-hotfix-admin-ui-112-105  
**Reported:** 2026-07-28

## Error description

On the data-management admin UI with locale **Español**, the **Sign out all devices**
button label (`Cerrar sesión en todos los dispositivos`) overflows the fixed-width
(`md:w-60`) desktop sidebar footer.

## Error logs

Issue-provided DOM (abbreviated):

```html
<button
  class="inline-flex ... whitespace-nowrap ... h-9 rounded-md px-3"
  type="button"
  data-testid="admin-sign-out-all-devices"
>
  Cerrar sesión en todos los dispositivos
</button>
```

English (`Log out of all devices`) fits; Spanish does not.

## Symptoms & reproduction

| Field | User report |
|-------|-------------|
| Symptom type | Layout overflow / i18n |
| Where | Staging admin frontend |
| Frequency | Every time in `es` locale |
| Repro env | Staging (interview) |
| Severity | Low |
| Related | UJ-035 / TC-097 |

## Investigation

| Time | Finding |
|------|---------|
| 2026-07-28 | Issue root cause: `Button` base includes `whitespace-nowrap`; sidebar is `md:w-60`; ES string is longer than EN. |
| 2026-07-28 | Surface: `AdminLayout.tsx` `UserMenu`; i18n key `admin.auth.signOutAllDevices`. |

## Root cause

*(pending Phase 1 confirmation after red repro)* — layout: nowrap + long ES label in narrow sidebar.

## Spec conformance

| Check | Result |
|-------|--------|
| UJ-035 / TC-097 | Functional scope OK; layout fit not specified — implementation polish |
| F35 admin chrome | Partial — control works but overflows in `es` |

## Remediation path

**local-first** — fix on branch, PR, merge+deploy after approval (S012-D5).

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_07_28_spanish_signout_overflow.test.tsx`
- Status: **GREEN** (2026-07-28) — `w-full` + `whitespace-normal` on sidebar auth buttons

## Fix

`AdminLayout.tsx` `UserMenu` buttons: `className="h-auto w-full whitespace-normal text-left"`
so long ES labels wrap inside `md:w-60` sidebar (override Button `whitespace-nowrap`).

Also renamed `authContext.ts` → `auth-context.ts` so case-insensitive APFS/Vite no longer
collapses it with `AuthContext.tsx` (local Vitest/build unblocker).

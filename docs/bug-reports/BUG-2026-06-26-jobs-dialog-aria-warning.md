# BUG-2026-06-26 — Admin Jobs page Radix DialogContent aria warning

**Status:** resolved (local green; pending admin FE deploy)
**Severity:** low (console warning; accessibility gap on mobile nav sheet)
**Feature:** F32 — Job Management tab (`apps/data-management-frontend`)
**Reported:** 2026-06-26
**Branch:** `fix/jobs-dialog-aria-get-jobs-deploy`

## Error description

On the admin **Jobs** page (and other routes using `AdminLayout`), the browser console shows:

```
Warning: Missing `Description` or `aria-describedby={undefined}` for {DialogContent}.
```

The warning appears twice (React `StrictMode` double effect when the mobile nav sheet opens).

## Repro

1. Open production admin frontend (`https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/jobs`) on a mobile viewport or open the hamburger menu.
2. Open DevTools console.
3. **Expected:** no Radix dialog accessibility warnings.
4. **Actual:** `DialogContent` description warning (×2 in dev/StrictMode).

## Error logs

```
installHook.js:1 Warning: Missing `Description` or `aria-describedby={undefined}` for {DialogContent}.
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-26 | `Sheet` uses `@radix-ui/react-dialog`; `SheetContent` is `DialogContent` internally. |
| 2026-06-26 | `AdminLayout` mobile nav has `SheetTitle` but no `SheetDescription` (`AdminLayout.tsx`). |
| 2026-06-26 | Radix warns when `aria-describedby` is set but the description element is missing. |
| 2026-06-26 | Bulk dialogs on Corpus already include `DialogDescription`; not the source on `/jobs`. |

**Root cause:** Code bug — mobile navigation sheet missing `SheetDescription` (or explicit `aria-describedby={undefined}`).

## Spec conformance

| Check | Result |
|-------|--------|
| F32 scope | In scope — admin frontend polish on Job Management surfaces |
| Accessibility | No spec section; follow Radix/shadcn a11y patterns |

No blocking spec drift.

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_06_26_jobs_dialog_aria.test.tsx`
- Red: open mobile nav on `/jobs` → `console.warn` contains DialogContent description message.
- Green: after `SheetDescription` added to mobile nav.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-26 | Add Vitest repro — App `/jobs`, open mobile sheet, spy `console.warn` | RED — 1 DialogContent warning |
| 2 | 2026-06-26 | Add `SheetDescription` (sr-only) + i18n `admin.nav.mobileMenuDescription` | GREEN |

## Remediation path

Local-first (user choice 2026-06-26). Frontend patch; admin FE deploy after user approval.

## Verification plan

- Success: no DialogContent aria warning when opening mobile nav on Jobs page.
- Checks: Vitest repro + full local CI parity before PR.
- Monitoring: user verifies production console after admin FE deploy.

## Fix

`AdminLayout.tsx`: add sr-only `SheetDescription` to mobile nav sheet.
`packages/frontend-i18n`: `admin.nav.mobileMenuDescription` (EN/ES).

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] `npm test` in data-management-frontend (193 pass)
- [ ] Local CI parity (full)

### Layer 2 — Reproduction

- [ ] User confirms console clean on Jobs page

### Layer 4 — Production

- [ ] After admin FE deploy

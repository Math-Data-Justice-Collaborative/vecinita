# BUG-2026-06-14 — Admin UI missing EN/ES toggle; theme toggle inconsistent

**Status:** fixing  
**Severity:** critical (operator UX — user report)  
**Feature:** F31 — Admin + shared frontend bilingual UI (en/es)  
**Reported:** 2026-06-14

## Error description

Production admin frontend (`data-management-frontend` on DigitalOcean):

1. **No English/Spanish language toggle** — operator cannot switch UI locale; user reports UI **defaults to Spanish**.
2. **Dark/Light theme toggle only visible on some screens** (e.g. dashboard) — inconsistent access to theme control across admin pages.

User tried hard reload; issue persists every time in production only (not reproduced locally per interview).

## Error logs

None provided (user: no screenshots/logs yet).

## Symptoms & reproduction

| Field | User report |
|-------|-------------|
| Symptom type | Wrong output — missing toggles / inconsistent UI chrome |
| Where | Production (DO admin frontend) |
| When started | After last deploy |
| Frequency | Every time |
| Repro env | Production only |
| Severity | Critical |
| Tried | Hard reload |

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-14 | `AdminLayout.tsx` has `ThemeToggle` in desktop sidebar footer + mobile nav sheet only — **no `LanguageToggle`**, no `LocaleProvider` in `main.tsx`. |
| 2026-06-14 | F31 / EV-004 M36 tasks (`T36.1`–`T36.10`) still **pending** in `docs/execution-plan.md`. |
| 2026-06-14 | `packages/frontend-ui` is a stub (`export {}`); `packages/frontend-i18n` `t()` throws — shared packages not ready for admin wiring. |
| 2026-06-14 | `docs/user-journeys.md` UJ-022 expects EN/ES toggle beside theme in sidebar footer — **spec vs implementation drift**. |
| 2026-06-14 | Current admin strings are hardcoded English in source — user report of "defaulting to Spanish" may be browser translate, ChatRAG confusion, or undeployed partial build; needs confirmation on production bundle. |
| 2026-06-14 | Theme toggle: code places control in sidebar (desktop) or hamburger sheet (mobile) for **all** routes via `AdminLayout`; "dashboard only" may reflect mobile UX (toggle hidden until menu opened) or viewport/sidebar visibility — TBD with repro test. |

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/user-journeys.md` UJ-022 | **Implementation drift** — LanguageToggle + LocaleProvider missing |
| `docs/feature-list.md` F31 | Planned, not implemented |
| `docs/test-plan.md` TC-065–TC-071 | Tests not present (`test_admin_language_toggle_i18n.test.tsx` missing) |
| Theme in AdminLayout | Partial — present in layout but mobile discoverability gap possible |

## Remediation path

**local-first** — fix locally, deploy to production only after user approval.

## Repro test

- Path: TBD (`tests/bugs/test_bug_2026_06_14_admin_missing_i18n_theme_toggle.test.tsx`)
- Status: not written yet

## Verification plan

TBD — Step 0.5 interview.

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Phase 0 intake | User confirmed production-only, every time, critical |

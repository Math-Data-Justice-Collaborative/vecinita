# 01-requirements — EV-013 / #148 Admin table density

**Session:** S014-admin-ui-polish-148  
**Cycle:** EV-013  
**Date:** 2026-07-29  
**Mode:** delta (extend F9 + F12)

## Scope (approved)

Polish Admin `/corpus` for single-screen density and truncation; share helpers across Jobs,
Users, Audit, Evaluation list tables. Pagination (#112) already shipped — keep `page_size` 50.

## Decisions (RD-179–RD-182)

| ID | Decision |
|----|----------|
| RD-179 | Extend F9+F12; shared tables in one PR; page_size 50 |
| RD-180 | light/dark/system + OS `prefers-contrast` only (no HC theme mode) |
| RD-181 | **Privacy:** no cookies, no new localStorage, no consent banner; native `title`/`aria-label` |
| RD-182 | Vitest TC-152–154; Playwright TC-155 viewport; no API change |

## Privacy / cookies alignment

Vecinita has **no cookie-consent product surface**. UI prefs already use **device-local
`localStorage`** (`vecinita-ui-theme`, `vecinita.locale`) — never cookies, never server sync
(ADR-004 / privacy posture).

EV-013 truncation chrome:

- Sets **no** `document.cookie`
- Adds **no** new storage keys
- Does **not** introduce a consent banner
- Relies on CSS + DOM attributes only for full-text reveal
- Theme contrast remains existing ThemeToggle + OS media queries

## Spec deltas written

| Doc | Delta |
|-----|-------|
| `docs/feature-list.md` | F9 / F12 EV-013 polish notes |
| `docs/user-journeys.md` | UJ-051 |
| `docs/test-plan.md` | TC-152–TC-155 + UJ map |
| `docs/acceptance-criteria.md` | AC-U1–AC-U7 |
| `docs/decisions.md` | RD-179–RD-182 |

## Out of scope

- New Fn id; AdminLayout redesign; cookie/consent product; high-contrast ThemeToggle mode;
  server pagination API; Radix Tooltip wrapper (deferred).

## Next

02-verify-plan (Lean gate A→B) → 07-build.

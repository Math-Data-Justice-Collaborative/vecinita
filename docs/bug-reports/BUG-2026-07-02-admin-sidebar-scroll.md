# BUG-2026-07-02 — Admin sidebar does not stay on left when scrolling

**Status:** resolved  
**Severity:** medium  
**Feature:** F31 — Admin frontend layout  
**Reported:** 2026-07-02

## Error description

Production admin frontend (`data-management-frontend`): the desktop sidebar navigation
(`data-testid="admin-nav"`) does not extend / stay pinned on the left when scrolling long
pages (e.g. Users). Intended behavior: sidebar remains visible on the left for the full scroll
range of the main content area.

## Error logs

User-provided DOM snippet — `admin-nav` inside `div.flex-1.overflow-auto.px-3.py-4` within
desktop sidebar; observed on `/users` with Users link active.

## Symptoms & reproduction

| Field | User report |
|-------|-------------|
| Symptom type | Wrong output — layout / sidebar scroll |
| Where | Production (DO admin frontend) |
| When started | After last deploy |
| Frequency | Every time on long-scroll pages |
| Repro env | Production only (per interview) |
| Severity | Medium |
| Tried | Nothing |

## Investigation

| Time | Finding |
|------|---------|
| 2026-07-02 | `AdminLayout.tsx` root uses `flex min-h-screen` — container can grow beyond viewport. |
| 2026-07-02 | `DesktopSidebar` uses `md:h-screen` — sidebar height locked to viewport while document may scroll. |
| 2026-07-02 | `main` has `overflow-auto` but parent chain lacks `h-screen overflow-hidden` + `min-h-0` — scroll may escape to document. |
| 2026-07-02 | Fix: viewport-lock shell (`h-screen overflow-hidden`), `min-h-0` on main column, `md:shrink-0` on sidebar. |

## Root cause

Code bug — outer layout allowed document height to exceed viewport (`min-h-screen`), while sidebar was viewport-height only (`md:h-screen`). Scrolling long pages scrolled the document, leaving the sidebar behind above the fold.

## Fix

`apps/data-management-frontend/src/components/AdminLayout.tsx`:
- Root: `min-h-screen` → `h-screen overflow-hidden` + `data-testid="admin-layout"`
- Content column: add `min-h-0 overflow-hidden`
- Main: add `min-h-0` + `data-testid="admin-main"`
- Sidebar: add `md:shrink-0` + `data-testid="admin-sidebar"`

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/user-journeys.md` UJ-020 (admin navigation) | **Implementation drift** — journey expects persistent sidebar on desktop |
| F31 admin chrome | Partial — nav renders but scroll containment broken on long pages |

## Remediation path

**local-first** — fix locally, deploy to production only after user approval.

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_07_02_admin_sidebar_scroll.test.tsx`
- Status: GREEN (2026-07-02)

## Verification

### Layer 1 — Automated
- [x] Repro test red→green (layout class assertions)
- [x] data-management-frontend lint pass
- [x] data-management-frontend 469 tests pass
- [x] PR branch CI success
- [x] main CI success (7fde976)

### Layer 4 — Production
- [x] Deploy DigitalOcean success — https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28595313375
- [x] User production verify — sidebar stays on left when scrolling (2026-07-02)

## Verification plan

| Field | Choice |
|-------|--------|
| Success criterion | Sidebar stays visible on left while scrolling any long admin page |
| Checks | Full main CI parity (local) + gh on main after merge |
| Monitoring | User watches production after deploy |

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Phase 0 intake | User confirmed production, every time, medium, local-first |

## Prevention & countermeasures

- Automated: repro test only (user choice)
- Cursor rule: `.cursor/rules/admin-layout-scroll-containment.mdc`

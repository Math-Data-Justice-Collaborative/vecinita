# S014 — Admin Corpus & dashboard UI/UX polish (#148)

**Type:** feature  
**Status:** in_progress  
**Orchestrator:** 16-evolve  
**Evolve cycle:** EV-013  
**Branch:** `evolve/EV-013-admin-ui-polish-148`  
**Source:** [GitHub #148](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/148)

## Intent

Polish the **Admin / Data Management** dashboard so operators can work corpus (and related
tables) without layout blowouts:

1. **Corpus must-have** — single-screen density (sticky header, compact rows; pagination already
   from #112), truncate long titles/URLs with full text on hover/`aria-label`, constrain columns
   so Actions stay visible, bound tag chips (`+N`), keep empty/loading/error clear.
2. **Shared polish (same PR)** — apply the same truncation/density helpers to Jobs, Users, Audit,
   and Evaluation tables where the same problems show up.
3. **Vitest** — long-fixture coverage for truncation + accessible full text; no regression in
   select-all / bulk actions / manage-tags / delete.

## Out of scope

- New features (#70 tree ingest, #114 monitoring dashboard, etc.).
- Full AdminLayout redesign (small scroll fixes OK).
- Server-side pagination API work (#112 — **already shipped** in S012).

## Prior related

| Item | Status |
|------|--------|
| [#112](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/112) pagination | Closed — S012 hotfix |
| [#105](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/105) ES sidebar | Related layout polish |
| [#106](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/106) tooltips | May reuse for truncated titles |
| EV-004 F31 bilingual admin | Closed 2026-07-29 (stale cycle; F31 already shipped) |

## Hard constraints

- Admin SPA only (`apps/data-management-frontend`); no ChatRAG changes unless sharing a package helper.
- Prefer extend **F9** / **F12** (or allocate one polish Fn in Phase 1) — confirm in intake.
- EN/ES i18n only if new visible chrome strings are added (native `title`/`aria-label` OK with raw text).
- TDD + Vitest per acceptance criteria.

## UI preview

Non-deployed local Admin UI — **yes**, open early to ground scope (user S014 intake).

## Decisions (session open)

| ID | Decision |
|----|----------|
| S014-D1 | Session type `feature` → 16-evolve |
| S014-D2 | Scope = Corpus must-have + shared table polish (Jobs/Users/Audit/Eval) in one PR |
| S014-D3 | Routing = Lean+build (`01→02→07→08→10→13`; skip 03–06, 09, 11–12) |
| S014-D4 | Close EV-004 (user) before EV-013 |
| S014-D5 | Early local (non-deployed) UI preview |
| S014-D6 | Truncation/density theme-aware via existing ThemeProvider + OS `prefers-contrast` (no HC mode) |
| S014-D7 | Full text via native `title` + `aria-label` (no Tooltip required) |
| S014-D8 | Privacy: no cookies / no new localStorage / no consent UI (RD-181) |
| S014-D9 | Fn = extend F9+F12; page_size 50; RD-179–RD-182 |

## Spec handoff

- [reports/01-requirements.md](./reports/01-requirements.md)
- Standing deltas: feature-list F9/F12, UJ-051, TC-152–155, AC-U1–U7, decisions RD-179–182

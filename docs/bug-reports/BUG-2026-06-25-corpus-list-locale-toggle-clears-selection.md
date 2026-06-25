# BUG-2026-06-25 — CorpusList: locale toggle refetches corpus and clears bulk selection

**Status:** fixed (local green; CI pending)
**Severity:** high (data loss: dismisses in-progress bulk action)
**Feature:** F31 / data-management admin frontend (EV-004)
**Reported:** 2026-06-25
**Source:** PR #66 review PRR-009 — inline comment on `CorpusList.tsx:64` (Bugbot, confirmed)

## Error description

Switching the admin UI language (EN ⇄ ES) while documents are selected silently clears the
selection and triggers an extra corpus reload. Any in-progress bulk delete / tag / metadata
action is dismissed because the bulk toolbar disappears with the selection.

## Error logs

No exception — a behavioral regression. Reactivity chain:

```
useAdminT(): tr = useCallback(..., [locale])   // identity changes on every EN/ES switch
CorpusList:  refresh = useCallback(..., [tr])   // → new identity when tr changes
CorpusList:  useEffect(() => void refresh(...), [refresh])  // → re-fires on locale change
refresh():   setSelectedIds(new Set())          // → wipes current selection + refetches
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-25 | `tr` from `useAdminT()` is `useCallback`-keyed on `[locale]`, so its identity changes on each language switch. |
| 2026-06-25 | `refresh` depends on `[tr]` only because of the localized load-error fallback `tr("admin.corpusList.loadFailed")`. |
| 2026-06-25 | The mount load effect `useEffect(..., [refresh])` therefore re-fires on locale change, re-running the loader and `setSelectedIds(new Set())`. |

**Root cause:** Code bug — the one-time mount load is coupled to `tr` purely for an error-fallback
string, so locale changes (not data changes) re-trigger the loader and reset selection state.

## Spec conformance

| Check | Result |
|-------|--------|
| F31 i18n must not regress admin UX | Selection must survive a locale switch |
| F31 scope | In scope — regression fix on the i18n integration |

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_06_25_corpus_list_locale_toggle_selection.test.tsx`
- Red: select rows → toggle locale → selection cleared (bulk toolbar gone) + second fetch
- Green: after decoupling the load path from `tr` — selection preserved, no refetch on locale switch

## Remediation path

PR #66 review remediation (PRM-006). Fix on the PR head branch `fix/admin-ui-es-en-toggle`.

## Fix

- `CorpusList.tsx`: hold the latest `tr` in a ref (`trRef`) updated via effect; `refresh` reads
  `trRef.current` for the localized load-error fallback and drops `tr` from its dependency list.
  The mount effect now has a stable `refresh`, so it fires only on real data refreshes — not on
  locale changes. Render-time labels still re-localize live because they call `tr` directly.
- Regression: `test_bug_2026_06_25_corpus_list_locale_toggle_selection.test.tsx`

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass (local) | `npm run lint` clean; `npm test` 183 passed (29 files); `npm run build` ok (data-management-frontend) |
| CI | pending | watch `ci.yml` on `fix/admin-ui-es-en-toggle` after push |

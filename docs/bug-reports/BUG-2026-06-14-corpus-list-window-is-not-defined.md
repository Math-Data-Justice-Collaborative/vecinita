# BUG-2026-06-14 — CI: CorpusList `window is not defined` in admin nav tests

**Status:** verifying  
**Severity:** high (main CI red)  
**Feature:** F31 / data-management admin frontend  
**Reported:** 2026-06-14

## Error description

GitHub Actions `frontend (data-management-frontend)` job fails during `npm test` with
`ReferenceError: window is not defined` originating from `CorpusList.tsx:46` while running
`test_admin_nav.test.tsx` (corpus navigation mounts `CorpusList`, which loads documents on mount).

CI run: https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/27514134365/job/81319613348

## Error logs

```
ReferenceError: window is not defined
❯ getCurrentEventPriority ../../node_modules/react-dom/cjs/react-dom.development.js:10993:22
❯ requestUpdateLane ../../node_modules/react-dom/cjs/react-dom.development.js:25495:19
❯ dispatchSetState ../../node_modules/react-dom/cjs/react-dom.development.js:16648:14
❯ src/components/CorpusList.tsx:46:7
This error originated in "src/test/test_admin_nav.test.tsx" test file.
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-14 | `CorpusList` `useEffect` calls async `refresh()`; admin nav tests navigate to `/corpus` without mocking `fetch` or awaiting load completion. |
| 2026-06-14 | When the test ends and jsdom tears down, pending `refresh()` resolves and `setLoading(false)` (line 46) triggers React state update without `window` — flaky in CI. |
| 2026-06-14 | `DocumentAdmin` already guards async polling with `cancelled`; `CorpusList` initial load lacks an unmount guard. |

**Root cause:** Code bug — state updates after unmount when async corpus list fetch completes post-test cleanup.

## Spec conformance

| Check | Result |
|-------|--------|
| Admin frontend tests | Should pass in CI (`ci.yml` frontend matrix) |
| F31 scope | In scope — test/regression fix |

## Repro test

- Path: `apps/data-management-frontend/src/test/test_bug_2026_06_14_corpus_list_unmount_during_load.test.tsx`
- Red: unmount before delayed fetch resolves → `window is not defined`
- Green: after unmount guard in `CorpusList.refresh` / mount effect

## Remediation path

**local-first** — fix on `main`, PR optional (user-directed CI hotfix).

## Fix

- `CorpusList.tsx`: guard async `refresh()` state updates with an `isActive()` callback; mount
  effect sets `cancelled = true` on unmount so pending fetches cannot call `setState` after jsdom
  teardown (matches `DocumentAdmin` polling guard pattern).
- `test_admin_nav.test.tsx`: stub `fetch` in `beforeEach`; `waitFor` corpus list load on corpus
  navigation tests so async work completes before test teardown.
- Regression: `test_bug_2026_06_14_corpus_list_unmount_during_load.test.tsx`

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass (local) | `npm run lint`, `npm test` (172 tests), `npm run build` |
| CI | pending | push + watch `frontend (data-management-frontend)` |

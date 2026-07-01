---
name: ui-tests
description: >
  Authors Playwright UI interaction tests for Vecinita frontends (chat-rag and data-management).
  Covers cross-component browser flows in tests/ui/, route mocks, auth seeding, UJ/TC mapping, and
  TDD workflow. Use when adding UI tests, Playwright specs, frontend interaction coverage, or when
  the user asks to test behavior between components (sidebar, tabs, shell state, forms).
---

# UI Tests (Playwright)

Independent skill for **Playwright T0-ui** specs under `tests/ui/`. Complements Vitest
(component logic) and pytest API E2E (`tests/e2e/`).

**Repo docs:** [tests/ui/README.md](../../tests/ui/README.md), [docs/test-plan.md](../../docs/test-plan.md)

## When to use Playwright vs Vitest

| Write **Playwright** when… | Keep **Vitest** when… |
|----------------------------|------------------------|
| Two+ components must cooperate (shell ↔ panel, nav ↔ outlet) | Single component/hook in isolation |
| Real routing, `localStorage`, or URL query params matter | Mocked `MemoryRouter` is enough |
| Behavior depends on browser layout/focus | Recharts or heavy libs are mocked |
| Regression was “works in jsdom, breaks in browser” | Pure transform/validation logic |

Do **not** duplicate Vitest coverage in Playwright. Mirror the **interaction** the Vitest test
cannot prove (see `apps/*/src/test/test_bug_*` for good candidates).

## Layout

```
tests/ui/
├── chat/           # chat-rag-frontend (baseURL :5173)
├── admin/          # data-management-frontend (baseURL :5174)
├── staging/        # T3-ui — env-gated live URLs
└── helpers/        # mock-chat-api, mock-admin-api, mock-admin-auth, mock-supabase-auth
```

| App | Spec path | Playwright project |
|-----|-----------|-------------------|
| ChatRAG | `tests/ui/chat/uj*.spec.ts` | `chat-rag` |
| Admin | `tests/ui/admin/uj*.spec.ts` | `data-management` |
| Staging | `tests/ui/staging/*.spec.ts` | `staging` |

Config: [playwright.config.ts](../../playwright.config.ts) — `vite preview` web servers, no dev server.

## Workflow

### 1 — Scope the interaction

1. Read the **user journey** in `docs/user-journeys.md` (UJ-NNN) or infer from the feature.
2. List **components involved** and the **observable outcome** (e.g. “Sidebar nav → EvaluationPage tabs visible”).
3. Check existing **Vitest** tests in `apps/<app>/src/test/` — reuse mock payloads and `data-testid`s.
4. Confirm the journey is **not** API-only; if backend-only, use `tests/e2e/` instead.

### 2 — Pick helpers (T0-ui mocks)

| Scenario | Import |
|----------|--------|
| Chat shell / ask / corpus | `mockChatShell`, `mockChatApi`, `mockChatStream` from `tests/ui/helpers/mock-chat-api.ts` |
| Admin authenticated | `mockAuthenticatedAdmin` from `tests/ui/helpers/mock-admin-api.ts` |
| Admin viewer role | `mockAuthenticatedViewer` from same |
| Login / unauthenticated | `mockSupabaseAuth` from `tests/ui/helpers/mock-supabase-auth.ts` |

Extend helpers when a new API surface is needed — **do not** inline duplicate route handlers across specs.

Build env for preview bundles is set in [scripts/ui/build_for_playwright.sh](../../scripts/ui/build_for_playwright.sh).

### 3 — Write the spec (TDD)

1. Create `tests/ui/<chat|admin>/uj<NNN>-<slug>.spec.ts`.
2. File header comment: **UJ-NNN**, **components under test**, optional **TC-NNN** / bug ID.
3. `test.describe` = interaction boundary; one `test()` per user-visible outcome.
4. **Red first:** run `npx playwright test <file>` and confirm failure for the right reason.
5. Prefer accessible selectors: `getByRole`, `getByLabel`, `getByTestId` (match existing component testids).
6. Assert **interaction outcomes** inside the correct container (`message-list`, `evaluation-page`), not global text that also appears in sidebars.
7. For admin auth, call `mockAuthenticatedAdmin(page)` in `beforeEach` before `page.goto`.

Minimal template:

```typescript
import { expect, test } from "@playwright/test";
import { mockChatShell } from "../helpers/mock-chat-api";

/** UJ-NNN: [Component A] ↔ [Component B] — [behavior]. */
test.describe("[Feature] interaction", () => {
  test.beforeEach(async ({ page }) => {
    await mockChatShell(page);
  });

  test("[user-visible outcome]", async ({ page }) => {
    await page.goto("/");
    // act → assert cross-component state
  });
});
```

### 4 — Map to docs

Update (same PR):

- `docs/user-journeys.md` — browser steps if new/changed
- `docs/test-plan.md` — UI E2E column: `tests/ui/...spec.ts` + TC-ID

### 5 — Verify

```bash
# Node 24 required
bash scripts/ui/build_for_playwright.sh   # if sources changed
npx playwright test tests/ui/<path>.spec.ts
make test-ui                              # full CI-parity suite
```

Staging-only specs: `npm run test:ui:staging` with `VECINITA_STAGING_*_FRONTEND_URL` set.

## Selector conventions

- Reuse `data-testid` from production components (grep `apps/<app>/src`).
- Chat i18n: default locale **en** unless testing locale toggle (click `language-toggle` → **ES**).
- Admin i18n: shared `LanguageToggle` in layout; Spanish nav uses **Panel** not Dashboard.
- Empty containers may be `hidden` — assert on visible siblings (`getByLabel`, `toBeAttached`).

## Anti-patterns

- ❌ Testing implementation details (CSS classes, internal state not user-visible)
- ❌ Full stack in default CI (use route mocks for T0-ui; hybrid per test-plan)
- ❌ Copy-pasting Vitest mock setup — extract to `tests/ui/helpers/`
- ❌ `getByText` for strings that appear in both sidebar list and main panel
- ❌ New Playwright dependency without `docs/dependency-inventory.md` entry

## Checklist before done

- [ ] Spec maps to UJ-NNN (and TC-NNN if assigned)
- [ ] Tests **interaction between components**, not isolated logic
- [ ] Helpers reused or extended (not duplicated)
- [ ] `npx playwright test` passes locally
- [ ] `docs/test-plan.md` UI E2E column updated
- [ ] No `any` in new TypeScript (strict typing policy)

## Additional resources

- Patterns, helper API, example specs: [reference.md](reference.md)
- Pipeline context: [01-requirements](../01-requirements/SKILL.md) §Test requirements, [09-qa](../09-qa/SKILL.md) Agent 4

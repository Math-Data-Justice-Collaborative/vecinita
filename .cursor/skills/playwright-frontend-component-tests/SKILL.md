---
name: playwright-frontend-component-tests
description: Create and run Playwright component tests for frontend components in React and Vue projects. Use when users ask to add, generate, update, or run Playwright frontend component tests, including requests mentioning playwright, component tests, test-ct, mount, or frontend UI components.
---

# Playwright Frontend Component Tests

## Goal

Create reliable Playwright component tests for frontend components, then run them with fast, scoped commands before broader runs.

## Default Workflow

```md
Playwright Component Test Progress
- [ ] Detect framework and current Playwright setup
- [ ] Initialize component testing if missing
- [ ] Create or update component spec files
- [ ] Run focused component tests
- [ ] Run broader component suite
```

## 1) Detect framework and setup

- Check whether the project is React, Vue, or mixed.
- Look for existing Playwright files before scaffolding:
  - `playwright.config.*`
  - `playwright/index.html`
  - `playwright/index.ts`
  - existing `*.spec.ts` / `*.spec.tsx` in frontend folders
- Reuse existing conventions instead of introducing new patterns.

## 2) Initialize component testing (only if missing)

Use the package manager already used by the project:

```bash
npm init playwright@latest -- --ct
```

Equivalent options:

```bash
yarn create playwright --ct
pnpm create playwright --ct
```

## 3) Create or update component specs

- Keep tests next to components when the repo already follows that pattern.
- Prefer one behavior-focused test per scenario.
- Use `mount` from Playwright component testing package.

React example:

```tsx
import { test, expect } from '@playwright/experimental-ct-react';
import Button from './Button';

test('renders label', async ({ mount }) => {
  const component = await mount(<Button label="Save" />);
  await expect(component).toContainText('Save');
});
```

Vue example:

```ts
import { test, expect } from '@playwright/experimental-ct-vue';
import Button from './Button.vue';

test('renders label', async ({ mount }) => {
  const component = await mount(Button, { props: { label: 'Save' } });
  await expect(component).toContainText('Save');
});
```

## 4) Run focused tests first

Use targeted commands while iterating:

```bash
npx playwright test src/components/Button.spec.tsx
```

Run a single browser if needed:

```bash
npx playwright test --project=chromium src/components/Button.spec.tsx
```

## 5) Run broader component suite

After focused tests pass:

```bash
npm run test-ct
```

or:

```bash
npx playwright test
```

## Quality Rules

- Prefer minimal, behavior-driven assertions over snapshot-heavy tests.
- Keep tests deterministic: no real network calls unless explicitly required.
- Do not add extra frameworks or helpers unless the repo already uses them.
- Match existing naming, file placement, and command conventions.

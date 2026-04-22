# Implementation Notes: Chat Message Presentation

## Existing TypeScript Library Reuse (T001)

- Reused existing `react-markdown` + `remark-gfm` stack for assistant rich markdown rendering.
- Added policy logic in local utility modules instead of introducing a new markdown rendering dependency.
- Implemented safety and rendering policy with in-repo TypeScript helpers:
  - `frontend/src/app/lib/assistantMarkdownPolicy.ts`
  - `frontend/src/app/lib/assistantMessageNormalization.ts`

## Playwright Configuration Verification (T004)

- Existing `frontend/playwright.config.ts` already includes Chromium projects suitable for CI-focused runs.
- New rendering-focused E2E tests were added under `frontend/tests/e2e/` and rely on deterministic route fixtures.

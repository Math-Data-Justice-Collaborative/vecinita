# Quickstart: Chat Message Presentation

## Prerequisites

- Frontend dependencies installed.
- Existing local chat frontend runnable.
- Playwright installed in project test stack.

## 1) Run unit-level rendering checks

Use existing frontend test commands to verify:

- payload-to-display normalization
- markdown transformation rules
- HTML stripping/escaping
- remote image link conversion
- table overflow policy behavior

## 2) Run Playwright E2E for chat rendering

Recommended baseline:

- run Chromium-focused suite first for speed and CI parity
- execute rendering scenarios with deterministic seeded responses

Core E2E scenarios:

1. Assistant payload metadata is not rendered in message body.
2. Markdown lists/code/links/tables render readably.
3. Oversized tables stay in-bounds with horizontal scroll.
4. Remote images render as links only.
5. Raw HTML appears escaped/stripped (not executed).
6. Empty assistant content shows fallback message.

Suggested command subset for this feature:

```bash
npm run test:e2e -- --project=chromium-chat-gateway-smoke tests/e2e/chat-gateway-smoke.spec.ts tests/e2e/chat-markdown-rendering.spec.ts tests/e2e/chat-visual-hierarchy.spec.ts tests/e2e/chat-edge-cases.spec.ts
```

## 3) Validate non-regression in chat flow

- Confirm user can continue sending messages after long/complex assistant output.
- Confirm sender visual hierarchy remains consistent across mixed conversation turns.

## 4) CI guidance

- Prefer Chromium-only install for faster CI where appropriate (`npx playwright install chromium --with-deps`).
- Keep E2E deterministic; avoid dependence on unstable third-party network content.

## 5) Latest implementation validation run

- Targeted Vitest run completed for rendering-related files:
  - `src/app/lib/__tests__/assistantMarkdownPolicy.test.ts`
  - `src/app/components/__tests__/ChatMessage.sources.test.tsx`
  - `src/app/components/__tests__/ChatWidget.stream-success.integration.test.tsx`
  - `src/app/components/__tests__/ChatInterface.integration.test.tsx`
  - `src/app/services/__tests__/agentService.test.ts`
- Result: `67 passed` tests across `5` files in the targeted suite.
- Additional unit/integration coverage run:
  - `src/app/components/__tests__/ChatWidget.test.tsx`
  - `src/app/components/__tests__/ChatMessage.sources.test.tsx`
  - `src/app/components/__tests__/ChatWidget.stream-success.integration.test.tsx`
  - `src/app/pages/__tests__/ChatPage.test.tsx`
- Result: `54 passed` tests across `4` files.
- Playwright Chromium chat rendering subset run:
  - `tests/e2e/chat-gateway-smoke.spec.ts`
  - `tests/e2e/chat-markdown-rendering.spec.ts`
  - `tests/e2e/chat-visual-hierarchy.spec.ts`
  - `tests/e2e/chat-edge-cases.spec.ts`
- Result: `4 passed` E2E tests.

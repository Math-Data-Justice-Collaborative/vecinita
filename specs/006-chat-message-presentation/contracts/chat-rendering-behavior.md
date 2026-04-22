# Contract: Chat Rendering Behavior

## Purpose

Define the user-visible rendering contract for assistant messages so implementation and testing remain aligned.

## Input Contract

- Input source is an assistant response payload that may contain:
  - semantic reply text
  - metadata fields
  - markdown elements (lists, code blocks, tables, links, images)
  - irregular content (raw HTML tags, empty content, escaped newlines)

## Output Contract

- Chat UI must render a `DisplayMessage` with these guarantees:
  1. Message body displays semantic assistant content only.
  2. Metadata fields are not shown in the main message content.
  3. Markdown elements are rendered in readable rich text form.
  4. Raw HTML is escaped or stripped.
  5. Remote images are shown as clickable links, not inline media.
  6. Wide tables preserve column structure and scroll horizontally within message bounds.
  7. Missing/empty assistant content produces user-friendly fallback text.

## Failure/Edge Contract

- If rendering transformation fails, UI must still show safe fallback text and keep chat input usable.
- Layout must never overflow or block interaction with follow-up prompts.

## Verification Contract (Testing)

- Unit tests validate normalization and policy transformations.
- Playwright E2E validates browser-visible behavior for:
  - markdown formatting
  - table horizontal scrolling
  - remote image link conversion
  - raw HTML stripping/escaping
  - fallback behavior for empty content

## Implementation Alignment Notes

- Rendering policy helpers are implemented in:
  - `frontend/src/app/lib/assistantMarkdownPolicy.ts`
  - `frontend/src/app/lib/assistantMessageNormalization.ts`
- Message rendering + containment behavior is implemented in:
  - `frontend/src/app/components/ChatMessage.tsx`
  - `frontend/src/app/components/ChatWidget.tsx`
  - `frontend/src/app/pages/ChatPage.tsx`
- E2E fixture and rendering specs are implemented in:
  - `frontend/tests/e2e/chat-rendering.fixtures.ts`
  - `frontend/tests/e2e/chat-markdown-rendering.spec.ts`
  - `frontend/tests/e2e/chat-visual-hierarchy.spec.ts`
  - `frontend/tests/e2e/chat-edge-cases.spec.ts`

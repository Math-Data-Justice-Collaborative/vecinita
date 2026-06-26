# BUG-2026-06-25 — Chat history disappears when switching to the Corpus tab

**Status:** resolved (local green)
**Severity:** high (data loss: client-side chat history is lost, not merely hidden)
**Feature:** F3 / chat-rag-frontend (client-side conversation history, ADR-004)
**Reported:** 2026-06-25
**Source:** GitHub issue [#53](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/53) (P1, Ready)
**Branch:** `fix/chat-tab-corpus-state`

## Error description

When the user navigates from the Chat view to the Corpus tab in the ChatRAG UI and then
returns to Chat, the conversation is gone. The history is permanently lost (per issue intake
2026-05-30), not just visually hidden.

## Repro

1. Open the Chat UI.
2. Ask a question (chat shows the user + assistant messages).
3. Click the **Corpus** tab.
4. Click **Chat** (or **Back to chat**) to return.
5. **Expected:** prior chat messages still present.
6. **Actual:** message list is empty — history lost.

## Error logs

No exception — a state-management regression. The mount/unmount chain:

```
App.tsx (AppContent):
  onCorpus ? <CorpusBrowse/> : <ChatPanel/>      // conditional render → mount/unmount

ChatPanel:
  const { messages, ... } = useChatHistory();    // useState lives INSIDE ChatPanel

Navigate to /corpus → ChatPanel unmounts → useChatHistory state (messages) destroyed.
Navigate back to /   → fresh ChatPanel mounts → messages = [] (empty history).
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-25 | `useChatHistory()` stores `messages` in React `useState`, and is called *inside* `ChatPanel` (`ChatPanel.tsx:28-35`). |
| 2026-06-25 | `App.tsx` renders the Corpus view with a conditional `onCorpus ? <CorpusBrowse/> : <ChatPanel/>` (`App.tsx:45-53`), which unmounts `ChatPanel` on navigation to `/corpus`. |
| 2026-06-25 | Unmounting `ChatPanel` discards its local `messages` state; returning mounts a new instance with an empty history. `usePathname` navigation does not preserve component state. |

**Root cause:** Code bug — conversation state is owned by a component (`ChatPanel`) that is
conditionally unmounted on tab navigation, so the state is destroyed and re-initialized empty.

## Spec conformance

| Check | Result |
|-------|--------|
| F3 / ADR-004: chat history is client-side-only and must never be sent to the server | Honored — fix lifts state within the SPA only; no persistence, no server contact |
| F3 scope | In scope — regression fix on the chat UI; no API/contract change |
| `docs/api-contract.md` | No change — purely client-side state lifecycle |

No blocking spec drift.

## Repro test

- Path: `apps/chat-rag-frontend/src/test/test_bug_2026_06_25_chat_corpus_tab_state_loss.test.tsx`
- Red (before fix): ask a question → switch to Corpus → switch back to Chat → user message
  gone (message list empty / `emptyHint` shown).
- Green (after fix): the user/assistant messages survive the Chat → Corpus → Chat round-trip.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-25 | Add Vitest repro rendering `<App/>`, ask → Corpus → back | RED — history lost on return |
| 2 | 2026-06-25 | Lift `useChatHistory` to `AppContent`; `ChatPanel` accepts injected history | GREEN |

## Remediation path

Local-first (user choice 2026-06-25). Fix on `fix/chat-tab-corpus-state`; PR to `main`; deploy
only after user approval.

## Verification plan

- **Success criterion:** chat messages persist across Chat ⇄ Corpus navigation within a session.
- **Checks:** red→green Vitest repro test; full `chat-rag-frontend` lint + test + build; watch
  `ci.yml` on the branch after push.
- **Monitoring:** staging smoke H4–H5 only if/when deployed (frontend behavior change).

## Fix

- `App.tsx`: call `useChatHistory()` in `AppContent` (which stays mounted across tab switches)
  and pass the history instance into `<ChatPanel chat={chat} />`.
- `ChatPanel.tsx`: accept an optional `chat?: ChatHistory` prop; use it when provided, else fall
  back to its own `useChatHistory()` (keeps `ChatPanel` usable standalone and existing unit tests
  unchanged). The hook is always called unconditionally (rules of hooks).
- `useChatHistory.ts`: export a `ChatHistory` type for the prop.
- Regression: `test_bug_2026_06_25_chat_corpus_tab_state_loss.test.tsx`.

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass (local) | repro red→green; `npm run lint` clean; `npm test` 83 passed (16 files); `npm run build` (`tsc --noEmit` + `vite build`) ok |
| L2 Reproduction | pass (local) | repro test executes issue #53 steps (ask → Corpus → back) and the conversation survives |
| CI | pending | watch `ci.yml` on `fix/chat-tab-corpus-state` after push |

## Regression prevention

- New regression test: `test_bug_2026_06_25_chat_corpus_tab_state_loss.test.tsx`.

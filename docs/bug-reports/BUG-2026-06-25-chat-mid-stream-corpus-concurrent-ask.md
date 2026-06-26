# BUG-2026-06-25 — Mid-stream Corpus tab switch loses in-flight ask state (concurrent stream)

**Status:** resolved (local green)
**Severity:** medium (no data loss; requires switching tabs before a stream completes — can produce duplicate/interleaved assistant messages)
**Feature:** F3 / chat-rag-frontend (client-side chat, ADR-004)
**Reported:** 2026-06-25
**Source:** PR [#68](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/68) review (PRR-010) — Bugbot finding, triaged 🟡; inline thread on `ChatPanel.tsx:43`
**Branch:** `fix/chat-tab-corpus-state`

## Error description

The #53 fix lifted the conversation **history** (`useChatHistory`) into the always-mounted
`AppContent` shell so it survives Chat ⇄ Corpus navigation. However, the **in-flight ask
lifecycle** (`loading`) was left as local `useState` inside `ChatPanel`. If the user switches
to the **Corpus** tab *while a stream is still running* and returns to Chat, `ChatPanel`
remounts with `loading` reset to `false`. The **Ask** control is re-enabled while the original
`streamAsk` loop is still appending tokens to the now-shared history. A second submission then
runs a concurrent stream against the same `messages`, producing duplicate user/assistant pairs
and interleaved tokens.

This does not affect the #53 fix (the normal Chat ⇄ Corpus round-trip is correct) and requires
switching tabs before a stream completes, so it is non-blocking.

## Repro

1. Open the Chat UI.
2. Ask a question and, **before the answer finishes streaming**, click the **Corpus** tab.
3. Click **Chat** to return.
4. **Expected:** the Ask control stays disabled / "Asking…" until the original stream finishes.
5. **Actual (before fix):** the Ask control is enabled again; submitting a second question
   spawns a concurrent stream against the shared history.

## Error logs

No exception — a state-management regression (partial state lift). Mount/unmount chain:

```
App.tsx (AppContent):
  const chat = useChatHistory();                 // history lifted (#53 fix) — survives
  onCorpus ? <CorpusBrowse/> : <ChatPanel chat={chat}/>   // conditional render → mount/unmount

ChatPanel:
  const [loading, setLoading] = useState(false); // loading NOT lifted — local to ChatPanel
  handleSubmit: if (!trimmed || loading) return; // guard relies on local loading

Navigate to /corpus mid-stream → ChatPanel unmounts → local `loading` destroyed.
Navigate back to /            → fresh ChatPanel mounts → loading = false (Ask re-enabled),
                                while the original streamAsk loop is still running against the
                                shared (lifted) history → concurrent stream on next submit.
```

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-25 | `useChatHistory` (history) is owned by `AppContent` and passed to `ChatPanel` via `chat` prop (`App.tsx:16,56`). It survives tab switches. |
| 2026-06-25 | `loading` is local `useState` in `ChatPanel` (`ChatPanel.tsx:31`); the in-flight-ask guard `if (!trimmed \|\| loading) return;` (`ChatPanel.tsx:83`) depends on it. |
| 2026-06-25 | The `streamAsk` consumer in `handleSubmit` closes over the **stable** lifted history setters, so tokens keep appending after unmount; only `loading` (and `error`/`statusMessage`) is lost on remount. |
| 2026-06-25 | On remount, `loading=false` re-enables **Ask**; a second submit calls `streamAsk` again → concurrent stream / duplicate messages. |

**Root cause:** Code bug — partial state lift. The in-flight ask state (`loading`) lives in a
conditionally-unmounted view (`ChatPanel`) instead of the always-mounted shell, so it resets on
the Corpus round-trip and no longer blocks a concurrent submission.

## Spec conformance

| Check | Result |
|-------|--------|
| F3 / ADR-004: chat history client-side-only, never sent to server | Honored — fix lifts `loading` within the SPA only; no persistence, no server contact |
| `.cursor/rules/frontend-session-state-lifting.mdc` (session state above conditional views) | This bug is exactly the rule's class; the fix extends the lift to the in-flight lifecycle |
| `.cursor/rules/chat-rag-cold-start-retry.mdc` | Unchanged — `streamAsk` retry/cold-start surface (`ask.ts`) is not modified |
| `docs/api-contract.md` | No change — purely client-side state lifecycle |

No blocking spec drift.

## Repro test

- Path: `apps/chat-rag-frontend/src/test/test_bug_2026_06_25_chat_mid_stream_corpus_concurrent_ask.test.tsx`
  (frontend React/Vitest bug — colocated with the #53 regression test, mirroring that
  convention; the Python `tests/bugs/` layout cannot exercise the React component lifecycle).
- Red (before fix): ask with a never-resolving stream → switch to Corpus → back to Chat → the
  Ask control is enabled with the "Ask" label (loading lost).
- Green (after fix): after the round-trip the Ask control still shows "Asking…" and is disabled,
  and the in-flight stream is not duplicated.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-25 | Add Vitest repro: ask (pending stream) → Corpus → back; assert Ask stays "Asking"/disabled | RED — Ask re-enabled after round-trip |
| 2 | 2026-06-25 | Lift `loading` + `setLoading` into `useChatHistory`; `ChatPanel` consumes them from the chat object | GREEN |

## Remediation path

Local-first (PR review follow-up, PRM cycle on PR #68). Fix on `fix/chat-tab-corpus-state`;
no separate deploy — folds into the existing #53 hotfix PR.

## Verification plan

- **Success criterion:** the in-flight ask state survives the Chat ⇄ Corpus round-trip — the Ask
  control stays disabled until the original stream completes; no concurrent stream is possible.
- **Checks:** red→green Vitest repro; full `chat-rag-frontend` lint + test + build; watch
  `ci.yml` on the branch after push.
- **Monitoring:** staging smoke H4–H5 only if/when deployed (frontend behavior change).

## Fix

- `useChatHistory.ts`: own `loading` + `setLoading` in the hook so they are lifted alongside
  `messages` into the always-mounted shell.
- `ChatPanel.tsx`: consume `loading`/`setLoading` from the chat object instead of local
  `useState`.
- Regression: `test_bug_2026_06_25_chat_mid_stream_corpus_concurrent_ask.test.tsx`.
- Out of scope (deliberately deferred): threading an `AbortController` through `streamAsk` —
  it would change the `ask.ts` API surface and the cold-start retry rule; lifting `loading`
  fully resolves the concurrency. `error`/`statusMessage` remain local (cosmetic, not a
  concurrency hazard).

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass (local) | repro red→green; `npm run lint` clean; `npm test` 84 passed (17 files); `npm run build` (`tsc --noEmit` + `vite build`) ok |
| L2 Reproduction | pass (local) | repro test executes the mid-stream Corpus round-trip (ask → Corpus → back → Ask stays "Asking"/disabled, no second stream) |
| CI | pending | `ci.yml` on `fix/chat-tab-corpus-state` after push |

**PR:** [#68](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/68) (not merged — awaiting user approval).

## Related

- BUG-2026-06-25 — chat history disappears on Corpus tab (`docs/bug-reports/BUG-2026-06-25-chat-disappears-on-corpus-tab.md`) — the #53 fix this finding follows up.

## Regression prevention

- New regression test: `test_bug_2026_06_25_chat_mid_stream_corpus_concurrent_ask.test.tsx`.
- `.cursor/rules/frontend-session-state-lifting.mdc` already covers lifting session-scoped state;
  this bug is an instance of incomplete lift. Rule wording is sufficient (no new rule needed).

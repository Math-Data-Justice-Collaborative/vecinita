# BUG-2026-07-25 — Previous chats restore with empty Vecinita response

> Status: **fix_applied_local**
> Issue: **#145**
> Session: **S011-hotfix-retag-empty-chats**
> Feature: **F33** (browser-local persistent chat history) / UJ-025
> Component: `apps/chat-rag-frontend` (`useConversationStore`, `useChatHistory`, `ChatPanel`, `PreviousChatsList`)

## Error description

When opening a conversation from the **previous-chats** list, the **user question** appears but the **Vecinita (assistant) response is empty** (`message-content` blank).

## Error logs

No server stack (client-only history). Staging (2026-07-25):

```text
# Before deploy sync (missing chat-rag PROXY_KEY):
Ask → cold-start / LLM 401 exhaustion → error text archived (non-empty).

# After PROXY_KEY sync + chat-rag redeploy:
Ask → stream tokens → New chat → select → assistant + sources restored (happy path OK).

# Repro of empty archive (unit):
Ask (stream held open) → select another previous chat → tokens update only `active`
→ archived conversation keeps assistant content "".
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Restored assistant bubble empty |
| Where | ChatRAG frontend (staging) |
| Reported | Issue #145 |
| Frequency | Mid-stream previous-chat select (New chat already blocked while loading) |
| Severity | High for UJ-025 |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `newChat` archives before tokens flush | **Rejected** — New chat disabled while `loading`; Vitest happy path green |
| H2 | `selectConversation` drops assistant messages | **Rejected** — restores full `messages` array |
| H3 | localStorage validation strips content | **Rejected** |
| H4 | Render hides empty stored content | Symptom when `content === ""` |
| H5 | Staging ask never yields tokens (proxy key) | **Observed** — fixed via deploy sync (RD-165) |
| H6 | Mid-stream `selectConversation` archives empty placeholder; later tokens miss archived id | **Confirmed** — `setActiveMessages` only patched `active` |

### Root cause

`appendAssistantToken` / `setAssistantSources` only updated the **active** conversation. Selecting a previous chat mid-stream archives the in-flight turn (empty assistant placeholder). Subsequent SSE tokens no longer match any message in `active`, so the archived assistant stays blank.

Contributing ops issue: chat-rag lacked `VECINITA_MODAL_PROXY_KEY`, so many Ask attempts failed before a successful stream could be archived (confused with empty restore).

## Repro test

| Test | Path | Status |
|------|------|--------|
| Happy-path restore after New chat | `apps/chat-rag-frontend/src/test/test_bug_2026_07_25_previous_chats_empty_assistant.test.tsx` | green |
| Previous-chat select disabled while asking | same | green |
| `updateMessageById` patches archived in-flight assistant | `apps/chat-rag-frontend/src/hooks/useConversationStore.test.ts` | green (was the red race) |

## Fix

1. `useConversationStore.updateMessageById` — patch by message id in **active or previous**.
2. `useChatHistory` token/sources writers use `updateMessageById`.
3. Disable previous-chat select while `chat.loading` (same guard as New chat).

## Deploy

- ChatRAG frontend redeploy after merge.
- Staging smoke: Ask → New chat → select; optionally attempt select while Asking (should be disabled).

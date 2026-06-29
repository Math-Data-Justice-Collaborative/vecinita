# ADR-024: ChatRAG chat-history persistence design (`useConversationStore` + sessionStorage)

**Status:** Superseded in part by [ADR-025](ADR-025-chat-history-localstorage-persistence.md)
**Stage:** 04-tech-plan (S003)
**Date:** 2026-06-26
**Feature:** F33 — Browser-local persistent chat history
**Builds on:** ADR-023 (device-only, tab-scoped persistence policy)

> **Update (2026-06-28, ADR-025):** §2/§3 below specify write-through to `sessionStorage`.
> Per ADR-025 the store now writes to **`localStorage`** (durable, cross-tab). The
> `useConversationStore` architecture, envelope schema (`vecinita.chat.history.v1`,
> `version: 1`), cap/label/fallback design, and previous-chats UI are otherwise unchanged.

## Context

ADR-023 established the **policy**: ChatRAG chat history may be persisted on the user's device
via `sessionStorage` (per-tab, cleared on tab close, never transmitted). This ADR records the
**technical design** that implements that policy, resolving the items 01-requirements deferred
to 04-tech-plan (storage key, serialized schema/versioning, label truncation, and the
persistence-layer architecture).

Today the active conversation lives in `useChatHistory` (in-memory React state) lifted to the
always-mounted `AppContent` shell, which survives in-app Chat ⇄ Corpus navigation
(BUG-2026-06-25 / #53, PR #68) but is wiped on refresh / tab-away. F33 also adds a **list of
previous conversations** the user can revisit.

## Decision

### 1. Persistence layer — `useConversationStore` (TP-S003-02)

Introduce a new hook **`useConversationStore`** (in `apps/chat-rag-frontend/src/hooks/`) that:

- Owns the **active conversation** plus a capped **previous-conversations list**.
- Is **write-through** to `sessionStorage` on every mutation.
- Is lifted to the `AppContent` shell (alongside the existing lifted chat state, per
  `frontend-session-state-lifting.mdc`).

`useChatHistory` is refactored to read/write its active-conversation slice **through** the
store, preserving its current public shape (`messages`, `append*`, `setAssistantSources`,
`clearHistory`, `loading`, `setLoading`) so `ChatPanel` is unchanged at the message level and
the standalone-fallback pattern (PR #68) still holds.

Store operations: `newChat` (archive active → list, start empty), `selectConversation(id)`
(restore as active), `deleteConversation(id)`, `clearAll` (empty the list), and the existing
`clearHistory` (reset the active conversation).

### 2. Storage key + serialized schema (TP-S003-01)

- **Key:** `vecinita.chat.history.v1` (version suffix allows future migration).
- **Envelope:**

```ts
type Conversation = { id: string; messages: ChatMessage[]; createdAt: number };
type ChatHistoryEnvelope = {
  version: 1;
  active: Conversation;
  previous: Conversation[]; // newest first, capped at 10 (FIFO)
};
```

  Reuses the existing `ChatMessage` / `Source` types (`src/api/types.ts`) — sources are
  serialized with the messages so they rehydrate (TC-072). Unknown/old/corrupt payloads are
  ignored (treated as empty) rather than throwing.

### 3. Cap, label, timing (TP-S003-05/06/10)

- **Cap:** last **10** conversations, FIFO eviction of the oldest (RD-070).
- **Label:** first user message **truncated to 60 chars** + a relative timestamp rendered with
  **`Intl.RelativeTimeFormat`** in the active UI locale (RD-071).
- **Write timing:** write-through on mutation. `sessionStorage` already survives same-tab
  refresh and tab-away, so no `visibilitychange`/`pagehide` flush is needed.

### 4. Previous-chats UI (TP-S003-03)

A **collapsible panel inside `ChatPanel`** (the Chat view) lists previous conversations
(newest first) with a "New chat" action, per-item select/delete, and "Clear all history".
Not placed in the shell sidebar (would clutter the Corpus tab). New i18n keys are added to the
**app-local** `messages.ts` EN/ES tables (TP-S003-04; see Consequences re: EV-004).

### 5. Graceful degradation (TP-S003-09)

All `sessionStorage` access is wrapped in try/catch. On failure (quota exceeded, disabled,
private-mode throw) the store falls back to **in-memory** state for the session — chat keeps
working, persistence is silently disabled, no uncaught error (TC-073, AC-S2).

## Consequences

- **Rule update:** `.cursor/rules/frontend-session-state-lifting.mdc` point 4 is amended to
  permit **device-only, tab-scoped `sessionStorage`** persistence for chat history (citing
  ADR-023/024), while still forbidding any server/off-device persistence. Done at
  04-tech-plan (03/06 tooling stages skipped under evolve-lite).
- **EV-004 coordination (TP-S003-04):** EV-004 migrates ChatRAG i18n to
  `packages/frontend-i18n` on `fix/es-en-full-ui` (unmerged). S003 is based on `main` and adds
  keys to app-local `messages.ts`. Whichever PR merges second ports the new keys into the
  shared package — tracked in execution-plan Open Questions.
- **Privacy (AC-S6):** No history crosses the network, DB, or logs; server stays stateless
  (F3 unchanged). Verified in 09-qa + 10-e2e.
- **No new dependencies, no API/contract/CORS changes** (AC-S7) — `sessionStorage` and
  `Intl.RelativeTimeFormat` are browser built-ins.
- **Trade-offs (inherited from ADR-023):** history does not survive tab close and is not
  shared across tabs/devices/browsers. A durable variant would move to `localStorage` under a
  new ADR.

## References

- Policy: ADR-023 (device-only, tab-scoped persistence)
- Feature: `docs/feature-list.md` §F33
- Journeys: `docs/user-journeys.md` UJ-024, UJ-025
- Tests: `docs/test-plan.md` TC-072–TC-076
- Acceptance: `docs/acceptance-criteria.md` AC-S1–AC-S7
- Decisions: `docs/decisions.md#technical-decisions-05-verify-tech` §S003 (TP-S003-01–12, TV-S003-01); `docs/decisions.md#requirements-decisions-01-requirements` RD-068–RD-072
- Plan: `docs/execution-plan.md` §Phase 10
- Related: ADR-004 (zero personal data / stateless chat)

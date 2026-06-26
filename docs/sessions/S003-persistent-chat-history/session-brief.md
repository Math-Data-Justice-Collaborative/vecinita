# S003 — Browser-Local Persistent Chat History

- **Session ID:** S003-persistent-chat-history
- **Type:** feature (evolve)
- **Branch:** `feat/S003-persistent-chat-history`
- **Opened:** 2026-06-26
- **Orchestrator:** 16-evolve (evolve-lite routing)

## Intent

Give the chat-rag-frontend main page an **ephemeral, browser-local chat history** so a
user's conversation is not lost on page refresh or when switching browser tabs, and so the
user can revisit earlier conversations.

Today `useChatHistory` keeps the conversation in in-memory React state lifted to the
always-mounted `AppContent` shell. That survives **in-app** Chat ⇄ Corpus navigation
(BUG-2026-06-25 / #53, PR #68) but is **wiped on page refresh, tab close, or browser-tab
navigation** because nothing is persisted to browser storage.

## Scope (both — user decision)

1. **Persist the active conversation** across page refresh, tab-away, and switching browser
   tabs, using **`sessionStorage`** (device-only; never sent to the server; cleared when the
   browser tab is closed).
2. **List of previous conversations** — keep a selectable list of past chats on the main page
   so the user can open a prior conversation.

Frontend-only delta in `apps/chat-rag-frontend`. No backend, API, or contract changes.

## Key decisions (AskQuestion 2026-06-26)

| Decision | Choice | Rationale |
|---|---|---|
| Active-session handling | Pause/park S002, open S003 | New unrelated feature; one active session allowed |
| Scope | Persist current conversation **and** previous-chats list | User wants both |
| Privacy / storage | **`sessionStorage`** (not localStorage) | Narrower footprint — cleared on tab close; still survives refresh + tab-away |
| Routing | evolve-lite (approved) | Small frontend-only delta |

## Privacy note (ADR-004)

ADR-004 + `.cursor/rules/frontend-session-state-lifting.mdc` currently say chat history is
"client-side-only ... never persist to the server or to storage that leaves the browser."
`sessionStorage` stays on the user's device and is never transmitted, so it is consistent with
the "zero personal data on server / client-side only" intent. ADR-004 and the rule will be
revisited in 01/04 to explicitly permit **device-only, tab-scoped** persistence.

## Out of scope

- No server-side chat/session persistence (ADR-004).
- No cross-device or cross-browser sync.
- No persistence that survives closing the browser tab (sessionStorage by design).
- No changes to the admin (data-management) frontend.

## Carried-forward note

S002-admin-job-management is **paused** (not complete) with open blockers (Modal `GET /jobs`
405, typecheck `reportAny`, jobs dialog aria warning, deploy not ready). Its branch
`feat/S002-admin-job-management` is preserved for resumption.

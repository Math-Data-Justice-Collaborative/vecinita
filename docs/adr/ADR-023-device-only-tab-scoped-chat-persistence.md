# ADR-023: Device-only, tab-scoped client-side chat persistence (sessionStorage)

**Status:** Accepted
**Stage:** 01-requirements (S003)
**Date:** 2026-06-26
**Feature:** F33 — Browser-local persistent chat history

## Context

ADR-004 (zero personal data) keeps ChatRAG **stateless on the server**: no `sessions` /
`messages` tables, no server-side conversation memory, and "no … chat history tied to
identity." It allows multi-turn context only "purely in browser memory (client-only)."

Today the ChatRAG conversation lives in in-memory React state (`useChatHistory`) lifted to
the always-mounted `AppContent` shell. That survives in-app Chat ⇄ Corpus navigation
(BUG-2026-06-25 / #53, PR #68) but is **lost on page refresh, tab close, or switching
browser tabs**, because nothing is written to browser storage.

The user (S003) asked for an **ephemeral, browser-local chat history** that:
1. persists the active conversation across page refresh and leaving/returning to the tab, and
2. keeps a selectable list of previous conversations to revisit.

This requires writing chat content to web storage, which is in tension with two existing
statements that must be reconciled:

- **ADR-004**: chat allowed only "purely in browser memory (client-only)".
- **`.cursor/rules/frontend-session-state-lifting.mdc`**: lift chat state "within the SPA
  only … never persist to the server or to storage that leaves the browser."

## Decision

Permit **device-only, tab-scoped** persistence of ChatRAG chat history in the browser using
**`sessionStorage`** (R41 / RD-068). Specifically:

- The active conversation and a capped list of previous conversations are serialized to
  `sessionStorage` on the user's device.
- This data is **never** transmitted to the server, written to the database, or emitted to
  logs. The server remains stateless (F3 unchanged); no session/message row is created.
- Persistence is **per-tab** and **cleared when the browser tab closes** (a property of
  `sessionStorage`). A brand-new/duplicate tab starts empty. This narrower footprint
  (vs. `localStorage`) was the user's explicit privacy preference (R41).

Behavior parameters (from the 01-requirements interview):

| Aspect | Decision | Ref |
|--------|----------|-----|
| Storage mechanism | `sessionStorage` (device-only, per-tab) | R41, RD-068 |
| Conversation boundary | Explicit "New chat" archives current, starts fresh | R44, RD-069 |
| History cap / eviction | Last 10, FIFO | R45, RD-070 |
| Previous-chat label | First user message + relative timestamp | R46, RD-071 |
| Clear / delete | "Clear" active; per-item delete + "Clear all history" for list | R47, RD-072 |
| Failure mode | Degrade to in-memory state if storage full/disabled | TC-073 |

### Relationship to ADR-004

ADR-004's intent is **no personal data on the server** and a **stateless backend**. Storing
chat content in `sessionStorage` keeps all of it **on the user's own device**, never crossing
the network. This is consistent with ADR-004's "client-only" allowance; ADR-004 §"Application
— stateless chat" (no server-side store, no identity-keyed checkpoints) and the F15 privacy
guardrails (server schema + logs) are **unchanged**. ADR-004 is **not superseded** — this ADR
clarifies that the "client-only" allowance includes device-only web storage, not just RAM.

## Consequences

- **`.cursor/rules/frontend-session-state-lifting.mdc`** must be updated so its "within the
  SPA only … never persist to storage" wording explicitly permits **device-only, tab-scoped**
  `sessionStorage` persistence for chat history. Scheduled for 04-tech-plan / 07-build (the
  03/06 tooling stages are skipped under evolve-lite).
- Acceptance criteria **AC-S6** asserts no chat history reaches the server, DB, or logs, and
  that persistence is per-tab + cleared on tab close — verified in 09-qa and 10-e2e.
- Frontend-only delta in `apps/chat-rag-frontend`; **no** backend, API, contract, or CORS
  policy changes (AC-S7).
- Trade-off: history does **not** survive closing the tab and is **not** shared to new tabs,
  cross-device, or cross-browser (accepted, R43). If durable/local-device persistence is
  later required, revisit with a new ADR (would move to `localStorage` with a broader
  footprint).

## References

- Feature: `docs/feature-list.md` §F33
- Journeys: `docs/user-journeys.md` UJ-024, UJ-025
- Tests: `docs/test-plan.md` TC-072–TC-076
- Acceptance: `docs/acceptance-criteria.md` AC-S1–AC-S7
- Decisions: `docs/requirements-decisions.md` RD-068–RD-072; `docs/context-brief.md` §14 (R39–R42)
- Related: ADR-004 (zero personal data / stateless chat), F3, F15

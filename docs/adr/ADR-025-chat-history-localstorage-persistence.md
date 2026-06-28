# ADR-025: Chat history persists via `localStorage` (durable, cross-tab)

**Status:** Accepted
**Stage:** 07-build (S003, reopened)
**Date:** 2026-06-28
**Feature:** F33 — Browser-local persistent chat history
**Supersedes (in part):** ADR-023 §Decision (storage mechanism), ADR-024 §2/§3 (`sessionStorage` write-through)

## Context

ADR-023/024 implemented F33 with **`sessionStorage`** (per-tab, cleared on tab close,
not shared across tabs). That deliberately narrow footprint was the user's earlier
preference (R41/R43). Both ADRs explicitly anticipated this reversal: *"A durable variant
would move to `localStorage` under a new ADR."*

After F33 shipped (Phase 10 gate PASS), the user reviewed the behavior and requested that
chat history **persist across closing the tab and be available in new tabs** of the same
origin — i.e. durable device-local persistence rather than tab-ephemeral. The user
explicitly accepted the wider on-device footprint that entails.

## Decision

Persist ChatRAG chat history to **`localStorage`** instead of `sessionStorage`.

- The active conversation and the capped previous-conversations list are serialized to
  `localStorage` under the unchanged key `vecinita.chat.history.v1` (envelope schema
  `version: 1` is unchanged — no migration needed).
- History now **survives a tab close / browser restart** and is **readable by other tabs**
  of the same origin (each tab reads the shared store on mount).
- All other F33 behavior parameters are **unchanged**: explicit "New chat" boundary (R44),
  last-10 FIFO cap (R45/RD-070), first-message + relative-timestamp label (R46/RD-071),
  clear / per-item delete / clear-all semantics (R47/RD-072), and silent in-memory
  fallback when storage is unavailable (TC-073, AC-S2).

### Cross-tab scope

A newly opened or reloaded tab reads the shared `localStorage` on mount, satisfying the
user's "history persists in another tab" requirement. **Live** synchronization between two
**simultaneously open** tabs (via `storage` events) is **not** implemented — concurrent
tabs use last-write-wins on their next write. This is an accepted scope boundary; revisit
with a `storage`-event listener only if simultaneous multi-tab editing becomes a need.

## Relationship to ADR-004 (unchanged)

`localStorage` is still **device-local** — chat content **never crosses the network**, is
**never written to the database or logs**, and **no server-side session/message row** is
created. ADR-004 (zero personal data, stateless backend), F3, and the F15 privacy
guardrails are **unchanged**. The only change versus ADR-023 is the on-device retention
window (until explicitly cleared / browser data cleared, vs. tab close) and cross-tab
visibility.

## Consequences

- **Rule update:** `.cursor/rules/frontend-session-state-lifting.mdc` point 4 is amended to
  permit **device-local `localStorage`** persistence for chat history (was: forbid
  `localStorage`). Still forbids any server/off-device persistence.
- **Acceptance criteria:** AC-S1/AC-S2/AC-S5/AC-S6 wording updated from "tab-scoped
  `sessionStorage` / cleared on tab close" to "device-local `localStorage` / survives tab
  close, shared across tabs; still never leaves the device."
- **Tests:** `useConversationStore.test.ts`, `test_chat_history_persistence.test.tsx`, and
  `test_chat_history_privacy.test.tsx` assert `localStorage` persistence (and that history
  is absent from `sessionStorage`, cookies, and the network). 116 chat-rag-frontend Vitest
  tests pass; 95% coverage gate green; `tsc --noEmit` + ESLint clean; `vite build` green.
- **No new dependencies, no API/contract/CORS changes** (AC-S7) — `localStorage` is a
  browser built-in.
- **Trade-off accepted:** history is no longer ephemeral; it remains on the device until the
  user clears chat history or clears browser data. This is the user's explicit choice.

## References

- Supersedes: ADR-023 (sessionStorage policy), ADR-024 §2/§3 (sessionStorage design)
- Feature: `docs/feature-list.md` §F33
- Acceptance: `docs/acceptance-criteria.md` AC-S1, AC-S2, AC-S5, AC-S6, AC-S7
- Rule: `.cursor/rules/frontend-session-state-lifting.mdc` point 4
- Related: ADR-004 (zero personal data / stateless chat), F3, F15

# S003 — 04-tech-plan Report

- **Session:** S003-persistent-chat-history
- **Stage:** 04-tech-plan (evolve-lite delta)
- **Date:** 2026-06-26
- **Feature:** F33 — Browser-local persistent chat history
- **Branch:** `feat/S003-persistent-chat-history`

## Summary

Turned the approved F33 requirements (ADR-023, UJ-024/UJ-025, TC-072–TC-076, AC-S1–AC-S7,
RD-068–RD-072) into an execution-plan delta and resolved the technical decisions that
01-requirements deferred to this stage. Frontend-only — no backend, API, contract, CORS, or
dependency changes.

## Decisions (user-approved via AskQuestion 2026-06-26)

| ID | Decision |
|----|----------|
| TP-S003-01 | Storage key `vecinita.chat.history.v1`; versioned envelope `{version:1, active, previous[]}` reusing `ChatMessage`/`Source` |
| TP-S003-02 | New `useConversationStore` hook lifted to `AppContent`; `useChatHistory` backs onto its active slice |
| TP-S003-03 | Previous-chats list = collapsible panel inside `ChatPanel` |
| TP-S003-04 | New i18n keys added to app-local `messages.ts` on `main`; reconcile with EV-004 on second merge |
| TP-S003-05 | Label = first user msg ≤60 chars + `Intl.RelativeTimeFormat` (locale-aware) |
| TP-S003-06–08 | Cap 10 FIFO; "New chat" archives; "Clear"/per-item delete/"Clear all history" |
| TP-S003-09 | Degrade silently to in-memory on `sessionStorage` failure (TC-073) |
| TP-S003-10 | Write-through on mutation; no `visibilitychange`/`pagehide` flush needed |
| TP-S003-11 | Amended `frontend-session-state-lifting.mdc` to permit device-only tab-scoped `sessionStorage` |
| TP-S003-12 | No API/contract/CORS changes; no backend/Modal redeploy |

ADR-024 records the full persistence design.

## Plan delta

- **Phase 10** added to `docs/execution-plan.md`: **M39** store/persistence layer →
  **M40** wire into shell + rehydration → **M41** previous-chats UI + actions/i18n →
  **M42** rule verify + privacy + full suite. **17 tasks** (T39.1–T42.3); total **239**.
- TDD ordering preserved (test-before-code within each milestone).
- PR-46 (Major, Phase 10 → `main`) added; evolve-lite single-branch like S002.

## Artifacts changed

- `docs/execution-plan.md` — Phase 10, Current State, PR Plan, Task Tracking, Open Questions, header
- `docs/tech-decisions.md` — §S003 (TP-S003-01–12, TV-S003-01) + merge-coordination note
- `docs/adr/ADR-024-chat-history-persistence-design.md` (new) + `docs/adr/README.md` index
- `docs/requirements-decisions.md` — F33 unresolved items marked resolved
- `.cursor/rules/frontend-session-state-lifting.mdc` — device-only `sessionStorage` allowance + new regression-guard ref

## Open / carried forward

- **EV-004 i18n merge coordination (TP-S003-04):** new chat-history keys live app-local;
  port to `packages/frontend-i18n` whenever S003 / EV-004 merges second.
- No new dependencies; `dependency-inventory.md` unchanged (built-in `sessionStorage` + `Intl`).

## Skipped stages (evolve-lite)

02-verify-plan, 03-plan-tooling, 05-verify-tech, 06-tech-tooling, 11-verify-impl — per routing plan.

## Next stage

**07-build** — implement M39–M42 TDD; then 09-qa → 10-e2e → 12-verify-deploy → 13-deploy-smoke.

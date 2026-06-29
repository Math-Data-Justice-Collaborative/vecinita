# Chat RAG Screen Redesign — Design Brief

**Session:** S003-persistent-chat-history (delta — folded in per user decision)
**Stage:** 00-context (design derivation)
**App:** `apps/chat-rag-frontend`
**Date:** 2026-06-28
**Reference:** ChatGPT-style sidebar layout (user-provided screenshot)

## 1. Intent

Restructure the chat-rag-frontend main screen from a single centered column into a
ChatGPT-style two-region layout: a persistent left **sidebar** for navigation + chat
management, and a main **conversation area** with a centered welcome state. This is a
**full visual overhaul** (new theme, typography, spacing, components), not just a
re-layout.

## 2. Derived decisions (from clarifying interview)

| # | Question | Decision |
|---|----------|----------|
| D1 | Session handling | Fold into existing session **S003** (continue same session) |
| D2 | Scope | **Full visual overhaul** — new theme, typography, spacing, components |
| D3 | Left sidebar contents | New chat button · Recent/previous chats list · Chat/Corpus nav · Tag filters · Language toggle |
| D4 | Empty state | Centered greeting + centered input when empty; input **relocates to bottom** once a conversation starts |
| D5 | Quick-action chips | Yes — **tailored to Vecinita** (suggested community questions / tag shortcuts), not the generic ChatGPT actions |
| D6 | Right-hand panel | **None** — sources stay inline under each answer |
| D7 | Responsive | Sidebar is **collapsible** behind a hamburger toggle on narrow screens |

### Resolved decisions (follow-up interview)

| # | Question | Decision |
|---|----------|----------|
| D8 | Theme mode | **Dark default + light/dark toggle** (persisted to `localStorage`) |
| D9 | Sidebar chat search | **Omit for v1** — recent chats list only |
| D10 | Suggested-question content | **Generic community samples**, localized EN/ES (e.g., food pantry hours, rent assistance, ESL classes) |
| D11 | Proceed | Draft a short build plan (components + tests), then implement with TDD |

### Assumptions (reasonable defaults — flag if wrong)

- **A2 — Account section:** No bottom "account" block (not selected in D3); Vecinita has no
  user accounts / personal data (privacy constraint F3, ADR-025).
- **A3 — Corpus stays a route** (`/corpus`) but its entry point moves from the top tab into
  the sidebar nav. The Corpus browse screen itself is restyled to match the new theme but
  keeps its current structure/behavior.
- **A4 — Quick-action chips** surface 3–4 suggested community questions (localized EN/ES);
  clicking one prefills the input. A "filter by topic" affordance maps to existing tag chips.
- **A5 — Theme persistence:** theme choice stored in `localStorage` (`vecinita.theme.v1`),
  device-local only, consistent with the privacy posture; default dark; respects nothing
  from the server.

## 3. Target layout

```
+----------------+-------------------------------------------+
|  SIDEBAR       |  MAIN (conversation area)                 |
|  (collapsible) |                                           |
|  [+ New chat]  |   empty state:                            |
|  ── nav ──     |        "What can I help with?"            |
|   Chat         |        [ centered input box ]             |
|   Corpus       |        [chip][chip][chip]  (suggested Qs) |
|  ── topics ──  |                                           |
|   tag chips    |   active state:                           |
|  ── recent ──  |        [ message list, scrolls ]          |
|   chat 1       |        ...                                |
|   chat 2       |        [ input docked at bottom ]         |
|   ...          |                                           |
|  [ EN | ES ]   |                                           |
+----------------+-------------------------------------------+
```

- **Narrow screens:** sidebar hidden; a hamburger toggle opens it as an overlay/drawer.
- **Sources:** rendered inline beneath each assistant answer (unchanged behavior, restyled).

## 4. Behavior preserved (must not regress)

- Chat history is **device-local only** (`localStorage` key `vecinita.chat.history.v1`),
  never sent to server (ADR-025, frontend-session-state-lifting rule). Conversation state
  stays lifted in the always-mounted shell so it survives Chat ⇄ Corpus navigation
  (BUG-2026-06-25 / #53).
- Cold-start retry + status messaging in `streamAsk` / `ChatPanel` (chat-rag-cold-start
  rule) unchanged.
- Bilingual i18n (EN/ES) via `messages.ts` `t()`; all new UI strings added to both tables.
- Inline source/citation list per answer.

## 5. New i18n strings (to add EN + ES)

- `welcomeHeading` — "What can I help with?"
- `suggestedQuestionsLabel`, and 3–4 suggested-question strings
- `sidebarToggle` (open/close), `recentChats` (if distinct from `previousChats`)
- Any new section labels (e.g., `topicsHeading`)

## 6. Open questions — RESOLVED

- **O1 — Theme mode:** Dark default + light/dark toggle (D8).
- **O2 — Sidebar "Search chats":** Omit for v1 (D9).
- **O3 — Suggested questions:** Generic localized community samples (D10).

## 7. Build plan (components + tests)

### Components / files

| Component | File | Responsibility |
|-----------|------|----------------|
| `AppShell` (restyle) | `src/App.tsx` | Two-region grid: `<Sidebar>` + `<main>`; owns sidebar open/close + theme; keeps lifted chat store/history |
| `Sidebar` (new) | `src/components/Sidebar.tsx` | New-chat btn, Chat/Corpus nav, tag-filter chips, recent chats list, language toggle; collapsible |
| `ThemeToggle` (new) | `src/components/ThemeToggle.tsx` | Light/dark toggle; persists to `localStorage` (`vecinita.theme.v1`) |
| `useTheme` (new) | `src/hooks/useTheme.ts` | Read/write theme, apply `data-theme` on root, graceful fallback |
| `ChatPanel` (restyle) | `src/components/ChatPanel.tsx` | Welcome (centered) ↔ active (docked input) states; suggested chips when empty; move PreviousChats/Tags out into Sidebar |
| `SuggestedQuestions` (new) | `src/components/SuggestedQuestions.tsx` | Localized sample-question chips; click prefills input |
| `PreviousChatsList` (adapt) | `src/components/PreviousChatsList.tsx` | Render as always-visible sidebar list (drop collapse) |
| Theme + layout CSS | `src/App.css` | CSS variables for light/dark tokens; grid layout; responsive drawer |
| i18n | `src/i18n/messages.ts` | New keys (welcomeHeading, suggested questions, sidebar labels, theme labels) EN+ES |

### Tests (Vitest, TDD — write first)

- `Sidebar.test.tsx` — renders new-chat, nav, tags, recent chats, lang toggle; collapse toggle hides/shows; nav switches route.
- `ThemeToggle` / `useTheme.test.ts` — toggles `data-theme`, persists + rehydrates from `localStorage`, falls back in-memory on storage failure.
- `ChatPanel.test.tsx` (extend) — empty state shows welcome heading + suggested chips; sending a message hides welcome and docks input; suggested-chip click prefills the textarea.
- `App.test.tsx` (extend) — Chat⇄Corpus nav from sidebar still preserves conversation (BUG-2026-06-25 guard remains green).
- i18n `messages.test.ts` — new keys present in both locales.

### Verify

Lint, typecheck (basedpyright N/A; `tsc`/eslint), full FE Vitest suite, `vite build`.

## 8. Status — IMPLEMENTED

Design + plan approved (D11 = plan then build). Implementation complete.

### Files added
- `src/components/Sidebar.tsx` — persistent left sidebar
- `src/components/ThemeToggle.tsx` — light/dark switch
- `src/components/SuggestedQuestions.tsx` — localized empty-state chips
- `src/hooks/useTheme.ts` — theme state + `localStorage` persistence (`vecinita.theme.v1`)
- `src/hooks/useTagFilters.ts` — tag fetch + selection lifted to the shell
- Tests: `useTheme.test.ts`, `useTagFilters.test.ts`, `test/Sidebar.test.tsx`

### Files changed
- `src/App.tsx` — sidebar + main grid shell; wires theme, tags, sidebar collapse
- `src/components/ChatPanel.tsx` — welcome ↔ active states, docked input, tags via prop,
  tags/recent removed (now in sidebar)
- `src/App.css` — full theme-token overhaul (dark default + light), grid layout,
  responsive off-canvas drawer
- `src/i18n/messages.ts` — new EN/ES keys (welcome, suggestions, sidebar, theme labels)
- Updated guard tests: `ChatPanel.test.tsx` (tags now prop-injected), i18n + language-toggle
  guard (toggle now in sidebar; single-toggle invariant preserved)

### Verification
- 134/134 Vitest tests pass (was 120; +14 net new)
- `tsc --noEmit` clean · `eslint src` clean · `vite build` succeeds
- BUG-2026-06-25 (#53) and F33 persistence guards remain green

### Notes / follow-ups
- Two pre-existing unformatted test files (`test_chat_history_persistence.test.tsx`,
  `test_previous_chats_list.test.tsx`) were left untouched (out of scope).
- Workflow-state S003 should be updated to record this UI-redesign delta (07-build reopen).

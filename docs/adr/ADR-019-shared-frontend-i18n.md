# ADR-019: Shared frontend i18n package (en/es)

**Status:** Accepted  
**Date:** 2026-06-13  
**Cycle:** EV-004  
**Stage:** 00-context  
**Deciders:** Product (evolve request)

## Context

Vecinita ships two browser SPAs: **chat-rag-frontend** (public ChatRAG) and **data-management-frontend** (admin). ChatRAG already implements en/es UI chrome via app-local `LocaleProvider`, `LanguageToggle`, and `i18n/messages.ts` with `localStorage` key `vecinita.locale`.

EV-004 (F31) adds the same bilingual operator experience to the admin dashboard. Duplicating locale detection, storage, and message tables in a second app would drift from ChatRAG defaults (e.g. ES fallback for non-en/es browsers) and complicate maintenance.

Resolution R29 (context-brief §13).

## Decision

Introduce a workspace TypeScript package **`packages/frontend-i18n`** (npm name `vecinita-frontend-i18n`) consumed by both frontends.

### Package surface (minimum)

| Export | Responsibility |
|--------|----------------|
| `Locale` type | `"en" \| "es"` |
| `detectBrowserLocale()`, `readStoredLocale()` | Browser default + `localStorage` read |
| `LOCALE_STORAGE_KEY` | `"vecinita.locale"` (shared across apps) |
| `messages` / `t(locale, key, ...)` | Namespaced EN/ES strings (`chat.*`, `admin.*`, `shared.*`) |

React components (`LanguageToggle`, `LocaleProvider`, etc.) live in **`packages/frontend-ui`** per ADR-020 — not in this package.

### App responsibilities

| App | Keeps local |
|-----|-------------|
| chat-rag-frontend | `ChatPanel`, `CorpusBrowse` page shell (Tailwind layout), routing |
| data-management-frontend | `AdminLayout`, pages, shadcn `ui/*`, bulk dialogs |

### Translation scope

- **In scope:** All static admin UI chrome (nav, headings, buttons, empty states, validation messages defined in frontend).
- **Out of scope:** Corpus document titles, tag labels, URLs, audit JSON payloads, API `error_message`, health/job status enum strings from backends (R30).

### Default locale

Match ChatRAG: browser `en*` → `en`, `es*` → `es`, otherwise **ES**.

## Consequences

- **Positive:** Single source of truth for locale rules and shared strings (e.g. `languageGroupLabel`); admin and ChatRAG stay aligned.
- **Positive:** No API, CORS, or database changes.
- **Negative:** One-time migration of ChatRAG off app-local `i18n/messages.ts`; both frontends must pin workspace packages in `package.json`.
- **Negative:** React UI components moved to ADR-020 `frontend-ui`; i18n package stays React-free.

## References

- `docs/context-brief.md` §13 (EV-004 delta), R28–R38
- ADR-020 (shared frontend UI components)
- `apps/chat-rag-frontend/src/i18n/messages.ts`
- `docs/bug-reports/BUG-2026-06-05-english-query-spanish-corpus.md` (ChatRAG i18n follow-up)

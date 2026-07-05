# ADR-020: Shared frontend UI component package

**Status:** Accepted  
**Date:** 2026-06-13  
**Cycle:** EV-004  
**Stage:** 00-context  
**Deciders:** Product (evolve request; assumptions R34–R38)

## Context

EV-004 (F31) adds bilingual en/es UI to the admin dashboard, mirroring ChatRAG. ADR-019 establishes `packages/frontend-i18n` for locale detection, storage, and message tables.

The user also requested a **shared component library** so ChatRAG and admin reuse the same UI/UX primitives (language toggle, locale provider, tag display, pagination) rather than duplicating React components with divergent styling.

Today:

| Concern | ChatRAG | Admin |
|---------|---------|-------|
| Styling | Plain CSS (`App.css`) | Tailwind + shadcn/ui (F23) |
| Locale context | App-local `LocaleContext.tsx` | None |
| Language toggle | App-local `LanguageToggle.tsx` | None |
| Tag UI | `TagFilterChips` (interactive) | `TagBadge` (read-only) |
| Pagination | Inline in `CorpusBrowse.tsx` | Inline in `AuditPage.tsx` |

Resolution R35, R37 (context-brief §13).

## Decision

Introduce **`packages/frontend-ui`** (npm name `vecinita-frontend-ui`) — a React component library consumed by both frontends. It **depends on** `vecinita-frontend-i18n` for `Locale`, `t()`, and message keys.

### Package surface (EV-004 minimum)

| Export | Responsibility |
|--------|----------------|
| `LocaleProvider`, `useLocale` | React context; `document.documentElement.lang`; `vecinita.locale` persistence |
| `LanguageToggle` | EN/ES pill control with accessible `role="group"` |
| `TagFilterChips` | Interactive tag filter buttons; locale-filtered facets |
| `TagBadge` | Read-only tag pill; LLM vs manual color variant |
| `PaginationControls` | Previous/Next buttons + page summary |
| `ThemeToggle` | System-preference light/dark control; bilingual labels via `frontend-i18n` (02-verify-plan audit) |

### Styling

- **`frontend-ui` uses Tailwind CSS** for component styling (R36).
- **Admin** already has Tailwind; imports components directly.
- **ChatRAG** migrates **full layout to Tailwind** in EV-004 (RD-056; supersedes prior “minimal scan-only” note). PostCSS `content` paths include `packages/frontend-ui/src/**/*.{tsx,ts}`.

### shadcn re-exports (RD-060)

`frontend-ui` re-exports a **minimal shadcn set** for shared components: `Button`, `Badge`, `Input`, `Label`, `Dialog`. Admin may continue using local shadcn for app-specific dialogs; shared primitives come from `frontend-ui`.

### Dependency rule (extends ADR-012)

```text
packages/frontend-i18n   ← no React dependency
packages/frontend-ui     ← depends on frontend-i18n; no apps/* imports
apps/*                   ← depend on both packages; no cross-app imports
```

### npm workspaces

Root `package.json` declares npm workspaces for `apps/*` and `packages/frontend-*` (R38). CI frontend matrix installs from root or builds packages before app `npm ci`.

### App responsibilities (unchanged scope)

| App | Keeps local |
|-----|-------------|
| chat-rag-frontend | `ChatPanel`, `CorpusBrowse` page shell (Tailwind layout), routing |
| data-management-frontend | `AdminLayout`, pages, shadcn `ui/*`, bulk dialogs |

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Single `frontend-shared` package (i18n + UI together) | Couples pure TS i18n to React/Tailwind; harder to test locale logic in isolation |
| i18n-only package (ADR-019 alone) | Leaves duplicated React components; styling drift between apps |
| Headless components + per-app CSS | More boilerplate; user asked for shared UI/UX, not just shared logic |
| Migrate ChatRAG fully to Tailwind in EV-004 | ~~Scope creep~~ **Selected in 01-requirements (RD-056)** — user chose full migration for consistent shared UI/UX |

## Consequences

- **Positive:** One implementation of language toggle, tag chips, and pagination; consistent bilingual UX across operator and public surfaces.
- **Positive:** Package-level Vitest tests for shared components.
- **Negative:** ChatRAG gains Tailwind as a dependency (dev/build tooling only for shared imports).
- **Negative:** CI must build/link workspace packages before frontend matrix jobs.
- **Negative:** shadcn minimal re-exports add Radix coupling to shared package (RD-060).
- **Negative:** Full ChatRAG Tailwind migration increases EV-004 scope vs minimal shared-import path.

## References

- ADR-012 (monorepo packages boundary)
- ADR-019 (shared frontend i18n)
- `docs/sessions/S000-internal-docs-archive/context-brief.md` §13, R34–R38
- [Repo: `apps/chat-rag-frontend/src/components/`]
- [Repo: `apps/data-management-frontend/src/components/`]

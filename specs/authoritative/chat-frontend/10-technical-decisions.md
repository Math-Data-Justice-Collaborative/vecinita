# chat-frontend — Technical Decisions

> Auto-generated: 2026-05-12

## Overview

Key architectural and technical decisions for the chat frontend, including both resolved decisions and pending choices.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | UI framework | React 18 + Vite 6 | Next.js, Remix, plain React + Webpack | 2026-05-12 | Moderate |
| TD-002 | Styling approach | Tailwind CSS 4 + Shadcn/ui | CSS Modules, styled-components, MUI-only | 2026-05-12 | Moderate |
| TD-003 | State management | React Context + custom hooks | Redux, Zustand, Jotai | 2026-05-12 | Easy |
| TD-004 | Streaming protocol | Server-Sent Events (EventSource) | WebSocket, HTTP long-polling | 2026-05-12 | Moderate |
| TD-005 | Conversation persistence | localStorage | IndexedDB, server-side storage | 2026-05-12 | Easy |
| TD-006 | Markdown rendering | react-markdown + remark-gfm | Custom parser, marked.js | 2026-05-12 | Easy |
| TD-007 | Auth strategy | Env-configured admin credentials | Supabase Auth, OAuth, JWT | 2026-05-12 | Easy |

### TD-001: UI Framework — React 18 + Vite 6

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Need a fast-building SPA framework for a chat interface |
| Decision | React 18 with Vite 6 for development and production builds |
| Rationale | Vite provides sub-second HMR and fast builds. React is the team's primary framework. No SSR needed for a chat SPA. |
| Alternatives considered | **Next.js** — SSR overhead unnecessary for a chat app. **Remix** — server-side focus doesn't fit client-heavy chat. |
| Consequences | No SSR/SSG capabilities; purely client-rendered |
| Reversibility | Moderate — component code is portable, but build config and routing differ |

### TD-003: State Management — React Context + Custom Hooks

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Need state management for auth, language, theme, chat, accessibility, and backend settings |
| Decision | Five React Contexts (Auth, Language, Accessibility, BackendSettings, ChatState) with custom hooks (useAgentChat, useConversationStorage) |
| Rationale | App state is naturally segmented. No global store needed. Context avoids external dependency. Custom hooks encapsulate complex logic (streaming, persistence). |
| Alternatives considered | **Redux** — overkill for the state complexity. **Zustand** — nice API but adds dependency for minimal gain. |
| Consequences | Context re-render performance is acceptable given the small component tree |
| Reversibility | Easy — contexts can be replaced with any state library without changing component interfaces |

### TD-004: Streaming Protocol — Server-Sent Events

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Need real-time streaming of agent responses to the browser |
| Decision | Use native `EventSource` API for SSE connections to `/ask/stream` |
| Rationale | SSE is simpler than WebSocket for unidirectional server-to-client streaming. No connection upgrade negotiation. Works through proxies and CDNs. Native browser API with no library dependency. |
| Alternatives considered | **WebSocket** — bidirectional capability not needed; more complex connection management. **HTTP long-polling** — higher latency, more requests. |
| Consequences | SSE is GET-only (question sent as query params). Reconnection handled manually. |
| Reversibility | Moderate — switching to WebSocket would require backend changes too |

### TD-005: Conversation Persistence — localStorage

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Need to persist conversation history across page reloads |
| Decision | Store message arrays and thread IDs in localStorage with cross-tab sync via `storage` events |
| Rationale | Simple, zero-infrastructure persistence. Sufficient for single-user chat. No backend storage needed. |
| Alternatives considered | **IndexedDB** — better for large data but overkill for text messages. **Server-side storage** — adds backend complexity and auth requirements. |
| Consequences | ~5MB storage limit per origin. Data lost on browser clear. No cross-device sync. |
| Reversibility | Easy — swap storage adapter without changing hook interfaces |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | MUI + Shadcn/ui coexistence | Consolidate to Shadcn/ui only, keep both | Bundle size, consistency | Medium — dual dependency inflates bundle | Consolidate to Shadcn/ui |

### PTD-001: MUI + Shadcn/ui Component Library Coexistence

| Property | Value |
|----------|-------|
| Status | Pending |
| Identified | 2026-05-12 |
| Evidence | `package.json` includes both `@mui/material` (7.3.5) and Shadcn/ui (`@radix-ui/*` primitives). Both are used in components. |
| Impact | Bundle size inflation (~200KB+ for MUI), inconsistent design language, two styling paradigms |
| Decision deadline | Before next major UI feature |

**Options researched:**

**Option A: Consolidate to Shadcn/ui only**
- How it works: Replace all MUI component usage with Shadcn/ui equivalents, remove `@mui/material`, `@emotion/react`, `@emotion/styled`
- Pros: Smaller bundle, consistent Tailwind styling, tree-shakeable
- Cons: Migration effort for existing MUI components
- Effort: M
- Reversibility: Moderate
- Ecosystem fit: Aligns with Tailwind-first approach

**Option B: Keep both libraries**
- How it works: Continue using MUI where already integrated, Shadcn/ui for new components
- Pros: No migration effort
- Cons: Larger bundle, inconsistent UX, two mental models
- Effort: S (no work needed)
- Reversibility: Easy
- Ecosystem fit: Creates friction as codebase grows

**Recommendation:** Option A — consolidate to Shadcn/ui. The project already uses Tailwind CSS throughout and Shadcn/ui for most new components.
**Risk of continued deferral:** Bundle size grows, styling inconsistencies accumulate, onboarding friction for contributors.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)

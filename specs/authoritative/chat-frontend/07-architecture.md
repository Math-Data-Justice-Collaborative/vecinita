# chat-frontend — Architecture

> Auto-generated: 2026-05-12

## Overview

Single-page application (SPA) built with React, TypeScript, and Vite. Uses a layered architecture with React Context for state management, custom hooks for business logic, and a service layer for API communication.

## Architecture Style

Client-side SPA with component-based UI, context-driven state, and a thin service layer.

## Component Map

| Component | Responsibility | Source Path |
|-----------|---------------|-------------|
| App | Root component, context providers, routing | `frontends/chat/src/app/App.tsx` |
| ChatPage | Main chat view — layout for chat widget | `frontends/chat/src/app/pages/ChatPage.tsx` |
| ChatWidget | Core chat UI — input, messages, streaming indicator | `frontends/chat/src/app/components/ChatWidget.tsx` |
| ChatMessage | Single message bubble with markdown and sources | `frontends/chat/src/app/components/ChatMessage.tsx` |
| SuggestionChips | Follow-up question chip buttons | `frontends/chat/src/app/components/SuggestionChips.tsx` |
| NavBar | Top navigation with theme toggle, language selector | `frontends/chat/src/app/components/NavBar.tsx` |
| AccessibilityPanel | Accessibility settings dialog | `frontends/chat/src/app/components/AccessibilityPanel.tsx` |
| KeyboardShortcutsHelp | Keyboard shortcuts reference dialog | `frontends/chat/src/app/components/KeyboardShortcutsHelp.tsx` |
| SkipToContent | Skip-to-main-content link for screen readers | `frontends/chat/src/app/components/SkipToContent.tsx` |
| DocumentsDashboard | Read-only corpus/documents view | `frontends/chat/src/app/pages/DocumentsDashboard.tsx` |
| LoginPage | Admin login form | `frontends/chat/src/app/pages/LoginPage.tsx` |
| AgentServiceClient | HTTP/SSE client for gateway API | `frontends/chat/src/app/services/agentService.ts` |
| useAgentChat | Core chat hook — message state, streaming, fallback | `frontends/chat/src/app/hooks/useAgentChat.ts` |
| useConversationStorage | localStorage persistence with cross-tab sync | `frontends/chat/src/app/hooks/useConversationStorage.ts` |
| AuthContext | Admin authentication state and login/logout | `frontends/chat/src/app/context/AuthContext.tsx` |
| LanguageContext | English/Spanish locale management | `frontends/chat/src/app/context/LanguageContext.tsx` |
| AccessibilityContext | Accessibility preferences state | `frontends/chat/src/app/context/AccessibilityContext.tsx` |
| BackendSettingsContext | Agent config (providers/models) from gateway | `frontends/chat/src/app/context/BackendSettingsContext.tsx` |
| ChatStateContext | Shared chat UI state across components | `frontends/chat/src/app/context/ChatStateContext.tsx` |
| UI primitives | Shadcn/ui components (button, card, dialog, etc.) | `frontends/chat/src/app/components/ui/` |

## Runtime Characteristics

| Property | Value |
|----------|-------|
| Language / runtime | TypeScript / Browser (ES2020+) |
| Framework | React 18 + Vite 6 |
| Entry point | `frontends/chat/src/main.tsx` |
| Port | 5173 (dev), 10000 (Render production via nginx) |
| Health check | `/health` (served by nginx or Vite dev server) |

## Concurrency Model

Single-threaded browser event loop. SSE connections are managed via the native `EventSource` API. Multiple concurrent streams are not expected — one active stream per chat session. Cross-tab synchronization uses the `storage` event listener on `window`.

## Diagrams

- [Architecture Diagram](diagrams/architecture.md)

## Related Documents

- [Behavior](01-behavior.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

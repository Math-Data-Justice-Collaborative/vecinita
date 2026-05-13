# chat-frontend — High-Level Behavior

> Auto-generated: 2026-05-12

## Purpose

The chat frontend is the end-user-facing React SPA that provides a RAG-powered civic information Q&A interface. Community members type questions about civic resources (food banks, legal aid, housing, etc.), and the app streams AI-generated answers with cited sources from the Vecinita agent through the gateway API.

## Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Chat interface | Render a conversational UI with message bubbles, streaming response indicators, and source citations |
| Streaming responses | Consume Server-Sent Events (SSE) from the gateway's `/ask/stream` endpoint, displaying tokens as they arrive |
| Conversation history | Persist conversation threads in localStorage with cross-tab synchronization |
| Multi-language support | Support English and Spanish UIs via `LanguageContext` with localized copy |
| Agent config discovery | Fetch available LLM providers and models from the gateway's `/ask/config` endpoint |
| Accessibility | Provide keyboard navigation, screen reader support, skip-to-content, and accessibility panel |
| Theme management | Support light/dark theme toggling persisted in localStorage |
| Documents browsing | Display a read-only documents dashboard for corpus inspection |
| Admin authentication | Optional admin login flow using env-configured credentials |

## Key Behaviors

### Ask a Question (Streaming)

- **Trigger:** User types a question and presses Enter or clicks Send
- **Process:** `useAgentChat` hook calls `agentService.askStream()` which opens an SSE connection to `GET /ask/stream?question=...`. Tokens, thinking events, tool events, sources, and clarification requests stream in real-time. A fallback to non-streaming `GET /ask` fires if the stream returns empty.
- **Outcome:** Assistant message rendered with markdown formatting, cited sources displayed as cards, and suggested follow-up questions shown as chips

### Load/Resume Conversation

- **Trigger:** Page load or tab switch
- **Process:** `useConversationStorage` reads the active thread ID and message history from localStorage. Cross-tab storage events sync state.
- **Outcome:** Previous conversation restored with full message history

### Start New Conversation

- **Trigger:** User clicks "New Chat"
- **Process:** Current thread deleted from storage, new UUID generated, messages cleared
- **Outcome:** Clean chat interface with splash suggestions

### Clarification Handling

- **Trigger:** Agent sends a `clarification` stream event
- **Process:** Clarification prompt and suggested questions displayed. User's response sent back with `clarification_response` parameter.
- **Outcome:** Agent continues processing with the additional context

## Boundaries

- Does NOT directly access the database (all data flows through the gateway API)
- Does NOT manage documents or corpus (handled by data-management-frontend)
- Does NOT run LLM inference (handled by agent service)
- Does NOT manage scraping jobs (handled by data-management-frontend → DM API)
- Does NOT handle user registration (admin-only auth via environment credentials)

## Related Documents

- [Architecture](07-architecture.md)
- [Integration Points](03-integration-points.md)
- [Architecture Diagram](diagrams/architecture.md)

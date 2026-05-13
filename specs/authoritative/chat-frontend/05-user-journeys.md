# chat-frontend — User Journeys

> Auto-generated: 2026-05-12

## Overview

Primary journeys center on asking civic questions and receiving streaming answers with source citations.

## Journeys

### Ask a Civic Question

**Persona:** Community Member
**Goal:** Find information about local civic resources

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Open chat at `/` | Splash screen with suggestion chips displayed | Suggestions localized to user's language |
| 2 | Type question or click suggestion chip | Input captured in chat widget | |
| 3 | Press Enter / click Send | User message bubble appears; streaming indicator starts | `useAgentChat.sendMessage()` called |
| 4 | Wait for streaming response | Thinking/tool events shown as progress; tokens stream into assistant bubble | SSE via `/ask/stream` |
| 5 | View completed response | Full markdown response with source cards and follow-up suggestions | |
| 6 | Click a source card | External link opens in new tab | |
| 7 | Click a suggested follow-up | New question sent with conversation context | thread_id maintained |

**Happy path outcome:** User receives a helpful, source-cited answer about civic resources.
**Failure modes:** Backend cold start timeout (15s first-event timeout), stream stall, gateway unreachable (fallback to non-streaming), empty response (default message shown).

### Switch Language

**Persona:** Community Member
**Goal:** Use the interface in Spanish

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Click language selector in NavBar | Language options displayed | |
| 2 | Select "Español" | UI labels and suggestions switch to Spanish | `LanguageContext` updates |
| 3 | Ask question in Spanish | `lang=es` parameter sent with request | |
| 4 | Receive Spanish response | Stream events localized via `agentChatStream.ts` translation map | |

**Happy path outcome:** Full Spanish experience from UI labels through agent responses.
**Failure modes:** Agent may respond in English if model lacks Spanish capability.

### Resume Previous Conversation

**Persona:** Community Member
**Goal:** Continue a previous chat session

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Return to chat page | Last active thread auto-loaded from localStorage | `getStoredActiveThreadId()` |
| 2 | View previous messages | Full conversation history rendered | Messages rehydrated from storage |
| 3 | Send new message | Continues conversation with existing thread_id | Context preserved |

**Happy path outcome:** Seamless conversation continuation across sessions.
**Failure modes:** localStorage cleared (conversation lost), thread_id expired on backend (new context started).

### Admin Login

**Persona:** Admin / Developer
**Goal:** Access admin-restricted routes

| Step | Action | System Response | Notes |
|------|--------|-----------------|-------|
| 1 | Navigate to `/admin` | Redirect to `/login?redirect=%2Fadmin` | `AdminRoute` guard |
| 2 | Enter admin email and password | Credentials validated against env vars | `VITE_DEV_ADMIN_EMAIL` / `VITE_DEV_ADMIN_PASSWORD` |
| 3 | Submit login form | Session stored in localStorage; redirect to `/admin` | |
| 4 | Access admin documents dashboard | Full dashboard displayed | Same as `/documents` but behind auth |

**Happy path outcome:** Admin authenticated and viewing documents dashboard.
**Failure modes:** Env credentials not configured (login disabled), invalid credentials (error shown).

## Diagrams

- [User Journey Diagram](diagrams/user-journeys.md)

## Related Documents

- [User Personas](04-user-personas.md)
- [Behavior](01-behavior.md)

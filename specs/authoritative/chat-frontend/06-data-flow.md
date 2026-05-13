# chat-frontend — Data Flow

> Auto-generated: 2026-05-12

## Overview

Data flows from user input through the gateway API and back as streamed responses. All persistence is client-side in localStorage.

## Inbound Data

| Source | Format | Trigger | Destination |
|--------|--------|---------|-------------|
| User keyboard input | Text string | Typing + Enter/Send | `useAgentChat.sendMessage()` |
| Gateway SSE stream | JSON events (text/event-stream) | After question sent | `AgentServiceClient.askStream()` |
| Gateway REST response | JSON (AgentResponse) | Fallback after stream failure | `AgentServiceClient.ask()` |
| Gateway config endpoint | JSON (AgentConfig) | App initialization | `BackendSettingsContext` |
| localStorage | JSON (Message[], thread IDs) | Page load | `useConversationStorage` |

## Internal Processing

| Stage | Input | Transformation | Output |
|-------|-------|----------------|--------|
| Question submission | Raw text | Add thread_id, lang, provider, model params | `AskQueryParams` |
| SSE event parsing | Raw SSE `data` field | `JSON.parse` into typed `StreamEvent` union | Typed stream events |
| Token accumulation | Individual token strings | Concatenate into `assistantContent` | Full response text |
| Markdown policy | Raw assistant text | `applyAssistantMarkdownPolicy()` — sanitize links, format | Safe markdown string |
| Message normalization | Raw agent payload | `extractAssistantTextFromPayload()` — extract text from nested structures | Clean text string |
| Localization | English stream messages | `localizeStreamMessage()` — translate thinking/tool labels to Spanish | Localized strings |
| Source mapping | `AgentSource[]` | Map to `{ title, url, snippet }` | `Message.sources` |

## Outbound Data

| Destination | Format | Trigger | Content |
|-------------|--------|---------|---------|
| Gateway `/ask/stream` | HTTP GET with query params | User sends message | Question, thread_id, lang, provider, model |
| Gateway `/ask` | HTTP GET with query params | Stream fallback | Same as above |
| localStorage | JSON | After each message exchange | Updated message array for thread |

## Data Persistence

| Store | Technology | What's Stored | Retention |
|-------|------------|---------------|-----------|
| Conversation threads | localStorage | Message history per thread_id | Until user clears browser data |
| Active thread pointer | localStorage | Currently active thread_id | Indefinite |
| Admin session | localStorage (`vecinita-admin-session`) | Email, token, timestamp | Until logout or clear |
| Theme preference | localStorage (`vecinita-theme`) | `'light'` or `'dark'` | Indefinite |

## Diagrams

- [Data Flow Diagram](diagrams/data-flow.md)

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)

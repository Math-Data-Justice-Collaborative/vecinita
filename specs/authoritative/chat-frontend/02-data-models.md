# chat-frontend — Data Models

> Auto-generated: 2026-05-12

## Overview

The chat frontend does not own a database. All persistent data lives in the browser's localStorage. The models below represent the TypeScript interfaces used for client-side state and API communication.

## Models

### Message

Client-side chat message stored in localStorage per thread.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string (UUID) | Required | Unique message identifier |
| role | `'user' \| 'assistant'` | Required | Message sender role |
| content | string | Required | Message text (markdown for assistant) |
| sources | `Source[]` | Optional | Cited sources for assistant messages |
| suggestedQuestions | `string[]` | Optional | Follow-up question suggestions |
| timestamp | Date | Required | Message creation time |

**Source:** `frontends/chat/src/app/hooks/useConversationStorage.ts`

### AgentResponse

Response shape from the gateway's `/ask` endpoint.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| answer | string | Required | Agent's text response |
| sources | `AgentSource[]` | Required | Cited document sources |
| thread_id | string | Optional | Conversation thread identifier |
| suggested_questions | `string[]` | Optional | Follow-up suggestions |
| language | string | Optional | Response language |
| model | string | Optional | Model used for generation |

**Source:** `frontends/chat/src/app/types/contracts/index.ts`

### AgentConfig

Provider/model configuration from the gateway's `/ask/config` endpoint.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| providers | `Provider[]` | Required | Available LLM providers |
| models | `Record<string, string[]>` | Required | Models per provider |
| defaultProvider | string | Optional | Default provider name |
| defaultModel | string | Optional | Default model name |

**Source:** `frontends/chat/src/app/types/contracts/index.ts`

### StreamEvent

Union type for SSE events from `/ask/stream`.

| Type | Key Fields | Description |
|------|------------|-------------|
| `thinking` | message, stage, progress | Agent processing status |
| `token` | content | Incremental response token |
| `source` | url, title, source_type | Discovered source citation |
| `tool_event` | tool, phase, message | Tool invocation status |
| `clarification` | message, questions | Agent requests user input |
| `complete` | answer, sources, thread_id | Final response |
| `error` | message, code | Error event |

**Source:** `frontends/chat/src/app/types/contracts/index.ts`

## Relationships

| From | To | Cardinality | Description |
|------|----|-------------|-------------|
| Thread | Message | 1:N | A conversation thread contains ordered messages |
| Message | Source | 1:N | Assistant messages may cite multiple sources |

## Diagrams

- [ER Diagram](diagrams/data-models.md)

## Related Documents

- [API Contract](08-api-contract.md)
- [Data Flow](06-data-flow.md)

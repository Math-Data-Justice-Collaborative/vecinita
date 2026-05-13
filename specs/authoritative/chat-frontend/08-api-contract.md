# chat-frontend — API Contract

> Auto-generated: 2026-05-12

## Overview

The chat frontend does not expose an API — it is a consumer of the gateway API. This document describes the gateway endpoints the frontend depends on.

## Base URL

| Environment | URL |
|-------------|-----|
| Local (Vite dev) | `http://localhost:5173` (app) → `/api` proxy → `http://localhost:8004` (gateway) |
| Render | `https://vecinita-frontend.onrender.com` → `VITE_GATEWAY_URL` (gateway) |

## Consumed Endpoints

### GET /ask/stream

Primary streaming Q&A endpoint.

| Property | Value |
|----------|-------|
| Auth | None (public) |
| Request | Query params: `question`, `thread_id`, `lang`, `provider`, `model`, `clarification_response`, `context_answer` |
| Response (2xx) | `text/event-stream` — SSE with JSON events (`thinking`, `token`, `source`, `tool_event`, `clarification`, `complete`, `error`) |
| Timeout | First event: 15s, Overall: 120s |

### GET /ask

Non-streaming Q&A fallback.

| Property | Value |
|----------|-------|
| Auth | None (public) |
| Request | Same query params as `/ask/stream` |
| Response (2xx) | JSON: `{ answer, sources, thread_id, suggested_questions, language, model }` |
| Timeout | 90s |

### GET /ask/config

Agent configuration discovery.

| Property | Value |
|----------|-------|
| Auth | None |
| Request | No parameters |
| Response (2xx) | JSON: `{ providers: [...], models: {...}, defaultProvider, defaultModel }` |
| Retry | 3 attempts, 800ms delay, multi-URL fallback |

### GET /health

Gateway health check.

| Property | Value |
|----------|-------|
| Auth | None |
| Response (2xx) | `200 OK` |

## Schemas

All types defined in `frontends/chat/src/app/types/contracts/index.ts`.

## Versioning

No formal API versioning. The frontend adapts to response shape variations via normalization functions (`normalizeAgentConfig`, `normalizeAskResponse`).

## Related Documents

- [Data Models](02-data-models.md)
- [Integration Points](03-integration-points.md)

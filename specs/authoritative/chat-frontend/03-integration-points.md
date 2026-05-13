# chat-frontend — Integration Points

> Auto-generated: 2026-05-12

## Overview

The chat frontend integrates exclusively with the Vecinita gateway API via HTTP REST and Server-Sent Events (SSE). All backend communication is routed through the gateway — the frontend never calls the agent service or database directly.

## Internal Integrations

| Target | Protocol | Direction | Purpose | Config |
|--------|----------|-----------|---------|--------|
| Gateway (`/ask`) | HTTP GET | Outbound | Non-streaming Q&A requests | `VITE_GATEWAY_URL` |
| Gateway (`/ask/stream`) | SSE (GET) | Outbound | Streaming Q&A responses | `VITE_GATEWAY_URL` |
| Gateway (`/ask/config`) | HTTP GET | Outbound | Fetch available providers/models | `VITE_GATEWAY_URL` |
| Gateway (`/health`) | HTTP GET | Outbound | Health check | `VITE_GATEWAY_URL` |
| Gateway (`/documents/*`) | HTTP GET | Outbound | Read-only corpus browsing | `VITE_GATEWAY_URL` |

## External Integrations

None. The chat frontend is a pure client-side SPA with no external API calls.

## Integration Details

### Gateway — Streaming Q&A (`/ask/stream`)

- **Endpoint/Function:** `GET /ask/stream?question=...&thread_id=...&lang=...&provider=...&model=...`
- **Request format:** Query parameters
- **Response format:** Server-Sent Events (SSE) with JSON payloads per event
- **Error handling:** First-event timeout (15s), overall stream timeout (120s), automatic fallback to non-streaming `/ask` on empty stream or stream error
- **Retry/timeout policy:** No automatic retry on SSE; fallback to REST on failure. Config endpoint retries 3 times with 800ms delay across multiple fallback URLs.

### Gateway — Agent Config (`/ask/config`)

- **Endpoint/Function:** `GET /ask/config` (gateway) or `GET /config` (direct agent)
- **Request format:** No parameters
- **Response format:** JSON with `providers` and `models` arrays
- **Error handling:** Multi-URL fallback chain with 3 retry attempts per URL
- **Retry/timeout policy:** 800ms between retries, tries `/ask/config`, `/config`, and origin-relative paths

### URL Resolution

The `AgentServiceClient` resolves the gateway URL with sophisticated fallback logic in `agentApiResolution.ts`:
1. Uses `VITE_GATEWAY_URL` (primary)
2. Falls back to `VITE_BACKEND_URL`
3. In dev mode, uses `/api` (Vite proxy)
4. Detects direct Render agent hosts and adjusts path prefixes accordingly

**Source:** `frontends/chat/src/app/lib/agentApiResolution.ts`

## Diagrams

- [Integration Diagram](diagrams/integration-points.md)
- [Sequence Flows](diagrams/sequence-flows.md)

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)

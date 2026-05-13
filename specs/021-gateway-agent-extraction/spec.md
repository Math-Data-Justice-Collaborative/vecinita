# Feature Specification: Gateway / Agent extraction

**Spec ID**: 021  
**Feature Branch**: `021-gateway-agent-extraction`  
**Created**: 2026-05-13  
**Status**: Draft  
**Phase**: 2 (Restructure Gateway + Extract Agent) — per `specs/monorepo-decomposition/09-migration-sequence.md`  
**Blocks**: Spec 022 (vLLM/LlamaIndex integration targets the extracted agent)  
**Dependencies**: Spec 020 (monorepo layout must be in place)  
**Risk**: High — gateway is deeply entangled, many internal imports  
**Effort**: L (4–5 days)

## Overview

Separate the agent (RAG/LLM logic) from the gateway monolith. Today the gateway contains agent code under `src/agent/` and `src/services/agent/`, plus shared services for LLM routing (`src/services/llm/`), corpus retrieval (`src/services/corpus/`), and guardrails. The agent Dockerfile currently uses an "overlay" pattern: it copies all of `apis/gateway/src` then replaces `src/agent/` with agent-specific code.

After this spec:
- **Gateway** (`apps/gateway/`) is the HTTP orchestrator: routing, auth, CORS, rate limiting, job orchestration (Modal triggers for scraper/embedding/indexing), data CRUD, WebSocket streaming, and OpenAPI aggregation.
- **Agent** (`apps/agent/`) is the RAG brain: LlamaIndex pipeline, conversation management, tool calling, vector search (pgvector), LLM provider routing, response generation, and guardrails.
- **Shared code** lives in `packages/db/` (DB models, migrations), `packages/config/` (config loading), and `packages/common/` (types, errors).
- Gateway calls agent over HTTP via a defined contract.

### Code Currently in Gateway That Moves to Agent

| Source (in `apis/gateway/`) | Destination (in `apps/agent/`) | Content |
|----------------------------|-------------------------------|---------|
| `src/agent/` | `src/agent/` | Core agent logic, conversation handling |
| `src/services/agent/` | `src/services/agent/` | Agent-domain service layer |
| `src/services/llm/` | `src/services/llm/` | LLM provider routing, prompt templates |
| `src/services/corpus/` | `src/services/corpus/` | Corpus retrieval for RAG context |
| Guardrails config files | `config/guardrails/` | Safety filters, content policy |

### Code That Stays in Gateway

| Path | Content |
|------|---------|
| `src/api/` | FastAPI route handlers, request/response models |
| `src/middleware/` | Auth, CORS, rate limiting, logging |
| `src/services/modal/` | Modal SDK integration for job triggers |
| `src/services/scraper/` | Scraper orchestration |
| `src/services/ingestion/` | Document ingestion pipeline triggers |
| `src/services/db/` | Database service layer (CRUD operations) |
| `src/config/` | Gateway-specific config (moves shared parts to `packages/config/`) |

### HTTP Contract

| Endpoint | Method | Purpose | Request | Response |
|----------|--------|---------|---------|----------|
| `/agent/query` | POST | Synchronous RAG query | `{ "query": str, "conversation_id": str?, "context": dict? }` | `{ "response": str, "sources": list, "conversation_id": str }` |
| `/agent/stream` | POST | Streaming RAG query (SSE) | `{ "query": str, "conversation_id": str?, "context": dict? }` | SSE stream of `{ "token": str, "done": bool, "sources": list? }` |
| `/agent/health` | GET | Health check | — | `{ "status": "healthy", "version": str }` |

## User Scenarios & Testing

### User Story 1 — Independent gateway operation (Priority: P1)

**US-001**: As a developer, I can start the gateway service independently and it handles HTTP routing, auth, and job orchestration without requiring the agent codebase to be co-located, so that the gateway is a focused HTTP orchestrator.

**Why this priority**: The gateway's tight coupling to agent code is the primary architectural debt. Decoupling is required before any agent-side changes (LlamaIndex, vLLM) can proceed safely.

**Independent Test**: Start `apps/gateway/` in isolation — it boots, responds to `/health`, and serves non-agent routes (data CRUD, job management) without importing any agent module.

**Acceptance Scenarios**:

1. **Given** the gateway service at `apps/gateway/`, **When** it starts with valid environment config, **Then** it boots without importing modules from `apps/agent/` and responds `200` on `GET /health`.
2. **Given** the gateway is running without agent available, **When** a client calls a data CRUD endpoint, **Then** the gateway handles the request normally (the agent being down does not block non-agent routes).
3. **Given** the gateway is running without agent available, **When** a client calls an agent-proxied endpoint, **Then** the gateway returns a clear `503 Service Unavailable` with a structured error message — not a crash or import error.

---

### User Story 2 — Independent agent operation (Priority: P1)

**US-002**: As a developer, I can start the agent service independently and it runs the RAG pipeline, so that agent development is decoupled from gateway changes.

**Why this priority**: Agent must be independently deployable for spec 022 (vLLM/LlamaIndex integration) to proceed without gateway risk.

**Independent Test**: Start `apps/agent/` in isolation — it boots, responds to `/agent/health`, and can process a query against its own endpoints.

**Acceptance Scenarios**:

1. **Given** the agent service at `apps/agent/`, **When** it starts with valid environment config and database access, **Then** it boots and responds `200` on `GET /agent/health`.
2. **Given** the agent is running, **When** a client POSTs to `/agent/query` with a valid query, **Then** the agent processes it through the RAG pipeline and returns a structured response.
3. **Given** the agent is running, **When** a client POSTs to `/agent/stream` with a valid query, **Then** the agent returns an SSE stream of tokens.

---

### User Story 3 — Gateway-to-agent HTTP integration (Priority: P1)

**US-003**: As the gateway, I call the agent over HTTP for RAG queries, so that the two services communicate via a defined contract rather than in-process imports.

**Why this priority**: The HTTP contract is the boundary that makes independent deployment possible. It replaces the current in-process function calls.

**Independent Test**: With both services running, a chat query through the gateway proxies to the agent and returns a complete response with sources.

**Acceptance Scenarios**:

1. **Given** both gateway and agent are running, **When** a chat-frontend client sends a query through the gateway's chat endpoint, **Then** the gateway forwards to `POST /agent/query`, receives the agent's response, and returns it to the client.
2. **Given** both services are running, **When** a streaming chat request arrives, **Then** the gateway forwards to `POST /agent/stream` and proxies the SSE stream back to the client.
3. **Given** the agent is unreachable, **When** a chat query arrives at the gateway, **Then** the gateway returns `503` with `{ "error": "agent_unavailable", "message": "..." }` — not a raw connection error.

---

### User Story 4 — Shared packages work across services (Priority: P2)

**US-004**: As a developer, I can use shared DB models, config, and types from `packages/` in both gateway and agent, so that common code is not duplicated.

**Why this priority**: Without shared packages, the extraction would require duplicating DB models and config loaders, creating maintenance debt.

**Independent Test**: Both gateway and agent import from `packages.db.models` and get the same model classes. A schema migration in `packages/db/migrations/` applies to both.

**Acceptance Scenarios**:

1. **Given** `packages/db/` contains shared DB models, **When** both gateway and agent import `from packages.db.models import Document`, **Then** both get the same model class backed by the same database table.
2. **Given** `packages/config/` contains config loading, **When** both services use `from packages.config import load_config`, **Then** each loads its own `.env` file but uses the same parsing logic.
3. **Given** a new migration is added to `packages/db/migrations/`, **When** the migration runs, **Then** schema changes are visible to both gateway and agent.

---

### Edge Cases

- Gateway agent-proxy timeout must be configurable and defaults to a value that accommodates LLM inference latency (30s minimum for synchronous, unlimited for streaming).
- Agent must handle concurrent requests — multiple gateway instances may call it simultaneously.
- Circular import detection: ensure no module in `apps/gateway/` imports from `apps/agent/` or vice versa (only from `packages/`).
- Database connection pooling: both services connect to the same PostgreSQL instance but should use separate connection pools.
- The agent's overlay Dockerfile pattern must be replaced with a standalone Dockerfile that only copies agent code + shared packages.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST extract agent core logic from `apis/gateway/src/agent/` to `apps/agent/src/`, preserving all agent functionality (conversation handling, tool calling, response generation).
- **FR-002**: The system MUST extract agent-domain services from `apis/gateway/src/services/agent/` to `apps/agent/src/services/agent/`, preserving the agent service layer.
- **FR-003**: The system MUST extract LLM routing logic from `apis/gateway/src/services/llm/` to `apps/agent/src/services/llm/`, so the agent owns LLM provider selection and prompt management.
- **FR-004**: The system MUST extract corpus retrieval logic from `apis/gateway/src/services/corpus/` to `apps/agent/src/services/corpus/`, so the agent owns RAG context retrieval.
- **FR-005**: The system MUST move guardrails configuration to `apps/agent/config/guardrails/`, so the agent owns safety filtering.
- **FR-006**: The gateway MUST retain: `src/api/` (route handlers), `src/middleware/` (auth, CORS, rate limiting), `src/services/modal/` (Modal SDK), `src/services/scraper/`, `src/services/ingestion/`, `src/services/db/` (data CRUD), and gateway-specific config. No agent logic may remain in the gateway.
- **FR-007**: The gateway MUST call the agent via HTTP: `POST /agent/query` for synchronous queries and `POST /agent/stream` for streaming queries. The request/response schemas MUST be documented in both services.
- **FR-008**: The agent MUST expose `GET /agent/health` returning `{ "status": "healthy", "version": str }` with a `200` status code when operational.
- **FR-009**: The system MUST extract shared database models (used by both gateway and agent) to `packages/db/`, with a `pyproject.toml` that both services declare as a dependency.
- **FR-010**: The system MUST extract shared configuration loading logic to `packages/config/`, with env var parsing and validation utilities.
- **FR-011**: Both Dockerfiles (`apps/gateway/Dockerfile`, `apps/agent/Dockerfile`) MUST use root `.` as dockerContext so that `COPY packages/ ./packages/` works. The agent's overlay pattern MUST be eliminated.
- **FR-012**: Both services MUST independently start, pass health checks, and handle requests without the other service's source code being present in their build context (shared packages excepted).

### Key Entities

- **Gateway service**: HTTP entry point — owns routing, auth, orchestration, and data CRUD.
- **Agent service**: RAG brain — owns LlamaIndex pipeline, conversation, vector search, LLM routing.
- **Agent HTTP contract**: The `POST /agent/query`, `POST /agent/stream`, and `GET /agent/health` endpoints that define the gateway→agent boundary.
- **Shared packages**: `packages/db/`, `packages/config/`, `packages/common/` — code imported by both services.
- **Overlay pattern**: The current agent Dockerfile strategy of copying all gateway code then overwriting `src/agent/`. This pattern is eliminated by this spec.

## Acceptance Scenarios

- **AS-001**: **Given** the extraction is complete, **When** `ls apps/gateway/src/` is run, **Then** no `agent/` directory exists, and no file imports from an agent-specific module.
- **AS-002**: **Given** the extraction is complete, **When** `ls apps/agent/src/` is run, **Then** agent core logic, services (agent, llm, corpus), and guardrails config are present.
- **AS-003**: **Given** the extraction is complete, **When** `grep -r "from.*apps.gateway" apps/agent/` is run, **Then** zero matches are found (no cross-app imports).
- **AS-004**: **Given** the extraction is complete, **When** `grep -r "from.*apps.agent" apps/gateway/` is run, **Then** zero matches are found (no cross-app imports).
- **AS-005**: **Given** gateway is running, **When** `curl http://localhost:8000/health` is called, **Then** a `200` response is returned.
- **AS-006**: **Given** agent is running, **When** `curl http://localhost:8001/agent/health` is called, **Then** `{ "status": "healthy", "version": "..." }` is returned with status `200`.
- **AS-007**: **Given** both services are running, **When** a query is sent to gateway's chat endpoint, **Then** the gateway proxies to agent, and the end-to-end response includes RAG sources.
- **AS-008**: **Given** agent is down, **When** a chat query hits gateway, **Then** gateway returns `503` with a structured error — not a stack trace.
- **AS-009**: **Given** `packages/db/models/` contains shared models, **When** both services start, **Then** both can query the same database tables without import errors.
- **AS-010**: **Given** the agent Dockerfile at `apps/agent/Dockerfile`, **When** `docker build -f apps/agent/Dockerfile .` is run from root, **Then** the build succeeds without referencing `apis/gateway/`.

## Success Criteria

- **SC-001**: Gateway starts and passes health check (`GET /health → 200`) without any agent code in its source tree. Verified by booting gateway in isolation.
- **SC-002**: Agent starts and passes health check (`GET /agent/health → 200`) without any gateway code in its source tree. Verified by booting agent in isolation.
- **SC-003**: End-to-end query flow works: client → gateway → agent → response. Verified by sending a test query through the gateway and receiving a RAG-generated response with sources.
- **SC-004**: Zero cross-app imports exist between `apps/gateway/` and `apps/agent/`. Verified by `grep -r` for cross-references returning no matches.
- **SC-005**: Both Dockerfiles build successfully from the monorepo root with `dockerContext: .`. Verified by running `docker build` for each.
- **SC-006**: Shared packages (`packages/db/`, `packages/config/`, `packages/common/`) are importable by both services. Verified by import checks during service startup.
- **SC-007**: The agent's overlay Dockerfile pattern is eliminated. The agent Dockerfile does not reference `apis/gateway/` in any `COPY` or build instruction.
- **SC-008**: Gateway returns structured `503` errors when the agent is unreachable, not raw connection errors or stack traces.

## Assumptions

- Spec 020 (monorepo layout) is complete — `apps/` and `packages/` directories exist.
- The current agent overlay pattern in the Dockerfile is the only mechanism sharing code between gateway and agent; no runtime file-system sharing occurs.
- The gateway→agent HTTP contract uses internal networking (Render internal service URLs or `localhost` in local dev). No public internet routing is needed.
- Database connection strings are configured independently per service via `.environments/gateway.env` and `.environments/agent.env`.
- The schema-per-service migration (Phase 4) happens after this spec. During this phase, both services use the same default schema with separate connection pools.
- LLM provider routing code moves to agent but is not rewritten — that happens in spec 022.

## Technical References

- `specs/monorepo-decomposition/08-recommended-boundaries.md` — service boundary definitions (Gateway vs Agent ownership tables)
- `specs/monorepo-decomposition/09-migration-sequence.md` — Phase 2 details
- `specs/monorepo-decomposition/02-app-inventory.md` — agent inventory and overlay pattern note
- `specs/monorepo-decomposition/11-infrastructure-impact.md` — Dockerfile context changes
- `specs/.technical-decisions-log.json` — TD-001 (layout), TD-002 (schema-per-service), TD-006 (drop OpenAPI clients)
- `specs/020-flatten-submodules-monorepo-layout/spec.md` — prerequisite spec

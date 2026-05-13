# Vecinita Agent — Service Documentation

> Auto-generated: 2026-05-12

Comprehensive documentation for the Vecinita Agent service — the RAG "brain" of the
civic information system. The agent handles natural-language questions about community
resources by retrieving relevant documents from pgvector, augmenting prompts with
context, and generating bilingual (en/es) answers via LLM.

**Current code:** `apis/agent/src/agent/` + `apis/gateway/src/services/agent/`
**Target path:** `apps/agent/`

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | High-level service behavior, responsibilities, and boundaries |
| 02 | [Data Models](02-data-models.md) | Database tables, Pydantic schemas, and relationships |
| 03 | [Integration Points](03-integration-points.md) | Internal and external service integrations with error handling |
| 04 | [User Personas](04-user-personas.md) | Actors and roles interacting with the service |
| 05 | [User Journeys](05-user-journeys.md) | End-to-end user journey narratives |
| 06 | [Data Flow](06-data-flow.md) | Data ingress, RAG pipeline processing, and egress |
| 07 | [Architecture](07-architecture.md) | Layered architecture, component map, concurrency model |
| 08 | [API Contract](08-api-contract.md) | All endpoints, query parameters, schemas, SSE events |
| 09 | [Dependencies](09-dependencies.md) | Internal monorepo, external runtime, and infrastructure deps |
| 10 | [Technical Decisions](10-technical-decisions.md) | 7 decided ADRs + 4 pending decisions with recommendations |
| 11 | [Testing Plan](11-testing-plan.md) | Test layers, key scenarios, coverage gaps |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Docker build, Render deployment, scaling, observability |
| 13 | [Modal Integration](13-modal-integration-plan.md) | Modal LLM and embedding service consumption |
| 14 | [Render Integration](14-render-integration-plan.md) | Render service config, 40+ env vars, database bindings |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | System context and internal component diagrams |
| [Data Flow](diagrams/data-flow.md) | RAG pipeline, streaming, and embedding cache flows |
| [Data Models](diagrams/data-models.md) | Entity-relationship diagram for document_chunks |
| [Integration Points](diagrams/integration-points.md) | Service connectivity and auth flow |
| [User Personas](diagrams/user-personas.md) | Actor-to-touchpoint mapping |
| [User Journeys](diagrams/user-journeys.md) | Journey maps for community, streaming, and diagnostics |
| [Sequence Flows](diagrams/sequence-flows.md) | 5 sequence diagrams: answer-seeking, streaming, guardrails, rate-limit, model selection |

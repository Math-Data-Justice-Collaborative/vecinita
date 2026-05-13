# Data Management API — Service Documentation

> Auto-generated: 2026-05-12

Comprehensive documentation for the **data-management API** service — an
operator-facing FastAPI proxy that brokers communication between the
data-management SPA and the scraper, embedding, and model backend services.

**Current code:** `apis/data-management-api/` (git submodule)
**Target path:** `apps/data-management-api/`
**Render service:** `vecinita-data-management-api-v1`

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | High-level service behavior, responsibilities, and boundaries |
| 02 | [Data Models](02-data-models.md) | API-layer Pydantic schemas and scraper pipeline Postgres tables |
| 03 | [Integration Points](03-integration-points.md) | Internal/external integrations, error handling, and timeouts |
| 04 | [User Personas](04-user-personas.md) | Actors and roles interacting with the service |
| 05 | [User Journeys](05-user-journeys.md) | End-to-end operator and system journeys |
| 06 | [Data Flow](06-data-flow.md) | Data ingress, processing, and egress patterns |
| 07 | [Architecture](07-architecture.md) | Thin proxy / BFF architecture, component map, runtime characteristics |
| 08 | [API Contract](08-api-contract.md) | All endpoints with schemas, auth, and error responses |
| 09 | [Dependencies](09-dependencies.md) | Internal packages, external libraries, infrastructure, and service deps |
| 10 | [Technical Decisions](10-technical-decisions.md) | 5 decided ADRs + 3 pending decisions with researched options |
| 11 | [Testing Plan](11-testing-plan.md) | Test layers, scenarios, Pact contracts, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Build, deploy, scaling, observability, and CI/CD |
| 13 | [Modal Integration](13-modal-integration-plan.md) | Modal app invocation patterns, routing logic, env vars |
| 14 | [Render Integration](14-render-integration-plan.md) | Render service config, env vars, database bindings |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | System context and component view |
| [Data Flow](diagrams/data-flow.md) | Job proxy, embed, predict, and health data flows |
| [Data Models](diagrams/data-models.md) | Scraper pipeline ER diagram and Pydantic class diagram |
| [Integration Points](diagrams/integration-points.md) | Service connectivity, auth flow, Modal routing decision |
| [User Personas](diagrams/user-personas.md) | Actor-to-touchpoint mapping |
| [User Journeys](diagrams/user-journeys.md) | Job submission, monitoring, and embedding journeys |
| [Sequence Flows](diagrams/sequence-flows.md) | Request/response sequences for all major flows |

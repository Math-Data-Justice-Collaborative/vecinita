# Gateway Service Documentation
> Auto-generated: 2026-05-12

Comprehensive documentation for the Vecinita **gateway** service — the unified HTTP entry point for the civic/community information RAG system.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | Core responsibilities, key behaviors, and service boundaries |
| 02 | [Data Models](02-data-models.md) | Database schemas, Pydantic models, and entity relationships |
| 03 | [Integration Points](03-integration-points.md) | Upstream/downstream services, protocols, and error handling |
| 04 | [User Personas](04-user-personas.md) | Actors and roles that interact with the gateway |
| 05 | [User Journeys](05-user-journeys.md) | Step-by-step flows for each persona |
| 06 | [Data Flow](06-data-flow.md) | How data enters, transforms, and exits the service |
| 07 | [Architecture](07-architecture.md) | Internal components, middleware stack, and concurrency model |
| 08 | [API Contract](08-api-contract.md) | Complete endpoint reference with request/response shapes |
| 09 | [Dependencies](09-dependencies.md) | Runtime, dev, and infrastructure dependencies |
| 10 | [Technical Decisions](10-technical-decisions.md) | ADRs (decided) and pending decisions |
| 11 | [Testing Plan](11-testing-plan.md) | Testing layers, tools, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Dockerfile, scaling, and observability |
| 13 | [Modal Integration Plan](13-modal-integration-plan.md) | Modal SDK function invocation patterns |
| 14 | [Render Integration Plan](14-render-integration-plan.md) | Render deployment configuration |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | Component and deployment diagram |
| [Data Flow](diagrams/data-flow.md) | Request/response and data pipeline flows |
| [Data Models](diagrams/data-models.md) | ER diagram of gateway-owned tables |
| [Integration Points](diagrams/integration-points.md) | Service connectivity graph |
| [User Personas](diagrams/user-personas.md) | Actor relationship diagram |
| [User Journeys](diagrams/user-journeys.md) | Journey maps per persona |
| [Sequence Flows](diagrams/sequence-flows.md) | Key request sequence diagrams |

## Source Code

| Item | Path |
|------|------|
| Application entry | `apis/gateway/src/api/main.py` |
| Configuration | `apis/gateway/src/config.py` |
| Middleware | `apis/gateway/src/api/middleware.py` |
| Routers | `apis/gateway/src/api/router_*.py` |
| Services | `apis/gateway/src/services/` |
| Dockerfile | `apis/gateway/Dockerfile.gateway` |
| Dependencies | `apis/gateway/pyproject.toml` |
| Target path | `apps/gateway/` (post-refactor) |

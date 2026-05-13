# vLLM Inference — Service Documentation
> Auto-generated: 2026-05-12

Comprehensive documentation for the Vecinita **vllm-inference** service — the serverless LLM inference engine powering the civic information RAG system.

## Documents

| # | Document | Description |
|---|----------|-------------|
| 01 | [Behavior](01-behavior.md) | Core responsibilities, key behaviors, and service boundaries |
| 02 | [Data Models](02-data-models.md) | Request/response schemas and model registry |
| 03 | [Integration Points](03-integration-points.md) | Upstream/downstream services, protocols, and error handling |
| 04 | [User Personas](04-user-personas.md) | Actors and roles that interact with the service |
| 05 | [User Journeys](05-user-journeys.md) | Step-by-step flows for each persona |
| 06 | [Data Flow](06-data-flow.md) | How data enters, transforms, and exits the service |
| 07 | [Architecture](07-architecture.md) | Internal components, runtime model, and design philosophy |
| 08 | [API Contract](08-api-contract.md) | OpenAI-compatible endpoint reference with request/response shapes |
| 09 | [Dependencies](09-dependencies.md) | Runtime, dev, and infrastructure dependencies |
| 10 | [Technical Decisions](10-technical-decisions.md) | ADRs (decided) and pending decisions |
| 11 | [Testing Plan](11-testing-plan.md) | Testing layers, tools, and CI integration |
| 12 | [Infrastructure Plan](12-infrastructure-plan.md) | Build, deploy, scaling, observability |
| 13 | [Modal Integration Plan](13-modal-integration-plan.md) | Modal app config, GPU selection, model loading |
| 14 | [Render Integration Plan](14-render-integration-plan.md) | N/A — this service runs on Modal |

## Diagrams

| Diagram | Description |
|---------|-------------|
| [Architecture](diagrams/architecture.md) | Component and deployment diagram |
| [Data Flow](diagrams/data-flow.md) | Request/response and inference pipeline flows |
| [Data Models](diagrams/data-models.md) | Schema relationship diagram |
| [Integration Points](diagrams/integration-points.md) | Service connectivity graph |
| [User Personas](diagrams/user-personas.md) | Actor relationship diagram |
| [User Journeys](diagrams/user-journeys.md) | Journey maps per persona |
| [Sequence Flows](diagrams/sequence-flows.md) | Key request sequence diagrams |

## Source Code

| Item | Path |
|------|------|
| Current implementation | `modal-apps/model-modal/` |
| Target path (rewrite) | `apps/vllm-inference/` |
| Modal app entry | `apps/vllm-inference/app.py` |
| Configuration | `apps/vllm-inference/config.py` |
| Dependencies | `apps/vllm-inference/pyproject.toml` |

## Context

This service is a **rewrite** of the existing `modal-apps/model-modal/` Ollama-based inference service. The rewrite replaces Ollama with [vLLM](https://docs.vllm.ai/) to gain native OpenAI-compatible API support, GPU-optimized inference via PagedAttention, and direct compatibility with LlamaIndex's `llama-index-llms-vllm` client used by the agent service.

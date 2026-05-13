# User Personas: vLLM Inference
> Auto-generated: 2026-05-12

## Overview

The vllm-inference service is a backend inference engine with no direct end-user interaction. Its "users" are other services (automated systems), operators deploying and maintaining the service, and developers working on the Vecinita platform.

## Personas

### Agent Service (Automated System)

| Attribute | Value |
|-----------|-------|
| Role | Primary consumer of LLM inference |
| Interaction mode | Automated — OpenAI-compatible REST API via LlamaIndex |
| Goals | Get accurate, low-latency chat completions for RAG responses |
| Pain points | Cold start latency on first request; GPU availability during peak load |

### Gateway Service (Automated System)

| Attribute | Value |
|-----------|-------|
| Role | Secondary consumer via Modal SDK function invocation |
| Interaction mode | Automated — Modal `Function.from_name().remote()` |
| Goals | Proxy chat completion requests from frontends; health monitoring |
| Pain points | Function lookup failures when Modal tokens misconfigured |

### Platform Operator

| Attribute | Value |
|-----------|-------|
| Role | Deploys, monitors, and maintains the inference service |
| Interaction mode | CLI (`modal deploy`, `modal run`), Modal dashboard, CI/CD |
| Goals | Keep the service running with acceptable latency and cost; swap models when needed |
| Pain points | GPU cost management; model weight download time; cold start optimization |

### Platform Developer

| Attribute | Value |
|-----------|-------|
| Role | Develops and tests the inference service |
| Interaction mode | Local development, unit tests, CI |
| Goals | Iterate on model configuration, API behavior, and lifecycle logic |
| Pain points | Cannot run vLLM locally without GPU; testing requires mocks |

## Actor-System Map

| Persona | Touchpoint | Access Level |
|---------|------------|--------------|
| Agent Service | `/v1/chat/completions`, `/v1/models` | read (inference) |
| Gateway Service | Modal SDK function, `/health` | read (inference + monitoring) |
| Platform Operator | `modal deploy`, `modal run`, Modal dashboard, `/health` | admin |
| Platform Developer | `pytest`, `modal serve`, Docker Compose | admin (dev) |

## Diagrams

- [User Personas Diagram](diagrams/user-personas.md)

## Related Documents

- [User Journeys](05-user-journeys.md)
- [Behavior](01-behavior.md)

# Monorepo Decomposition Analysis

> Auto-generated: 2026-05-12

Analysis of the Vecinita monorepo structure, with recommendations for converting
from git-submodule-based layout to a true `apps/` + `packages/` monorepo with
clear service boundaries, vLLM + LlamaIndex integration, and unified Render
deployment.

## Contents

| Document | Description |
|----------|-------------|
| [01-executive-summary.md](./01-executive-summary.md) | High-level findings and recommendation |
| [02-app-inventory.md](./02-app-inventory.md) | Every app/service, purpose, runtime |
| [03-service-profiles.md](./03-service-profiles.md) | Deep profile per service |
| [04-dependency-graph.md](./04-dependency-graph.md) | Inter-service and shared-code dependencies |
| [05-data-ownership.md](./05-data-ownership.md) | Data stores, schema-per-service plan |
| [06-coupling-analysis.md](./06-coupling-analysis.md) | Coupling metrics and hotspots |
| [07-decomposition-candidates.md](./07-decomposition-candidates.md) | Extraction candidates with technical decisions |
| [08-recommended-boundaries.md](./08-recommended-boundaries.md) | Proposed service boundaries post-restructure |
| [09-migration-sequence.md](./09-migration-sequence.md) | Ordered restructuring plan |
| [10-shared-code-strategy.md](./10-shared-code-strategy.md) | packages/ structure and shared library plan |
| [11-infrastructure-impact.md](./11-infrastructure-impact.md) | CI, deploy, infra changes |
| [12-risks-and-trade-offs.md](./12-risks-and-trade-offs.md) | Risks, mitigations, deferred decisions |
| [diagrams/](./diagrams/) | Mermaid architecture diagrams |

## Context

- **Team**: Solo developer
- **Approach**: Full rewrite permitted
- **Priority**: Monorepo layout restructure first
- **Target stack**: vLLM (Modal GPU) + LlamaIndex (RAG) + Render (services) + PostgreSQL (schema-per-service)

# Vecinita Agent — User Personas Diagram

> Auto-generated: 2026-05-12

```mermaid
graph TB
    subgraph Personas
        Community[Community Member<br>en/es bilingual]
        Operator[Operator / Developer]
        Pipeline[Data Pipeline<br>vector_loader]
    end

    subgraph Service Touchpoints
        ChatUI[Chat Frontend]
        GatewayAPI[Gateway REST API]
        AgentAPI[Agent REST API<br>/ask, /ask-stream]
        DiagAPI[Diagnostic API<br>/test-db-search, /db-info]
        ConfigAPI[Config API<br>/config, /model-selection]
        SwaggerUI[Swagger UI<br>/docs]
        PgDirect[PostgreSQL Direct<br>document_chunks]
    end

    Community -->|types question| ChatUI
    ChatUI -->|HTTP| GatewayAPI
    GatewayAPI -->|proxies| AgentAPI

    Operator -->|diagnose| DiagAPI
    Operator -->|configure| ConfigAPI
    Operator -->|explore| SwaggerUI

    Pipeline -->|INSERT/UPSERT| PgDirect
```

# vLLM Inference — User Personas Diagram
> Auto-generated: 2026-05-12

```mermaid
graph TB
    subgraph Automated Systems
        AG[Agent Service<br/>Primary Consumer]
        GW[Gateway Service<br/>Secondary Consumer]
    end

    subgraph Human Operators
        OP[Platform Operator<br/>Deploy + Monitor]
        DEV[Platform Developer<br/>Develop + Test]
    end

    subgraph Service Touchpoints
        API[OpenAI REST API<br/>/v1/chat/completions]
        SDK[Modal SDK<br/>Function.from_name]
        CLI[Modal CLI<br/>deploy / run / serve]
        HEALTH[Health Endpoint<br/>GET /health]
        DASH[Modal Dashboard<br/>Metrics + Logs]
    end

    AG -->|calls| API
    GW -->|calls| SDK
    GW -->|monitors| HEALTH
    OP -->|deploys via| CLI
    OP -->|monitors| DASH
    OP -->|checks| HEALTH
    DEV -->|develops via| CLI
    DEV -->|tests via| API
```

# User Personas Diagram: Gateway
> Auto-generated: 2026-05-12

## Actor Relationship Diagram

```mermaid
graph TD
    subgraph "Human Actors"
        CM[Community Member<br/>Ask questions, browse docs]
        DM[Data Manager<br/>Scrape, embed, reindex]
        PO[Platform Operator<br/>Monitor health, deploy]
    end

    subgraph "System Actors"
        CF[Chat Frontend<br/>React SPA]
        DMF[Data Mgmt Frontend<br/>React SPA]
        AG[Agent Service<br/>LangGraph]
        MW[Modal Workers<br/>Scraper, Embedding]
    end

    GW[Gateway<br/>API Entry Point]

    CM --> CF
    DM --> DMF
    PO --> GW

    CF --> GW
    DMF --> GW
    GW --> AG
    GW -->|Modal SDK| MW
    MW -->|HTTP callback| GW
```

## Persona → Endpoint Mapping

```mermaid
graph LR
    subgraph "Community Member"
        E1[/ask]
        E2[/ask/stream]
        E3[/documents/overview]
        E4[/documents/preview]
        E5[/documents/tags]
    end

    subgraph "Data Manager"
        E6[/modal-jobs/scraper]
        E7[/scrape]
        E8[/embed]
        E9[/modal-jobs/reindex/spawn]
    end

    subgraph "Platform Operator"
        E10[/health]
        E11[/integrations/status]
        E12[/config]
    end

    subgraph "Modal Workers"
        E13[/internal/scraper-pipeline/*]
    end
```

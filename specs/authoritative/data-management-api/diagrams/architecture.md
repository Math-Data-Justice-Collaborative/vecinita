# Data Management API — Architecture Diagram

> Auto-generated: 2026-05-12

## System Context

```mermaid
graph TB
    subgraph Vecinita Platform
        GW[Gateway]
        AG[Agent]
        DM[Data Management API]
        FE[Chat Frontend]
        DMFE[DM Frontend / SPA]
    end

    subgraph Modal Workers
        SCR[Scraper App]
        EMB[Embedding App]
        MDL[Model App]
    end

    DB[(PostgreSQL<br/>vecinita-postgres)]

    DMFE -->|HTTP<br/>VITE_DM_API_BASE_URL| DM
    FE -->|HTTP| GW
    GW -->|HTTP proxy| DM
    DM -->|HTTP / Modal SDK| SCR
    DM -->|HTTP / Modal SDK| EMB
    DM -->|HTTP / Modal SDK| MDL
    SCR --> DB
    DM -.->|validates<br/>DATABASE_URL| DB
```

## Component View

```mermaid
graph TB
    subgraph DM API - apps/backend/vecinita_dm_api
        AppFactory[app.py<br/>create_app]
        HealthRouter[routers/health.py]
        JobsRouter[routers/jobs_proxy.py]
        IngestRouter[routers/ingest.py]
        ResponseMapper[routers/responses.py]
        CorpusGuard[corpus_db_guard.py]
        CorpusConflict[corpus_conflict.py]
    end

    subgraph packages/service-clients
        ScraperCli[ScraperClient]
        EmbedCli[EmbeddingClient]
        ModelCli[ModelClient]
        ModalInv[modal_invoker.py]
    end

    subgraph packages/shared-config
        Settings[BaseServiceSettings]
    end

    subgraph packages/shared-schemas
        Schemas[EmbedRequest/Response<br/>PredictRequest/Response<br/>ScrapeRequest/Result]
    end

    AppFactory --> HealthRouter
    AppFactory --> JobsRouter
    AppFactory --> IngestRouter
    HealthRouter --> ScraperCli
    HealthRouter --> CorpusGuard
    JobsRouter --> ScraperCli
    JobsRouter --> ResponseMapper
    IngestRouter --> EmbedCli
    IngestRouter --> ModelCli
    IngestRouter --> CorpusConflict
    ScraperCli --> ModalInv
    EmbedCli --> ModalInv
    ModelCli --> ModalInv
    AppFactory --> Settings
    IngestRouter --> Schemas
```

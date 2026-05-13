# Data Management API — Integration Points Diagram

> Auto-generated: 2026-05-12

## Service Connectivity

```mermaid
graph LR
    subgraph Inbound
        DMFE[DM Frontend SPA]
        GW[Gateway]
    end

    subgraph DM API
        DM[Data Management API<br/>FastAPI]
    end

    subgraph Outbound - HTTP
        SCR_HTTP[Scraper<br/>SCRAPER_SERVICE_BASE_URL]
        EMB_HTTP[Embedding<br/>EMBEDDING_SERVICE_BASE_URL]
        MDL_HTTP[Model<br/>MODEL_SERVICE_BASE_URL]
    end

    subgraph Outbound - Modal SDK
        SCR_MODAL[Scraper<br/>vecinita-scraper]
        EMB_MODAL[Embedding<br/>vecinita-embedding]
        MDL_MODAL[Model<br/>vecinita-model]
    end

    subgraph Data
        DB[(PostgreSQL<br/>vecinita-postgres)]
    end

    DMFE -->|HTTP<br/>CORS| DM
    GW -->|HTTP proxy| DM
    DM -->|HTTP| SCR_HTTP
    DM -->|HTTP| EMB_HTTP
    DM -->|HTTP| MDL_HTTP
    DM -->|Modal SDK| SCR_MODAL
    DM -->|Modal SDK| EMB_MODAL
    DM -->|Modal SDK| MDL_MODAL
    DM -.->|validate<br/>DATABASE_URL| DB
```

## Authentication Flow

```mermaid
flowchart LR
    Request[Incoming Request] --> CORSCheck{CORS<br/>allowed origin?}
    CORSCheck -->|no| Block[Blocked by browser]
    CORSCheck -->|yes| Route{Route<br/>type?}
    Route -->|/health| Health[Health Handler<br/>no auth]
    Route -->|/jobs/*| JobsProxy[Jobs Proxy<br/>forwards Bearer token to scraper]
    Route -->|/embed, /predict| Ingest[Ingest Handler<br/>no auth, CORS-protected]
    JobsProxy --> ScraperAuth[Scraper validates<br/>SCRAPER_API_KEYS]
    ScraperAuth -->|valid| Response[Response]
    ScraperAuth -->|invalid| Reject[401/403]
```

## Modal Routing Decision

```mermaid
flowchart TD
    Call[Service Client Call] --> Check{MODAL_FUNCTION_INVOCATION?}
    Check -->|empty / http / 0| HTTP[HTTP Client<br/>httpx.AsyncClient]
    Check -->|auto| TokenCheck{Token pair<br/>configured?}
    Check -->|1 / true| Modal[Modal SDK<br/>Function.from_name.remote]
    TokenCheck -->|yes| Modal
    TokenCheck -->|no| HTTP
    HTTP --> Response[Response]
    Modal -->|asyncio.to_thread| Response
```

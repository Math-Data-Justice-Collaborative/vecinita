# data-management-frontend — Architecture Diagram

> Auto-generated: 2026-05-12

## System Context

```mermaid
graph TB
    subgraph Vecinita Platform
        DMFE[DM Frontend]
        DMAPI[DM API]
        GW[Gateway]
        Modal[Modal Workers]
    end

    Admin[Admin / Developer] -->|Browser| DMFE
    DMFE -->|"HTTP REST"| DMAPI
    DMAPI -->|"Modal SDK"| Modal

    style DMFE fill:#f9f,stroke:#333,stroke-width:2px
```

## Component View

```mermaid
graph TB
    subgraph "DM Frontend (React SPA)"
        subgraph "Providers"
            Locale[LocaleProvider]
            Auth[AuthContext]
        end

        subgraph "Pages"
            Dash[Dashboard]
            Corpus[CorpusView]
            AddDoc[AddDocument]
            DocDetail[DocumentDetail]
            Jobs[ScrapeJobs]
            Tags[TagsView]
            Settings[Settings]
        end

        subgraph "Shared"
            Layout[Layout]
            RequireAuth[RequireAuth]
        end

        subgraph "API Layer"
            RAGApi[RAGApiClient]
            ScraperCfg[scraper-config]
            ModalTypes[modal-types]
        end

        subgraph "UI"
            ShadcnUI[Shadcn/ui]
        end
    end

    Layout --> Dash
    Layout --> Corpus
    Layout --> AddDoc
    Layout --> Jobs
    Layout --> Tags
    Dash --> RAGApi
    Corpus --> RAGApi
    AddDoc --> RAGApi
    Jobs --> RAGApi
    Tags --> RAGApi
    RAGApi --> ScraperCfg
    RAGApi -->|HTTP| DMAPI[DM API]
```

# Integration Points Diagram: Embedding Worker
> Auto-generated: 2026-05-12

## Service Connectivity

```mermaid
graph LR
    subgraph "Render"
        GW["Gateway<br/>(FastAPI on Render)"]
    end

    subgraph "Modal"
        EW["Embedding Worker<br/>(vecinita-embedding)"]
        VOL["Volume<br/>(embedding-models)"]
        EW ---|"model cache"| VOL
    end

    subgraph "Database"
        PG["PostgreSQL<br/>(agent.vectors)"]
    end

    subgraph "External"
        HF["HuggingFace Hub<br/>(model download)"]
    end

    GW -->|"Modal SDK<br/>fn.remote()"| EW
    EW -->|"return vectors"| GW
    GW -->|"INSERT vectors"| PG
    EW -.->|"first-run download"| HF
```

## Gateway Invocation Detail

```mermaid
graph TD
    subgraph "Gateway invoker.py"
        A["invoke_modal_embedding_single(text)"]
        B["invoke_modal_embedding_batch(texts)"]
        C["_lookup_function(app, fn, env)<br/>(LRU cached)"]
        D["modal.Function.from_name()"]
    end

    subgraph "Environment"
        E1["MODAL_EMBEDDING_APP_NAME<br/>default: vecinita-embedding"]
        E2["MODAL_EMBEDDING_SINGLE_FUNCTION<br/>default: embed_query"]
        E3["MODAL_EMBEDDING_BATCH_FUNCTION<br/>default: embed_batch"]
        E4["MODAL_FUNCTION_INVOCATION<br/>auto | on | off"]
        E5["MODAL_TOKEN_ID / MODAL_TOKEN_SECRET"]
    end

    A --> C
    B --> C
    C --> D

    E1 --> A
    E2 --> A
    E3 --> B
    E4 -.->|"gate"| C
    E5 -.->|"auth"| D

    subgraph "Modal"
        F["embed_query"]
        G["embed_batch"]
    end

    D -->|".remote()"| F
    D -->|".remote()"| G
```

## Invocation Mode Decision

```mermaid
flowchart TD
    A["MODAL_FUNCTION_INVOCATION"] --> B{Value?}
    B -->|"empty / unset"| C["OFF<br/>Use HTTP fallback"]
    B -->|"auto"| D{"Modal tokens<br/>configured?"}
    D -->|Yes| E["ON<br/>Use Modal SDK"]
    D -->|No| C
    B -->|"true / 1 / yes"| E
    B -->|"false / http / rest"| C
```

See: [Integration Points](../03-integration-points.md)

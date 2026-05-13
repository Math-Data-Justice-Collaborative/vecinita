# vLLM Inference — Architecture Diagram
> Auto-generated: 2026-05-12

## System Context

```mermaid
graph TB
    subgraph Vecinita Platform
        GW[Gateway<br/>Render]
        AG[Agent<br/>Render]
        FE[Chat Frontend<br/>Render]
    end

    subgraph Modal GPU
        VLLM[vLLM Inference<br/>H100/A100]
        EMB[Embedding<br/>CPU]
        SCR[Scraper<br/>CPU]
    end

    subgraph External
        HF[Hugging Face Hub]
    end

    DB[(PostgreSQL<br/>Render)]

    FE -->|HTTP| GW
    GW -->|HTTP internal| AG
    GW -->|Modal SDK| VLLM
    AG -->|OpenAI REST API| VLLM
    AG -->|Modal SDK| EMB
    GW -->|Modal SDK| SCR
    AG --> DB
    GW --> DB
    VLLM -.->|weight download| HF
```

## Component View

```mermaid
graph TB
    subgraph vLLM Inference Service
        APP[app.py<br/>Modal App Definition]
        CFG[config.py<br/>Settings + Model Registry]
        ENG[engine.py<br/>vLLM Engine Lifecycle]
        DL[download.py<br/>Weight Preloader]
        VLLM_SRV[vLLM OpenAI Server<br/>Built-in ASGI]
    end

    subgraph Modal Infrastructure
        VOL[(vecinita-vllm-models<br/>Persistent Volume)]
        GPU[GPU<br/>A100/H100]
        SEC[Modal Secrets<br/>HF_TOKEN, API_KEY]
    end

    APP --> CFG
    APP --> ENG
    APP --> DL
    ENG --> VLLM_SRV
    ENG --> GPU
    DL --> VOL
    VLLM_SRV --> VOL
    APP --> SEC

    Agent[Agent Service] -->|/v1/chat/completions| VLLM_SRV
    Gateway[Gateway] -->|Function.remote| APP
```

## Layer Diagram

```mermaid
graph TB
    subgraph API Layer
        OAI[OpenAI-Compatible API<br/>/v1/chat/completions<br/>/v1/completions<br/>/v1/models]
        HEALTH[/health]
    end

    subgraph Engine Layer
        SCHED[vLLM Scheduler<br/>Continuous Batching]
        PA[PagedAttention<br/>KV Cache Manager]
        TOK[Tokenizer<br/>HF Transformers]
    end

    subgraph Infrastructure Layer
        MODAL[Modal Container<br/>GPU + Volume]
        CUDA[CUDA Runtime<br/>12.1+]
    end

    OAI --> SCHED
    HEALTH --> SCHED
    SCHED --> PA
    SCHED --> TOK
    PA --> CUDA
    CUDA --> MODAL
```

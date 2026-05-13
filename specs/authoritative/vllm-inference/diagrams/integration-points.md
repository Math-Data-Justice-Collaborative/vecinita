# vLLM Inference — Integration Points Diagram
> Auto-generated: 2026-05-12

## Service Connectivity

```mermaid
graph LR
    subgraph Vecinita Services
        AG[Agent Service<br/>Render]
        GW[Gateway<br/>Render]
    end

    subgraph Modal
        VLLM[vLLM Inference<br/>GPU]
        VOL[(vecinita-vllm-models)]
    end

    subgraph External
        HF[Hugging Face Hub]
    end

    AG -->|OpenAI REST API<br/>POST /v1/chat/completions| VLLM
    GW -->|Modal SDK<br/>Function.from_name.remote| VLLM
    VLLM -->|read weights| VOL
    VLLM -.->|download weights<br/>deploy-time only| HF
```

## Protocol Detail

```mermaid
graph TB
    subgraph Agent Path
        AG_LLAMA[LlamaIndex<br/>llama-index-llms-vllm] -->|HTTPS| VLLM_API[/v1/chat/completions]
    end

    subgraph Gateway Path
        GW_INV[Gateway Invoker<br/>modal.Function.from_name] -->|Modal RPC| VLLM_FN[chat_completion function]
    end

    subgraph vLLM Inference
        VLLM_API --> ENGINE[vLLM Engine]
        VLLM_FN --> ENGINE
    end
```

## Authentication Flow

```mermaid
flowchart LR
    Request[Incoming Request] --> API_KEY{API Key?}
    API_KEY -->|valid or disabled| ENGINE[vLLM Engine]
    API_KEY -->|invalid| REJECT[401 Unauthorized]
    ENGINE --> Response[Completion Response]
```

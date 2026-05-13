# vLLM Inference — Sequence Flow Diagrams
> Auto-generated: 2026-05-12

## Chat Completion (Non-Streaming)

```mermaid
sequenceDiagram
    participant Agent
    participant vLLM as vLLM API Server
    participant Engine as vLLM Engine
    participant GPU

    Agent->>vLLM: POST /v1/chat/completions
    vLLM->>vLLM: Validate request
    vLLM->>Engine: Submit to scheduler
    Engine->>Engine: Apply chat template
    Engine->>Engine: Tokenize
    Engine->>GPU: Run inference (PagedAttention)
    GPU-->>Engine: Output token IDs
    Engine->>Engine: Detokenize
    Engine-->>vLLM: Completion result
    vLLM-->>Agent: 200 ChatCompletionResponse
```

## Chat Completion (Streaming)

```mermaid
sequenceDiagram
    participant Agent
    participant vLLM as vLLM API Server
    participant Engine as vLLM Engine
    participant GPU

    Agent->>vLLM: POST /v1/chat/completions (stream: true)
    vLLM->>Engine: Submit to scheduler
    Engine->>GPU: Begin inference

    loop Each token batch
        GPU-->>Engine: Token IDs
        Engine->>Engine: Detokenize batch
        Engine-->>vLLM: Delta content
        vLLM-->>Agent: SSE data: {delta}
    end

    Engine-->>vLLM: Generation complete
    vLLM-->>Agent: SSE data: [DONE]
```

## Cold Start Sequence

```mermaid
sequenceDiagram
    participant Agent
    participant Modal
    participant Container
    participant Volume as vecinita-vllm-models
    participant Engine as vLLM Engine
    participant GPU

    Agent->>Modal: POST /v1/chat/completions
    Modal->>Modal: No warm containers
    Modal->>Container: Spin up (allocate GPU)
    Container->>Volume: Mount at /models
    Container->>Engine: Initialize vLLM
    Engine->>Volume: Load model weights
    Engine->>GPU: Transfer to GPU memory
    GPU-->>Engine: Ready
    Engine-->>Container: Engine ready
    Container->>Engine: Process queued request
    Engine->>GPU: Run inference
    GPU-->>Engine: Output tokens
    Engine-->>Container: Completion
    Container-->>Modal: Response
    Modal-->>Agent: 200 ChatCompletionResponse
    Note over Container: Stays warm for scaledown_window
```

## Model Weight Download

```mermaid
sequenceDiagram
    participant CI as CI / Operator
    participant Modal
    participant Fn as download_model()
    participant HF as Hugging Face Hub
    participant Volume as vecinita-vllm-models

    CI->>Modal: modal run app.py::download_model --model-id ...
    Modal->>Fn: Execute (CPU container)
    Fn->>HF: snapshot_download(model_id)
    HF-->>Fn: Model files (safetensors)
    Fn->>Volume: Write to /models/<model_id>/
    Fn->>Volume: volume.commit()
    Volume-->>Fn: Persisted
    Fn-->>Modal: Success
    Modal-->>CI: Exit 0
```

## Gateway Modal SDK Invocation

```mermaid
sequenceDiagram
    participant Gateway
    participant Modal as Modal SDK
    participant Fn as chat_completion()
    participant Engine as vLLM Engine

    Gateway->>Modal: Function.from_name("vecinita-vllm-inference", "chat_completion")
    Modal-->>Gateway: Function handle
    Gateway->>Modal: fn.remote(model, messages, temperature)
    Modal->>Fn: Execute on GPU container
    Fn->>Engine: Inference request
    Engine-->>Fn: Completion dict
    Fn-->>Modal: Return dict
    Modal-->>Gateway: Result dict
```

## Error Flow

```mermaid
sequenceDiagram
    participant Agent
    participant vLLM as vLLM API Server
    participant Engine as vLLM Engine

    Agent->>vLLM: POST /v1/chat/completions
    vLLM->>Engine: Submit request

    alt Engine not ready
        Engine-->>vLLM: 503 Service Unavailable
        vLLM-->>Agent: 503 Model loading
    else GPU OOM
        Engine-->>vLLM: RuntimeError
        vLLM-->>Agent: 500 Internal Server Error
    else Invalid request
        vLLM-->>Agent: 422 Validation Error
    end
```

# vLLM Inference — Data Model Diagram
> Auto-generated: 2026-05-12

The vllm-inference service is stateless — it has no database tables. The diagram below shows the request/response schema relationships.

```mermaid
erDiagram
    ChatCompletionRequest {
        string model
        array messages
        float temperature
        float top_p
        int max_tokens
        bool stream
        string stop
        float frequency_penalty
        float presence_penalty
    }

    Message {
        string role
        string content
    }

    ChatCompletionResponse {
        string id
        string object
        int created
        string model
        array choices
    }

    Choice {
        int index
        string finish_reason
    }

    Usage {
        int prompt_tokens
        int completion_tokens
        int total_tokens
    }

    CompletionRequest {
        string model
        string prompt
        int max_tokens
        float temperature
        bool stream
    }

    HealthResponse {
        string status
        string model
        string gpu
    }

    ModelInfo {
        string id
        string object
        int created
        string owned_by
    }

    ChatCompletionRequest ||--|{ Message : "contains"
    ChatCompletionResponse ||--|{ Choice : "has"
    ChatCompletionResponse ||--|| Usage : "includes"
    Choice ||--|| Message : "contains"
```

## Model Weight Storage (Volume)

```mermaid
graph TB
    subgraph Modal Volume: vecinita-vllm-models
        subgraph "google/gemma-3-4b-it/"
            CFG[config.json]
            TOK[tokenizer.json]
            W1[model-00001-of-00002.safetensors]
            W2[model-00002-of-00002.safetensors]
        end
    end
```

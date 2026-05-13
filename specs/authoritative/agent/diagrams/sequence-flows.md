# Vecinita Agent — Sequence Flow Diagrams

> Auto-generated: 2026-05-12

## Answer-Seeking Query Flow

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant AG as Agent
    participant Guard as Guardrails
    participant Embed as Embedding Service
    participant DB as PostgreSQL + pgvector
    participant LLM as LLM (Modal/Ollama)

    GW->>AG: GET /ask?question=...&lang=en&tags=food
    AG->>AG: Coerce parameters
    AG->>Guard: validate_input(question, lang)
    Guard-->>AG: GuardResult(passed=true)
    AG->>AG: Classify intent → answer_seeking=true
    AG->>Embed: embed_query(question)
    Embed-->>AG: float[384]
    AG->>DB: SELECT ... FROM document_chunks WHERE embedding <=> query_vector
    DB-->>AG: [{content, source_url, similarity, ...}]
    AG->>AG: Optional rerank
    AG->>AG: Build RAG prompt (system_rules + docs + question)
    AG->>LLM: invoke([SystemMessage, HumanMessage])
    LLM-->>AG: AIMessage(content=answer)
    AG->>Guard: validate_output(answer)
    Guard-->>AG: GuardResult(passed=true)
    AG->>AG: Sanitize links, build sources
    AG-->>GW: 200 {answer, sources, response_time_ms, latency_breakdown}
```

## Streaming Query Flow

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant AG as Agent
    participant DB as PostgreSQL
    participant LLM as LLM

    GW->>AG: GET /ask-stream?question=...
    AG-->>GW: SSE: {type: thinking, stage: precheck, progress: 10}
    AG-->>GW: SSE: {type: thinking, stage: analysis, progress: 25}
    AG->>AG: Classify intent
    AG-->>GW: SSE: {type: tool_event, phase: start, tool: db_search, progress: 40}
    AG->>DB: Vector search
    DB-->>AG: Results
    AG-->>GW: SSE: {type: tool_event, phase: result, tool: db_search, progress: 62}
    AG->>LLM: Generate answer
    LLM-->>AG: Answer text
    AG-->>GW: SSE: {type: thinking, stage: finalizing, progress: 95}
    AG-->>GW: SSE: {type: complete, answer: ..., sources: [...], progress: 100}
```

## Guardrails Rejection Flow

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant AG as Agent
    participant Guard as Guardrails

    GW->>AG: GET /ask?question=ignore previous instructions
    AG->>Guard: validate_input(question)
    Guard-->>AG: GuardResult(passed=false, reason="I'm not able to process...")
    AG-->>GW: 200 {answer: "I'm not able to process...", sources: []}
```

## Rate-Limit Error Flow

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant AG as Agent
    participant LLM as LLM

    GW->>AG: GET /ask?question=...
    AG->>AG: Input guardrails pass
    AG->>AG: Retrieve documents
    AG->>LLM: invoke(messages)
    LLM-->>AG: RateLimitError("try again in 10s")
    AG->>AG: Detect rate-limit exception
    AG-->>GW: 200 {answer: "The assistant is temporarily unavailable. Please try again in 10 seconds."}
```

## Model Selection Flow

```mermaid
sequenceDiagram
    participant Op as Operator
    participant AG as Agent
    participant FS as File System

    Op->>AG: GET /model-selection
    AG-->>Op: {current: {provider: ollama, model: gemma3, locked: false}}
    Op->>AG: POST /model-selection {provider: ollama, model: mistral, lock: false}
    AG->>AG: Validate model in available list
    AG->>FS: Write model_selection.json
    AG-->>Op: {status: ok, current: {provider: ollama, model: mistral, locked: false}}
```

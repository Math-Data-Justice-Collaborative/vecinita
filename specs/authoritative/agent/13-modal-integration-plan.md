# Vecinita Agent — Modal Integration Plan

> Auto-generated: 2026-05-12

## Overview

The agent does not run on Modal itself. It *consumes* two Modal-hosted services: the model service (vLLM LLM inference) and the embedding service. Communication uses either the Modal Python SDK (function invocation) or HTTP to Ollama-compatible endpoints hosted on Modal.

## Modal Dependencies

| Modal App | Function | Purpose | Invocation |
|-----------|----------|---------|------------|
| vecinita-model | `chat_completion` | LLM chat inference (vLLM, Ollama-compatible API) | Modal SDK (`invoke_modal_model_chat`) or HTTP `POST /chat` |
| vecinita-embedding | `embed` | Generate 384-dim embeddings (all-MiniLM-L6-v2) | HTTP REST via `EMBEDDING_SERVICE_URL` |

## Invocation Pattern

### LLM Inference (vecinita-model)

The agent uses `LocalLLMClientManager` which resolves the invocation method based on the `OLLAMA_BASE_URL`:

1. **Modal SDK (preferred on Render):** When `MODAL_FUNCTION_INVOCATION=auto|1` and Modal tokens are set, `_ModalNativeChatClient.invoke()` calls `invoke_modal_model_chat()` which uses the Modal SDK directly.
2. **HTTP endpoint:** When the base URL points to `*.modal.run`, the client sends HTTP `POST /chat` with OpenAI-compatible payload.
3. **Local Ollama:** When the URL points to localhost, `ChatOllama` from `langchain-ollama` is used.

**Source:** `apis/gateway/src/services/llm/client_manager.py` → `_ModalNativeChatClient`, `LocalLLMClientManager.build_client()`

### Embedding (vecinita-embedding)

The embedding service is called via standard HTTP REST. The agent creates an embedding client at startup and calls `embed_query(text)` for every search query (with LRU caching).

**Source:** `apis/gateway/src/embedding_service/client.py`

## Supported Models

Models accepted by the Modal native chat function:

| Model ID | Description |
|----------|-------------|
| gemma3 | Google Gemma 3 (default) |
| llama3.2 | Meta Llama 3.2 |
| llama3.2:1b | Meta Llama 3.2 1B |
| llama3.1 | Meta Llama 3.1 |
| llama3.1:8b | Meta Llama 3.1 8B |
| mistral | Mistral 7B |
| phi3 | Microsoft Phi-3 |
| gemma2 | Google Gemma 2 |
| gemma2:2b | Google Gemma 2 2B |

**Source:** `apis/gateway/src/services/llm/client_manager.py` → `_MODAL_NATIVE_FUNCTION_CHAT_MODEL_IDS`

## Environment Variables

| Variable | Source | Required | Description |
|----------|--------|----------|-------------|
| OLLAMA_BASE_URL | Render env group | yes | Modal model endpoint or local Ollama URL |
| OLLAMA_API_KEY | Render env group | no | API key for authenticated endpoints |
| MODAL_TOKEN_ID | Render env group | yes (Render) | Modal SDK authentication |
| MODAL_TOKEN_SECRET | Render env group | yes (Render) | Modal SDK authentication |
| MODAL_FUNCTION_INVOCATION | Render env group | no | `auto`, `1`, or `0` — controls SDK vs HTTP invocation |
| EMBEDDING_SERVICE_URL | Render env group | yes | HTTP URL for embedding service |
| EMBEDDING_SERVICE_AUTH_TOKEN | Render env group | no | Bearer token for embedding service |
| FORCE_LOCAL_MODAL_LLM | Render env group | no | Force use of Modal native API (default `true`) |

## Cross-reference

- [Modal Landscape](../modal/current-landscape.md)

## Related Documents

- [Integration Points](03-integration-points.md)
- [Infrastructure Plan](12-infrastructure-plan.md)

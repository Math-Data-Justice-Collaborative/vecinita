"""
Unified API Gateway - Q&A Router

Endpoints for querying the knowledge base with LangGraph agent.
Proxies requests to the agent service running on port 8000.

Demo mode available via DEMO_MODE=true environment variable for testing without agent service.
"""

import logging
import os
import threading
import time
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from .models import AskResponse, SourceCitation

router = APIRouter(prefix="/ask", tags=["Q&A"])
logger = logging.getLogger(__name__)

# Agent service configuration
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
AGENT_TIMEOUT = float(os.getenv("AGENT_TIMEOUT", "30"))
AGENT_STREAM_TIMEOUT = float(os.getenv("AGENT_STREAM_TIMEOUT", "120"))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
_AGENT_CLIENT: httpx.AsyncClient | None = None
_AGENT_CLIENT_LOCK = threading.Lock()


def _get_agent_client() -> httpx.AsyncClient | None:
    """Reuse one HTTP client to avoid per-request connection setup overhead."""
    global _AGENT_CLIENT

    def _client_is_closed(client: httpx.AsyncClient | None) -> bool:
        if client is None:
            return True
        if not isinstance(client, httpx.AsyncClient):
            return True
        return bool(getattr(client, "is_closed", False))

    if _client_is_closed(_AGENT_CLIENT):
        with _AGENT_CLIENT_LOCK:
            if _client_is_closed(_AGENT_CLIENT):
                _AGENT_CLIENT = httpx.AsyncClient(
                    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                )
    return _AGENT_CLIENT


def _fallback_ask_config() -> dict[str, Any]:
    """Return a safe fallback config when agent service is unavailable."""
    # Default to Ollama (local). Groq / X.AI intentionally excluded.
    default_provider = "ollama"
    default_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    return {
        "providers": [
            {
                "name": default_provider,
                "models": [default_model],
                "default": True,
            }
        ],
        "models": {default_provider: [default_model]},
        "defaultProvider": default_provider,
        "defaultModel": default_model,
        "service_status": "degraded",
    }


def _normalize_agent_config(agent_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize agent /config payload to frontend-expected shape."""
    models_value = agent_data.get("models")
    providers_value = agent_data.get("providers")
    raw_models: dict[str, Any] = models_value if isinstance(models_value, dict) else {}
    raw_providers: list[Any] = providers_value if isinstance(providers_value, list) else []

    normalized_providers: list[dict[str, Any]] = []

    for index, provider in enumerate(raw_providers):
        if not isinstance(provider, dict):
            continue

        provider_name = provider.get("name") or provider.get("key")
        if not provider_name:
            continue

        provider_models = raw_models.get(provider_name, [])
        if not isinstance(provider_models, list):
            provider_models = []

        normalized_providers.append(
            {
                "name": provider_name,
                "models": provider_models,
                "default": bool(provider.get("default", index == 0)),
            }
        )

    if not normalized_providers and raw_models:
        for index, (provider_name, provider_models) in enumerate(raw_models.items()):
            if not isinstance(provider_models, list):
                provider_models = []
            normalized_providers.append(
                {
                    "name": provider_name,
                    "models": provider_models,
                    "default": index == 0,
                }
            )

    if not normalized_providers:
        return _fallback_ask_config()

    default_provider_obj = next(
        (provider for provider in normalized_providers if provider.get("default")),
        normalized_providers[0],
    )
    default_provider = default_provider_obj.get("name")
    default_model = next(iter(default_provider_obj.get("models") or []), None)

    return {
        "providers": normalized_providers,
        "models": raw_models,
        "defaultProvider": default_provider,
        "defaultModel": default_model,
        "service_status": "ok",
    }


def get_demo_response(question: str, lang: str | None = None) -> AskResponse:
    """Generate a demo response when agent service is unavailable or DEMO_MODE=true."""
    return AskResponse(
        question=question,
        answer=(
            "This is a demo response from the Vecinita Unified API Gateway. "
            "The agent service is not currently connected (expected to be running at "
            f"{AGENT_SERVICE_URL}). "
            "To start the agent service:\n\n"
            "```bash\n"
            "cd backend\n"
            "python -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000\n"
            "```\n\n"
            "For now, this gateway is in demo/documentation mode. All API endpoints are fully documented "
            "in the Swagger UI at /docs, and the request/response models include comprehensive examples."
        ),
        sources=[
            SourceCitation(
                url="https://github.com/acadiagit/vecinita",
                title="Vecinita GitHub Repository",
                chunk_id="demo-001",
                relevance=0.95,
                excerpt="Vecinita is a RAG Q&A Assistant using LangChain, LangGraph, and Supabase.",
            ),
            SourceCitation(
                url="http://localhost:8004/docs",
                title="API Documentation (Swagger UI)",
                chunk_id="demo-002",
                relevance=0.88,
                excerpt="Complete OpenAPI documentation with request/response examples for all endpoints.",
            ),
        ],
        language=lang or "en",
        model="demo-mode",
        response_time_ms=0,
        token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )


@router.get("")
async def ask_question(
    question: str = Query(..., description="User question"),
    thread_id: str | None = Query(None, description="Conversation thread ID"),
    lang: str | None = Query(None, description="Override language detection (es/en)"),
    provider: str | None = Query(None, description="LLM provider (e.g., groq, openai)"),
    model: str | None = Query(None, description="LLM model name"),
    tags: str | None = Query(None, description="Comma-separated metadata tags"),
    tag_match_mode: str = Query("any", description="Tag match mode: any|all"),
    include_untagged_fallback: bool = Query(
        True, description="Include untagged docs when tag filter is active"
    ),
    rerank: bool = Query(False, description="Enable backend reranking for search results"),
    rerank_top_k: int = Query(10, ge=1, le=50, description="Number of items to keep after rerank"),
) -> AskResponse:
    """
    Ask a question and get an answer with source citations.

    The system will detect the query language (Spanish/English) automatically
    and return answers with source attribution.

    Args:
        question: User's question
        thread_id: Optional conversation thread ID for context
        lang: Optional language override (es, en, etc.)
        provider: Optional LLM provider override
        model: Optional LLM model override

    Returns:
        Answer with sources and metadata
    """
    # Return demo response if demo mode enabled or agent service unavailable
    if DEMO_MODE:
        return get_demo_response(question, lang)

    try:
        started_at = time.perf_counter()
        # Build query parameters for agent service
        params: dict[str, Any] = {"question": question}
        if thread_id:
            params["thread_id"] = thread_id
        if lang:
            params["lang"] = lang
        if provider:
            params["provider"] = provider
        if model:
            params["model"] = model
        if tags:
            params["tags"] = tags
        params["tag_match_mode"] = tag_match_mode
        params["include_untagged_fallback"] = str(include_untagged_fallback).lower()
        params["rerank"] = str(rerank).lower()
        params["rerank_top_k"] = rerank_top_k

        # Proxy request to agent service
        client = _get_agent_client()
        if client is None:
            raise HTTPException(status_code=503, detail="Agent service client not available")
        response = await client.get(
            f"{AGENT_SERVICE_URL}/ask",
            params=params,
            timeout=AGENT_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        # Map agent response to gateway format
        return AskResponse(
            question=question,
            answer=data.get("answer", ""),
            sources=data.get("sources", []),
            language=data.get("language", lang or "en"),
            model=data.get("model", "unknown"),
            response_time_ms=(
                data.get("response_time_ms")
                if isinstance(data.get("response_time_ms"), int)
                else int((time.perf_counter() - started_at) * 1000)
            ),
            token_usage=(
                data.get("token_usage") if isinstance(data.get("token_usage"), dict) else None
            ),
            latency_breakdown=(
                data.get("latency_breakdown")
                if isinstance(data.get("latency_breakdown"), dict)
                else None
            ),
        )

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Agent service timeout - question took too long to process"
        ) from exc
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail=f"Agent service error: {e.response.text}"
        ) from e
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Unable to connect to agent service: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}") from e


async def sse_proxy_generator(
    question: str,
    request_id: str,
    thread_id: str | None = None,
    lang: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    tags: str | None = None,
    tag_match_mode: str = "any",
    include_untagged_fallback: bool = True,
    rerank: bool = False,
    rerank_top_k: int = 10,
) -> AsyncGenerator[bytes, None]:
    """
    Generator that proxies SSE events from agent service.

    Yields SSE-formatted events from the agent's streaming endpoint.
    """
    try:
        started_at = time.perf_counter()
        first_chunk_latency_ms: int | None = None
        chunk_count = 0

        # Build query parameters
        params: dict[str, Any] = {"question": question}
        if thread_id:
            params["thread_id"] = thread_id
        if lang:
            params["lang"] = lang
        if provider:
            params["provider"] = provider
        if model:
            params["model"] = model
        if tags:
            params["tags"] = tags
        params["tag_match_mode"] = tag_match_mode
        params["include_untagged_fallback"] = str(include_untagged_fallback).lower()
        params["rerank"] = str(rerank).lower()
        params["rerank_top_k"] = rerank_top_k

        logger.info(
            "SSE stream start request_id=%s thread_id=%s question_length=%s",
            request_id,
            thread_id,
            len(question or ""),
        )

        # Stream from agent service
        client = _get_agent_client()
        if client is None:
            raise RuntimeError("Agent service client not available")
        async with client.stream(
            "GET",
            f"{AGENT_SERVICE_URL}/ask-stream",
            params=params,
            timeout=AGENT_STREAM_TIMEOUT,
        ) as response:
            response.raise_for_status()

            # Forward raw SSE bytes from agent to preserve event boundaries.
            async for chunk in response.aiter_bytes():
                if chunk:
                    chunk_count += 1
                    if first_chunk_latency_ms is None:
                        first_chunk_latency_ms = int((time.perf_counter() - started_at) * 1000)
                        logger.info(
                            "SSE first chunk request_id=%s latency_ms=%s",
                            request_id,
                            first_chunk_latency_ms,
                        )
                    yield chunk

        logger.info(
            "SSE stream completed request_id=%s chunks=%s first_chunk_latency_ms=%s",
            request_id,
            chunk_count,
            first_chunk_latency_ms,
        )

    except httpx.TimeoutException:
        logger.warning("SSE stream timeout request_id=%s", request_id)
        error_event = 'data: {"type": "error", "message": "Request timeout"}\n\n'
        yield error_event.encode("utf-8")
    except httpx.HTTPStatusError as e:
        logger.warning(
            "SSE stream http error request_id=%s status=%s", request_id, e.response.status_code
        )
        error_event = (
            f'data: {{"type": "error", "message": "Agent error: {e.response.status_code}"}}\n\n'
        )
        yield error_event.encode("utf-8")
    except httpx.RequestError as e:
        logger.warning("SSE stream request error request_id=%s error=%s", request_id, str(e))
        error_event = f'data: {{"type": "error", "message": "Connection failed: {str(e)}"}}\n\n'
        yield error_event.encode("utf-8")
    except Exception as e:
        logger.exception("SSE stream internal error request_id=%s", request_id)
        error_event = f'data: {{"type": "error", "message": "Internal error: {str(e)}"}}\n\n'
        yield error_event.encode("utf-8")


@router.get("/stream")
async def ask_question_stream(
    question: str = Query(..., description="User question"),
    thread_id: str | None = Query(None, description="Conversation thread ID"),
    lang: str | None = Query(None, description="Override language detection (es/en)"),
    provider: str | None = Query(None, description="LLM provider (e.g., groq, openai)"),
    model: str | None = Query(None, description="LLM model name"),
    tags: str | None = Query(None, description="Comma-separated metadata tags"),
    tag_match_mode: str = Query("any", description="Tag match mode: any|all"),
    include_untagged_fallback: bool = Query(
        True, description="Include untagged docs when tag filter is active"
    ),
    rerank: bool = Query(False, description="Enable backend reranking for search results"),
    rerank_top_k: int = Query(10, ge=1, le=50, description="Number of items to keep after rerank"),
):
    """
    Ask a question and stream the response as Server-Sent Events (SSE).

    Proxies streaming from the agent service for real-time updates.

    Event types:
    - thinking: Agent is processing (with status message)
    - tool_event: Compact tool lifecycle updates (start/result/error)
    - complete: Final answer with sources
    - clarification: Agent needs more info
    - error: Something went wrong

    Args:
        question: User's question
        thread_id: Optional conversation thread ID for context
        lang: Optional language override (es, en, etc.)
        provider: Optional LLM provider override
        model: Optional LLM model override

    Returns:
        StreamingResponse with SSE events
    """
    request_id = str(uuid4())
    logger.info(
        "Incoming /ask/stream request_id=%s thread_id=%s question_length=%s",
        request_id,
        thread_id,
        len(question or ""),
    )

    return StreamingResponse(
        sse_proxy_generator(
            question,
            request_id,
            thread_id,
            lang,
            provider,
            model,
            tags,
            tag_match_mode,
            include_untagged_fallback,
            rerank,
            rerank_top_k,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/config")
async def get_ask_config():
    """
    Get current Q&A configuration (available LLM providers and models).

    Proxies to agent service /config endpoint.

    Returns:
        Configuration with available providers and models
    """
    try:
        client = _get_agent_client()
        if client is None:
            return _fallback_ask_config()
        response = await client.get(f"{AGENT_SERVICE_URL}/config", timeout=10.0)
        response.raise_for_status()
        return _normalize_agent_config(response.json())

    except httpx.RequestError:
        return _fallback_ask_config()
    except Exception:
        return _fallback_ask_config()

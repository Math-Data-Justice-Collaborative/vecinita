"""
Unified API Gateway - Q&A Router

Endpoints for querying the knowledge base with LangGraph agent.
Proxies requests to the agent service running on port 8000.

Demo mode available via DEMO_MODE=true environment variable for testing without agent service.
"""

import os
from typing import Optional, AsyncGenerator
from datetime import datetime

import httpx
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from .models import AskResponse, SourceCitation

router = APIRouter(prefix="/ask", tags=["Q&A"])

# Agent service configuration
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")
AGENT_TIMEOUT = float(os.getenv("AGENT_TIMEOUT", "30"))
AGENT_STREAM_TIMEOUT = float(os.getenv("AGENT_STREAM_TIMEOUT", "120"))
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


def get_demo_response(question: str, lang: Optional[str] = None) -> AskResponse:
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
            "python -m uvicorn src.services.agent.server:app --host 0.0.0.0 --port 8000\n"
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
                excerpt="Vecinita is a RAG Q&A Assistant using LangChain, LangGraph, and Supabase."
            ),
            SourceCitation(
                url="http://localhost:8004/docs",
                title="API Documentation (Swagger UI)",
                chunk_id="demo-002",
                relevance=0.88,
                excerpt="Complete OpenAPI documentation with request/response examples for all endpoints."
            )
        ],
        language=lang or "en",
        model="demo-mode",
        response_time_ms=0,
        token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    )


@router.get("")
async def ask_question(
    question: str = Query(..., description="User question"),
    thread_id: Optional[str] = Query(None, description="Conversation thread ID"),
    lang: Optional[str] = Query(None, description="Override language detection (es/en)"),
    provider: Optional[str] = Query(None, description="LLM provider (e.g., groq, openai)"),
    model: Optional[str] = Query(None, description="LLM model name"),
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
        # Build query parameters for agent service
        params = {"question": question}
        if thread_id:
            params["thread_id"] = thread_id
        if lang:
            params["lang"] = lang
        if provider:
            params["provider"] = provider
        if model:
            params["model"] = model

        # Proxy request to agent service
        async with httpx.AsyncClient(timeout=AGENT_TIMEOUT) as client:
            response = await client.get(
                f"{AGENT_SERVICE_URL}/ask",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        # Map agent response to gateway format
        return AskResponse(
            question=question,
            answer=data.get("answer", ""),
            sources=data.get("sources", []),
            language=data.get("language", lang or "en"),
            model=data.get("model", "unknown")
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Agent service timeout - question took too long to process"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Agent service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to agent service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


async def sse_proxy_generator(
    question: str,
    thread_id: Optional[str] = None,
    lang: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Generator that proxies SSE events from agent service.
    
    Yields SSE-formatted events from the agent's streaming endpoint.
    """
    try:
        # Build query parameters
        params = {"question": question}
        if thread_id:
            params["thread_id"] = thread_id
        if lang:
            params["lang"] = lang
        if provider:
            params["provider"] = provider
        if model:
            params["model"] = model

        # Stream from agent service
        async with httpx.AsyncClient(timeout=AGENT_STREAM_TIMEOUT) as client:
            async with client.stream(
                "GET",
                f"{AGENT_SERVICE_URL}/ask-stream",
                params=params
            ) as response:
                response.raise_for_status()
                
                # Forward SSE events from agent
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"

    except httpx.TimeoutException:
        error_event = 'data: {"type": "error", "message": "Request timeout"}\n\n'
        yield error_event
    except httpx.HTTPStatusError as e:
        error_event = f'data: {{"type": "error", "message": "Agent error: {e.response.status_code}"}}\n\n'
        yield error_event
    except httpx.RequestError as e:
        error_event = f'data: {{"type": "error", "message": "Connection failed: {str(e)}"}}\n\n'
        yield error_event
    except Exception as e:
        error_event = f'data: {{"type": "error", "message": "Internal error: {str(e)}"}}\n\n'
        yield error_event


@router.get("/stream")
async def ask_question_stream(
    question: str = Query(..., description="User question"),
    thread_id: Optional[str] = Query(None, description="Conversation thread ID"),
    lang: Optional[str] = Query(None, description="Override language detection (es/en)"),
    provider: Optional[str] = Query(None, description="LLM provider (e.g., groq, openai)"),
    model: Optional[str] = Query(None, description="LLM model name"),
):
    """
    Ask a question and stream the response as Server-Sent Events (SSE).
    
    Proxies streaming from the agent service for real-time updates.
    
    Event types:
    - thinking: Agent is processing (with status message)
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
    return StreamingResponse(
        sse_proxy_generator(question, thread_id, lang, provider, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
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
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{AGENT_SERVICE_URL}/config")
            response.raise_for_status()
            return response.json()

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to connect to agent service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )

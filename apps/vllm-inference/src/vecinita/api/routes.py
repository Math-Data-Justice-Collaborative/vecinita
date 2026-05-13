"""FastAPI route handlers.

``create_app`` is a factory that builds and returns a :class:`fastapi.FastAPI`
application.  It is called once per container when Modal starts the web
endpoint.  The Ollama server must already be running before this is called
(see ``app.py``).
"""

from __future__ import annotations

import json
import logging

import ollama as _ollama
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from ..config import resolve_startup_model_id, settings
from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Message,
    StreamChunk,
)

logger = logging.getLogger(__name__)


def create_app(ollama_host: str = settings.ollama_host) -> FastAPI:  # noqa: B008
    """Build and return the FastAPI application.

    Parameters
    ----------
    ollama_host:
        Base URL of the running Ollama server.  Defaults to the value in
        ``settings`` so that tests can override it easily.
    """
    client = _ollama.Client(host=ollama_host)

    app = FastAPI(
        title="Vecinita Model API",
        description="Serverless LLM inference API powered by Modal and Ollama.",
        version="0.1.0",
    )

    # ------------------------------------------------------------------
    # /health and /api/health
    # ------------------------------------------------------------------

    @app.get("/health", response_model=HealthResponse, tags=["Meta"])
    async def health() -> HealthResponse:
        """Return service status and the list of locally available models."""
        startup_model: str | None
        try:
            startup_model = resolve_startup_model_id()
        except ValueError as exc:
            logger.warning(
                "Startup model configuration invalid for health endpoint: %s",
                exc,
            )
            startup_model = None

        try:
            listed = client.list()
            model_names = [m.model for m in listed.models]
            return HealthResponse(
                status="ok",
                models=model_names,
                startup_model=startup_model,
            )
        except Exception as exc:
            logger.warning("Health check failed: %s", exc)
            return HealthResponse(
                status="error",
                models=[],
                startup_model=startup_model,
            )

    @app.get("/api/health", response_model=HealthResponse, tags=["Meta"])
    async def api_health() -> HealthResponse:
        """Return service status and locally available models in Ollama format."""
        return await health()

    # ------------------------------------------------------------------
    # /chat and /api/chat
    # ------------------------------------------------------------------

    @app.post("/chat", response_model=ChatResponse, tags=["Inference"])
    async def chat(request: ChatRequest) -> ChatResponse:
        """Send a conversation and receive a complete response."""
        try:
            response = client.chat(
                model=request.model,
                messages=[
                    {"role": m.role, "content": m.content}
                    for m in request.messages
                ],
                options=_build_options(request),
            )
            return ChatResponse(
                model=request.model,
                message=Message(
                    role="assistant",
                    content=response.message.content,
                ),
            )
        except Exception as exc:
            logger.error("Chat request failed: %s", exc)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request",
            ) from exc

    @app.post("/api/chat", response_model=ChatResponse, tags=["Inference"])
    async def api_chat(request: ChatRequest) -> ChatResponse:
        """Send a conversation and receive a complete response in Ollama format."""
        return await chat(request)

    # ------------------------------------------------------------------
    # /stream and /api/stream
    # ------------------------------------------------------------------

    @app.post("/stream", tags=["Inference"])
    async def stream(request: ChatRequest) -> StreamingResponse:
        """Stream response tokens as Server-Sent Events.

        Each event is a JSON-encoded :class:`StreamChunk`.  The final event
        has ``done=true``.
        """

        def generate():
            try:
                for chunk in client.chat(
                    model=request.model,
                    messages=[
                        {"role": m.role, "content": m.content}
                        for m in request.messages
                    ],
                    stream=True,
                    options=_build_options(request),
                ):
                    data = StreamChunk(
                        model=request.model,
                        content=chunk.message.content,
                        done=chunk.done,
                    )
                    yield f"data: {data.model_dump_json()}\n\n"
            except Exception as exc:
                error_payload = json.dumps({"error": str(exc)})
                yield f"data: {error_payload}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.post("/api/stream", tags=["Inference"])
    async def api_stream(request: ChatRequest) -> StreamingResponse:
        """Stream response tokens as Server-Sent Events (Ollama API format)."""
        return await stream(request)

    return app


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _build_options(request: ChatRequest) -> dict:
    options: dict = {}
    if request.temperature is not None:
        options["temperature"] = request.temperature
    if request.max_tokens is not None:
        options["num_predict"] = request.max_tokens
    return options

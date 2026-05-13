"""Pydantic request and response schemas for the Vecinita Model API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _default_model() -> str:
    from vecinita.config import settings

    return settings.default_model


class Message(BaseModel):
    """A single chat message in Ollama-compatible chat format."""

    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Speaker role for this turn.",
        examples=["user"],
    )
    content: str = Field(
        ...,
        description="Plain-text message body.",
        examples=["What affordable housing resources exist in Oakland?"],
    )


class ChatRequest(BaseModel):
    """Request body for the /chat, /api/chat, /stream, and /api/stream endpoints."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model": "gemma3",
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Summarize tenant rights in two bullet points."
                            ),
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 256,
                },
                {
                    "model": "gemma3",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You answer in Spanish using short paragraphs.",
                        },
                        {
                            "role": "user",
                            "content": "¿Dónde pido vouchers escolares?",
                        },
                    ],
                    "temperature": 0.3,
                    "max_tokens": 512,
                },
                {
                    "model": "gemma3",
                    "messages": [
                        {
                            "role": "user",
                            "content": "List three documents for WIC enrollment.",
                        },
                        {
                            "role": "assistant",
                            "content": (
                                "Typically ID, proof of income, and proof of residence."
                            ),
                        },
                        {
                            "role": "user",
                            "content": "Which IDs if I have no passport?",
                        },
                    ],
                    "temperature": 0.5,
                    "max_tokens": 400,
                },
                {
                    "model": "gemma3",
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Explain cooling centers vs libraries in heat waves."
                            ),
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 320,
                },
                {
                    "model": "gemma3",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Draft a polite rent payment plan email.",
                        }
                    ],
                    "temperature": 0.9,
                    "max_tokens": 600,
                },
            ]
        }
    )

    model: str = Field(
        default_factory=_default_model,
        description="Ollama model tag available on the server (see GET /health).",
        examples=["gemma3"],
    )
    messages: list[Message] = Field(
        ...,
        min_length=1,
        description="Ordered chat turns; must include at least one message.",
    )
    temperature: float | None = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature forwarded to Ollama as ``temperature``.",
        examples=[0.7],
    )
    max_tokens: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Upper bound on generated tokens (mapped to Ollama ``num_predict``)."
        ),
        examples=[256],
    )


class ChatResponse(BaseModel):
    """Response body for the /chat endpoint."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model": "gemma3",
                    "message": {
                        "role": "assistant",
                        "content": "Here is a concise summary of tenant rights.",
                    },
                    "done": True,
                },
                {
                    "model": "gemma3",
                    "message": {
                        "role": "assistant",
                        "content": "El horario de la clínica es lunes a viernes.",
                    },
                    "done": True,
                },
                {
                    "model": "gemma3",
                    "message": {
                        "role": "assistant",
                        "content": "Bring ID, proof of income, and proof of address.",
                    },
                    "done": True,
                },
                {
                    "model": "gemma3",
                    "message": {
                        "role": "assistant",
                        "content": "Cooling centers include Main Library this weekend.",
                    },
                    "done": True,
                },
                {
                    "model": "gemma3",
                    "message": {
                        "role": "assistant",
                        "content": "Bus 14 runs every 15 minutes at peak.",
                    },
                    "done": True,
                },
            ]
        }
    )

    model: str = Field(..., examples=["gemma3"])
    message: Message
    done: bool = Field(default=True, examples=[True])


class StreamChunk(BaseModel):
    """A single chunk yielded by the /stream endpoint (Server-Sent Events)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"model": "gemma3", "content": "Partial ", "done": False},
                {"model": "gemma3", "content": "", "done": True},
                {"model": "gemma3", "content": "Here is ", "done": False},
                {"model": "gemma3", "content": "the answer.", "done": False},
                {"model": "gemma3", "content": "\n", "done": True},
            ]
        }
    )

    model: str = Field(..., examples=["gemma3"])
    content: str = Field(..., examples=["Streaming token text…"])
    done: bool = Field(..., examples=[False])


class HealthResponse(BaseModel):
    """Runtime health and model discovery for load balancers and humans."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "ok", "models": ["gemma3", "llama3.2:latest"]},
                {"status": "error", "models": []},
                {"status": "ok", "models": ["mistral", "phi3:mini"]},
                {"status": "ok", "models": ["gemma3"]},
                {"status": "ok", "models": ["custom:latest"]},
            ]
        }
    )

    status: Literal["ok", "error"] = Field(
        ...,
        description="``ok`` when the Ollama client listed models successfully.",
        examples=["ok"],
    )
    models: list[str] = Field(
        default_factory=list,
        description="Model tags reported by the local Ollama server.",
        examples=[["gemma3", "llama3.2:latest"]],
    )
    startup_model: str | None = Field(
        default=None,
        description="Configured startup model id used for preload readiness.",
        examples=["gemma3"],
    )

"""OpenAPI-oriented Pydantic models and response maps for the agent FastAPI app."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentRootInfo(BaseModel):
    """`GET /` service discovery payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "service": "Vecinita Backend API",
                    "status": "running",
                    "version": "2.0",
                    "endpoints": {
                        "health": "/health",
                        "ask": "/ask?question=<your_question>",
                        "docs": "/docs",
                        "config": "/config",
                    },
                    "message": "Use the React frontend or call /ask directly.",
                }
            ]
        }
    )

    service: str = Field(..., examples=["Vecinita Backend API"])
    status: str = Field(..., examples=["running"])
    version: str = Field(..., examples=["2.0"])
    endpoints: dict[str, str] = Field(default_factory=dict)
    message: str = Field(..., examples=["Service discovery payload."])


class AgentHealthResponse(BaseModel):
    """`GET /health` payload; `preflight` mirrors optional startup diagnostics."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "readiness": "unknown",
                    "preflight": None,
                },
                {
                    "status": "ok",
                    "readiness": "ready",
                    "preflight": {"postgres": "ok"},
                },
                {
                    "status": "ok",
                    "readiness": "degraded",
                    "preflight": {"postgres": "slow"},
                },
                {
                    "status": "error",
                    "readiness": "not_ready",
                    "preflight": {"postgres": "unreachable"},
                },
                {
                    "status": "ok",
                    "readiness": "unknown",
                    "preflight": {"guardrails": "skipped"},
                },
            ]
        },
    )

    status: str = Field(..., examples=["ok"])
    readiness: str = Field(..., examples=["unknown"])


class PrivacyMarkdownPayload(BaseModel):
    """`GET /privacy` JSON body."""

    markdown: str


class ModelSelectionGetApiResponse(BaseModel):
    """`GET /model-selection` — `current` plus the same keys as `GET /config` for `available`."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "current": {
                        "provider": "ollama",
                        "model": "gemma3",
                        "locked": False,
                    }
                },
                {
                    "current": {
                        "provider": "ollama",
                        "model": None,
                        "locked": False,
                    }
                },
                {
                    "current": {
                        "provider": "ollama",
                        "model": "gemma3",
                        "locked": True,
                    }
                },
                {
                    "current": {
                        "provider": "ollama",
                        "model": "mistral",
                        "locked": False,
                    }
                },
                {
                    "current": {
                        "provider": "ollama",
                        "model": "phi3:mini",
                        "locked": False,
                    }
                },
            ]
        },
    )

    current: dict[str, Any]


class AgentLlmConfigApiResponse(BaseModel):
    """`GET /config` — LLM catalog plus `runtime` tuning block."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {"providers": [], "models": {"ollama": ["gemma3"]}},
                {"providers": [{"name": "ollama"}], "models": {"ollama": []}},
                {
                    "providers": [{"name": "ollama", "available": True}],
                    "models": {"ollama": ["gemma3", "mistral"]},
                },
                {
                    "providers": [],
                    "models": {"ollama": ["phi3:mini"]},
                    "runtime": {"temperature": 0.7},
                },
                {"providers": [], "models": {}, "defaultProvider": "ollama"},
            ]
        },
    )

    providers: list[Any] = Field(default_factory=list)


class AgentHttp422Example(BaseModel):
    """Documented FastAPI validation error envelope for query parameters."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "detail": [
                        {
                            "loc": ["query", "rerank_top_k"],
                            "msg": "ensure this value is greater than or equal to 1",
                            "type": "greater_than_equal",
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["query", "question"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["query", "tag_match_mode"],
                            "msg": "string does not match pattern",
                            "type": "value_error.str.regex",
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["body"],
                            "msg": "JSON decode error",
                            "type": "value_error.jsondecode",
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["query", "rerank_top_k"],
                            "msg": "ensure this value is less than or equal to 50",
                            "type": "less_than_equal",
                        }
                    ]
                },
            ]
        },
    )

    detail: list[dict[str, Any]] = Field(
        ...,
        description="Validation issues (``loc`` / ``msg`` / ``type`` per FastAPI).",
        examples=[
            [
                {
                    "loc": ["query", "rerank_top_k"],
                    "msg": "ensure this value is greater than or equal to 1",
                    "type": "greater_than_equal",
                }
            ]
        ],
    )


class AgentAskJsonResponse(BaseModel):
    """Typical successful JSON body for ``GET /ask`` (extra keys preserved)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "answer": "Nearby clinics include Eastside Community Health Center...",
                    "thread_id": "default",
                    "response_time_ms": 842,
                    "sources": [],
                    "latency_breakdown": None,
                },
                {
                    "answer": "The pantry is open Tuesdays 10am–2pm.",
                    "thread_id": "food-1",
                    "response_time_ms": 500,
                    "sources": [{"url": "https://food.example"}],
                    "latency_breakdown": {"llm_ms": 400},
                },
                {
                    "answer": "Bring photo ID and proof of income.",
                    "thread_id": "wic-2",
                    "response_time_ms": 1200,
                    "sources": [],
                    "latency_breakdown": {"retrieval_ms": 200, "llm_ms": 900},
                },
                {
                    "answer": "Cooling centers include Main Library this weekend.",
                    "thread_id": "heat-3",
                    "response_time_ms": 2000,
                    "sources": [{"url": "https://city.gov/heat", "title": "Heat"}],
                    "latency_breakdown": None,
                },
                {
                    "answer": "Short summary of tenant rights…",
                    "thread_id": "default",
                    "response_time_ms": 300,
                    "sources": [],
                    "latency_breakdown": {},
                },
            ]
        },
    )

    answer: str = Field(
        ...,
        examples=["Nearby clinics include Eastside Community Health Center..."],
    )
    thread_id: str = Field(default="default", examples=["default"])
    response_time_ms: int = Field(default=0, ge=0, examples=[842])
    sources: list[dict[str, Any]] = Field(default_factory=list)
    latency_breakdown: dict[str, Any] | None = Field(
        default=None,
        description="Optional retrieval / LLM timing breakdown.",
    )


class AgentTestDbSearchResponse(BaseModel):
    """``GET /test-db-search`` — diagnostic payload (shape varies by branch)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {"status": "success", "hits": 3},
                {"status": "no_results", "hits": 0},
                {"status": "error", "detail": "connection refused"},
                {"status": "success", "hits": 1, "took_ms": 12},
                {"status": "success", "hits": 50, "truncated": True},
            ]
        },
    )

    status: str | None = Field(
        default=None,
        description="success | no_results | error | omitted for early error dicts.",
        examples=["success"],
    )


class AgentDbInfoResponse(BaseModel):
    """``GET /db-info`` — database inspection payload."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {"status": "success", "tables": ["chunks", "sources"]},
                {"status": "error", "detail": "permission denied"},
                {"status": "success", "version": "15"},
                {"status": "success", "pool_size": 5},
                {"status": "degraded", "lag_ms": 200},
            ]
        },
    )

    status: str | None = Field(default=None, examples=["success"])


class ModelSelectionPostResponse(BaseModel):
    """``POST /model-selection`` success body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "current": {
                        "provider": "ollama",
                        "model": "gemma3",
                        "locked": False,
                    },
                },
                {
                    "status": "ok",
                    "current": {"provider": "ollama", "model": None, "locked": False},
                },
                {
                    "status": "ok",
                    "current": {
                        "provider": "ollama",
                        "model": "mistral",
                        "locked": False,
                    },
                },
                {
                    "status": "ok",
                    "current": {
                        "provider": "ollama",
                        "model": "gemma3",
                        "locked": True,
                    },
                },
                {
                    "status": "ok",
                    "current": {
                        "provider": "ollama",
                        "model": "phi3:mini",
                        "locked": False,
                    },
                },
            ]
        }
    )

    status: str = Field(default="ok", examples=["ok"])
    current: dict[str, Any] = Field(
        default_factory=dict,
        description="Persisted selection after update.",
    )


_AGENT_ASK_OPENAPI_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Missing ``question`` / ``query`` or empty value.",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                }
            }
        },
    },
    422: {
        "description": "Invalid query parameters (for example ``rerank_top_k`` out of range).",
        "model": AgentHttp422Example,
    },
    500: {"description": "Unhandled server error."},
}

_AGENT_STREAM_OPENAPI_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: _AGENT_ASK_OPENAPI_RESPONSES[400],
    422: {"description": "Invalid query parameters.", "model": AgentHttp422Example},
}

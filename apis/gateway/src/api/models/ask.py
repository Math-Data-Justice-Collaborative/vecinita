"""Gateway models — Q&A."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Q&A Models
# ============================================================================


class SourceCitation(BaseModel):
    """Source document cited in Q&A response."""

    url: str = Field(
        ..., description="Source document URL", examples=["https://example.com/docs/ml-guide"]
    )
    title: str | None = Field(
        default=None, description="Document title", examples=["Machine Learning Guide"]
    )
    chunk_id: str | None = Field(
        default=None, description="Chunk ID from vector store", examples=["chunk-456"]
    )
    relevance: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Vector similarity score (0-1, higher=more relevant)",
        examples=[0.95],
    )
    excerpt: str | None = Field(
        default=None,
        description="Relevant text excerpt from source",
        examples=["Machine learning is a branch of artificial intelligence..."],
    )


class AskQuestionRequest(BaseModel):
    """Request for Q&A query (GET /api/ask/)."""

    question: str = Field(
        ..., description="User's question to answer", examples=["What is machine learning?"]
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread ID for maintaining context across messages",
        examples=["conv-session-abc123xyz"],
    )
    lang: str | None = Field(
        default=None,
        description="Language code (es=Spanish, en=English). Auto-detected from question if omitted.",
        examples=["en"],
        pattern="^(es|en)?$",
    )
    provider: str | None = Field(
        default=None,
        description="Override local LLM provider (only ollama/local is supported)",
        examples=["ollama"],
    )
    model: str | None = Field(
        default=None,
        description="Override local LLM model name",
        examples=["gemma3"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What is vector embeddings?",
                    "thread_id": "conv-session-user-123",
                    "lang": "en",
                    "provider": "ollama",
                    "model": "gemma3",
                },
                {
                    "question": "¿Dónde solicito vouchers de vivienda?",
                    "thread_id": None,
                    "lang": "es",
                    "provider": None,
                    "model": None,
                },
                {
                    "question": "List three documents needed for WIC enrollment.",
                    "thread_id": "thread-wic-001",
                    "lang": "en",
                    "provider": "ollama",
                    "model": None,
                },
                {
                    "question": "Nearest cooling center open this weekend?",
                    "thread_id": None,
                    "lang": None,
                    "provider": None,
                    "model": "gemma3",
                },
                {
                    "question": "Explain good cause eviction in plain language.",
                    "thread_id": "legal-followup-7",
                    "lang": "en",
                    "provider": "ollama",
                    "model": "gemma3",
                },
            ],
            "example": {
                "question": "What is vector embeddings?",
                "thread_id": "conv-session-user-123",
                "lang": "en",
                "provider": "ollama",
                "model": "gemma3",
            },
        }
    )


class AskQuestionResponse(BaseModel):
    """Response to Q&A query (GET /api/ask/)."""

    question: str = Field(
        ..., description="Original user question", examples=["What is machine learning?"]
    )
    answer: str = Field(
        ...,
        description="Generated answer based on vector search results",
        examples=[
            "Machine learning is a branch of artificial intelligence that enables systems to learn and improve from experience..."
        ],
    )
    sources: list[SourceCitation] = Field(
        default_factory=list, description="List of source documents cited in the answer"
    )
    language: str = Field(..., description="Detected/used language code", examples=["en"])
    model: str = Field(
        ..., description="LLM model used to generate answer", examples=["llama-3.1-8b-instant"]
    )
    response_time_ms: int | None = Field(
        default=None, description="Total response time in milliseconds", examples=[2340]
    )
    token_usage: dict[str, int] | None = Field(
        default=None,
        description="Token usage breakdown (prompt_tokens, completion_tokens, total_tokens)",
        examples=[{"prompt_tokens": 512, "completion_tokens": 256, "total_tokens": 768}],
    )
    latency_breakdown: dict[str, Any] | None = Field(
        default=None, description="Optional stage-level latency metrics emitted by backend services"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What is machine learning?",
                    "answer": (
                        "Machine learning is a subset of AI that enables systems to learn..."
                    ),
                    "sources": [
                        {
                            "url": "https://example.com/ml-basics",
                            "title": "ML Basics",
                            "chunk_id": "chunk-001",
                            "relevance": 0.98,
                            "excerpt": "Machine learning enables systems to learn...",
                        }
                    ],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 2340,
                    "token_usage": {
                        "prompt_tokens": 512,
                        "completion_tokens": 256,
                        "total_tokens": 768,
                    },
                    "latency_breakdown": {
                        "retrieval_invoke_ms": 180,
                        "llm_ms": 1320,
                        "db_search": {
                            "embedding_ms": 54,
                            "retrieval_ms": 102,
                            "rerank_ms": 8,
                            "total_ms": 168,
                        },
                    },
                },
                {
                    "question": "Where is the nearest food pantry?",
                    "answer": "The Eastside pantry is open Tuesdays 10–2.",
                    "sources": [],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 1200,
                    "token_usage": None,
                    "latency_breakdown": None,
                },
                {
                    "question": "¿Cómo solicito vouchers de vivienda?",
                    "answer": "Puede iniciar la solicitud en la página del ayuntamiento.",
                    "sources": [
                        {
                            "url": "https://city.gov/housing",
                            "title": "Vivienda",
                            "chunk_id": "chunk-es-1",
                            "relevance": 0.88,
                            "excerpt": "Solicitud en línea disponible...",
                        }
                    ],
                    "language": "es",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 3100,
                    "token_usage": {
                        "prompt_tokens": 400,
                        "completion_tokens": 200,
                        "total_tokens": 600,
                    },
                    "latency_breakdown": {"llm_ms": 2100},
                },
                {
                    "question": "List WIC documents",
                    "answer": "ID, income proof, and residency proof are typical.",
                    "sources": [
                        {
                            "url": "https://health.example/wic",
                            "title": "WIC",
                            "chunk_id": "c2",
                            "relevance": 0.77,
                            "excerpt": "Bring photo ID...",
                        }
                    ],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 900,
                    "token_usage": {
                        "prompt_tokens": 200,
                        "completion_tokens": 120,
                        "total_tokens": 320,
                    },
                    "latency_breakdown": None,
                },
                {
                    "question": "Cooling centers this weekend?",
                    "answer": "Libraries act as cooling sites Sat–Sun per city alert.",
                    "sources": [
                        {
                            "url": "https://city.gov/heat",
                            "title": "Heat safety",
                            "chunk_id": "c3",
                            "relevance": 0.9,
                            "excerpt": "Libraries open extended hours...",
                        }
                    ],
                    "language": "en",
                    "model": "llama-3.1-8b-instant",
                    "response_time_ms": 1500,
                    "token_usage": {
                        "prompt_tokens": 300,
                        "completion_tokens": 150,
                        "total_tokens": 450,
                    },
                    "latency_breakdown": {"retrieval_invoke_ms": 200, "llm_ms": 900},
                },
            ],
            "example": {
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of AI that enables systems to learn and improve from experience...",
                "sources": [
                    {
                        "url": "https://example.com/ml-basics",
                        "title": "ML Basics",
                        "chunk_id": "chunk-001",
                        "relevance": 0.98,
                        "excerpt": "Machine learning enables systems to learn...",
                    }
                ],
                "language": "en",
                "model": "llama-3.1-8b-instant",
                "response_time_ms": 2340,
                "token_usage": {
                    "prompt_tokens": 512,
                    "completion_tokens": 256,
                    "total_tokens": 768,
                },
                "latency_breakdown": {
                    "retrieval_invoke_ms": 180,
                    "llm_ms": 1320,
                    "db_search": {
                        "embedding_ms": 54,
                        "retrieval_ms": 102,
                        "rerank_ms": 8,
                        "total_ms": 168,
                    },
                },
            },
        }
    )


class StreamEventType(str, Enum):
    """Server-Sent Event types for streaming Q&A."""

    THINKING = "thinking"
    TOOL_EVENT = "tool_event"
    COMPLETE = "complete"
    CLARIFICATION = "clarification"
    ERROR = "error"


class ThinkingEvent(BaseModel):
    """Streaming event: intermediate thinking step (GET /api/ask/stream)."""

    type: str = Field(default="thinking", description="Event type identifier")
    message: str = Field(
        ...,
        description="Thinking status message",
        examples=[
            "The question asks about vector embeddings. I need to search for relevant docs..."
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"type": "thinking", "message": "Searching local resources..."},
                {"type": "thinking", "message": "Planning retrieval with tag filter housing."},
                {"type": "thinking", "message": "Embedding query for vector search."},
                {"type": "thinking", "message": "Reranking top chunks for answer synthesis."},
                {"type": "thinking", "message": "Drafting final answer from citations."},
            ],
            "example": {"type": "thinking", "message": "Searching local resources..."},
        }
    )


class CompleteEvent(BaseModel):
    """Streaming event: complete answer with sources (GET /api/ask/stream)."""

    type: str = Field(default="complete", description="Event type identifier")
    answer: str = Field(..., description="Final complete answer")
    sources: list[SourceCitation] = Field(default_factory=list, description="Source citations")
    suggested_questions: list[str] = Field(
        default_factory=list,
        description="Optional follow-up questions to guide the next user turn",
    )
    thread_id: str | None = Field(default=None, description="Conversation thread identifier")
    plan: str = Field(default="", description="Optional compact plan generated by agent")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "complete",
                    "answer": "Vector embeddings are numerical representations of text...",
                    "sources": [{"url": "https://example.com/embeddings", "relevance": 0.95}],
                    "suggested_questions": [
                        "Can you summarize that in 3 key points?",
                        "What should I do first?",
                    ],
                    "thread_id": "thread-123",
                    "plan": "",
                },
                {
                    "type": "complete",
                    "answer": "The pantry is open Tuesdays 10am–2pm.",
                    "sources": [],
                    "suggested_questions": [],
                    "thread_id": None,
                    "plan": "",
                },
                {
                    "type": "complete",
                    "answer": "Bring ID, pay stubs, and a utility bill.",
                    "sources": [{"url": "https://health.example/wic", "relevance": 0.8}],
                    "suggested_questions": ["What if I lack a utility bill?"],
                    "thread_id": "wic-1",
                    "plan": "answer-from-docs",
                },
                {
                    "type": "complete",
                    "answer": "Cooling centers include Main Library this weekend.",
                    "sources": [
                        {"url": "https://city.gov/heat", "relevance": 0.91},
                        {"url": "https://library.example/hours", "relevance": 0.7},
                    ],
                    "suggested_questions": ["Hours on Sunday?", "ADA access?"],
                    "thread_id": "heat-9",
                    "plan": "",
                },
                {
                    "type": "complete",
                    "answer": "Short yes: you likely qualify if income is under the limit.",
                    "sources": [{"url": "https://benefits.example/snap", "relevance": 0.66}],
                    "suggested_questions": [],
                    "thread_id": "default",
                    "plan": "compact",
                },
            ],
            "example": {
                "type": "complete",
                "answer": "Vector embeddings are numerical representations of text...",
                "sources": [{"url": "https://example.com/embeddings", "relevance": 0.95}],
                "suggested_questions": [
                    "Can you summarize that in 3 key points?",
                    "What should I do first?",
                ],
                "thread_id": "thread-123",
                "plan": "",
            },
        }
    )


class ToolEvent(BaseModel):
    """Streaming event: compact tool lifecycle update (GET /api/ask/stream)."""

    type: str = Field(default="tool_event", description="Event type identifier")
    phase: str = Field(default="result", description="Lifecycle phase: start|result|error")
    tool: str = Field(..., description="Tool name", examples=["db_search"])
    message: str = Field(..., description="Compact human-readable summary")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "tool_event",
                    "phase": "result",
                    "tool": "db_search",
                    "message": "db_search returned 5 relevant chunks.",
                },
                {
                    "type": "tool_event",
                    "phase": "start",
                    "tool": "db_search",
                    "message": "Starting vector retrieval.",
                },
                {
                    "type": "tool_event",
                    "phase": "error",
                    "tool": "db_search",
                    "message": "db_search timed out after 8s.",
                },
                {
                    "type": "tool_event",
                    "phase": "result",
                    "tool": "web_search",
                    "message": "web_search returned 3 snippets.",
                },
                {
                    "type": "tool_event",
                    "phase": "result",
                    "tool": "rerank",
                    "message": "rerank kept top 8 chunks.",
                },
            ],
            "example": {
                "type": "tool_event",
                "phase": "result",
                "tool": "db_search",
                "message": "db_search returned 5 relevant chunks.",
            },
        }
    )


class ClarificationEvent(BaseModel):
    """Streaming event: request for clarification (GET /api/ask/stream)."""

    type: str = Field(default="clarification", description="Event type identifier")
    message: str | None = Field(
        default=None,
        description="Primary clarification prompt",
        examples=["Do you want information for renters or homeowners?"],
    )
    questions: list[str] = Field(
        default_factory=list,
        description="Optional list of clarifying questions",
        examples=[
            [
                "Are you asking about embeddings in NLP or general vector embeddings?",
                "Do you want implementation details or conceptual understanding?",
            ]
        ],
    )
    context: str | None = Field(
        default=None, description="Optional context explaining why clarification is needed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "clarification",
                    "message": "Can you share your neighborhood?",
                    "questions": [
                        "Are you asking about embeddings in NLP or general vector embeddings?",
                        "Do you want implementation details or conceptual understanding?",
                    ],
                    "context": "Initial search returned no localized results",
                },
                {
                    "type": "clarification",
                    "message": "Which county?",
                    "questions": ["Alameda?", "Contra Costa?", "San Francisco?"],
                    "context": "Benefits rules vary by county",
                },
                {
                    "type": "clarification",
                    "message": None,
                    "questions": ["Renters or homeowners?"],
                    "context": None,
                },
                {
                    "type": "clarification",
                    "message": "Language preference?",
                    "questions": ["English", "Spanish"],
                    "context": "Detected mixed-language query",
                },
                {
                    "type": "clarification",
                    "message": "Time window?",
                    "questions": ["This week", "This month", "Any"],
                    "context": "Event listings are date-sensitive",
                },
            ],
            "example": {
                "type": "clarification",
                "message": "Can you share your neighborhood?",
                "questions": [
                    "Are you asking about embeddings in NLP or general vector embeddings?",
                    "Do you want implementation details or conceptual understanding?",
                ],
                "context": "Initial search returned no localized results",
            },
        }
    )


class StreamErrorEvent(BaseModel):
    """Streaming event: error occurred (GET /api/ask/stream)."""

    type: str = Field(default="error", description="Event type identifier")
    message: str = Field(
        ..., description="Error message", examples=["No relevant documents found for this question"]
    )
    code: str | None = Field(
        default=None, description="Machine-readable error code", examples=["NO_CONTEXT"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "error",
                    "message": "No relevant documents found for this question",
                    "code": "NO_CONTEXT",
                },
                {
                    "type": "error",
                    "message": "Upstream LLM unavailable",
                    "code": "LLM_UNAVAILABLE",
                },
                {
                    "type": "error",
                    "message": "Rate limit exceeded",
                    "code": "RATE_LIMIT",
                },
                {
                    "type": "error",
                    "message": "Embedding service error",
                    "code": "EMBED_ERROR",
                },
                {"type": "error", "message": "Generic failure", "code": None},
            ],
            "example": {
                "type": "error",
                "message": "No relevant documents found for this question",
                "code": "NO_CONTEXT",
            },
        }
    )


class AskConfigResponse(BaseModel):
    """Response with Q&A service configuration (GET /api/ask/config)."""

    supported_languages: list[str] = Field(
        default_factory=lambda: ["en", "es"],
        description="List of supported language codes",
        examples=[["en", "es"]],
    )
    default_language: str = Field(
        default="en", description="Default language for questions", examples=["en"]
    )
    default_provider: str = Field(
        default="ollama", description="Default local LLM provider", examples=["ollama"]
    )
    available_models: list[dict[str, Any]] = Field(
        default_factory=list, description="List of available LLM models with specs"
    )
    features: dict[str, bool] = Field(
        default_factory=lambda: {
            "streaming_enabled": True,
            "thread_context": True,
            "model_override": True,
            "web_search": False,
        },
        description="Feature availability flags",
    )
    limits: dict[str, int] = Field(
        default_factory=lambda: {
            "max_question_length": 4000,
            "max_response_tokens": 2048,
            "request_timeout_seconds": 30,
        },
        description="Request/response limits",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "gemma3",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        }
                    ],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 4000,
                        "max_response_tokens": 2048,
                        "request_timeout_seconds": 30,
                    },
                },
                {
                    "supported_languages": ["en"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": False,
                        "model_override": False,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 2000,
                        "max_response_tokens": 1024,
                        "request_timeout_seconds": 20,
                    },
                },
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "es",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "llama3.1:70b",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        }
                    ],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": True,
                    },
                    "limits": {
                        "max_question_length": 8000,
                        "max_response_tokens": 4096,
                        "request_timeout_seconds": 60,
                    },
                },
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "gemma3",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        },
                        {
                            "provider": "ollama",
                            "name": "mistral",
                            "context_window": 8192,
                            "cost_per_1k_tokens": 0.0,
                        },
                    ],
                    "features": {
                        "streaming_enabled": False,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 4000,
                        "max_response_tokens": 2048,
                        "request_timeout_seconds": 45,
                    },
                },
                {
                    "supported_languages": ["en", "es"],
                    "default_language": "en",
                    "default_provider": "ollama",
                    "available_models": [
                        {
                            "provider": "ollama",
                            "name": "phi3:mini",
                            "context_window": 4096,
                            "cost_per_1k_tokens": 0.0,
                        }
                    ],
                    "features": {
                        "streaming_enabled": True,
                        "thread_context": True,
                        "model_override": True,
                        "web_search": False,
                    },
                    "limits": {
                        "max_question_length": 3000,
                        "max_response_tokens": 512,
                        "request_timeout_seconds": 15,
                    },
                },
            ],
            "example": {
                "supported_languages": ["en", "es"],
                "default_language": "en",
                "default_provider": "ollama",
                "available_models": [
                    {
                        "provider": "ollama",
                        "name": "gemma3",
                        "context_window": 8192,
                        "cost_per_1k_tokens": 0.0,
                    }
                ],
                "features": {
                    "streaming_enabled": True,
                    "thread_context": True,
                    "model_override": True,
                    "web_search": False,
                },
                "limits": {
                    "max_question_length": 4000,
                    "max_response_tokens": 2048,
                    "request_timeout_seconds": 30,
                },
            },
        }
    )


# Backward compatibility aliases
AskRequest = AskQuestionRequest
AskResponse = AskQuestionResponse

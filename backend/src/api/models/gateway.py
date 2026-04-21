"""Gateway models — health, config, integrations, documents."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# Gateway Health & Config Models
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Response from health check endpoint (GET /health)."""

    status: str = Field(..., description="Overall health status", examples=["ok"])
    agent_service: str | None = Field(
        default=None, description="Agent service health status", examples=["ok"]
    )
    embedding_service: str | None = Field(
        default=None, description="Embedding service health status", examples=["ok"]
    )
    database: str | None = Field(
        default=None, description="Database health status", examples=["ok"]
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "ok",
                    "agent_service": "ok",
                    "embedding_service": "ok",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "status": "degraded",
                    "agent_service": "ok",
                    "embedding_service": "timeout",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:31:00Z",
                },
                {
                    "status": "error",
                    "agent_service": "error",
                    "embedding_service": "ok",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:32:00Z",
                },
                {
                    "status": "ok",
                    "agent_service": None,
                    "embedding_service": "ok",
                    "database": "ok",
                    "timestamp": "2024-02-09T10:33:00Z",
                },
                {
                    "status": "ok",
                    "agent_service": "ok",
                    "embedding_service": None,
                    "database": "slow",
                    "timestamp": "2024-02-09T10:34:00Z",
                },
            ],
            "example": {
                "status": "ok",
                "agent_service": "ok",
                "embedding_service": "ok",
                "database": "ok",
                "timestamp": "2024-02-09T10:30:00Z",
            },
        }
    )


class IntegrationComponentStatus(BaseModel):
    """Health snapshot for a single dependency or integration."""

    status: str = Field(..., description="Integration status", examples=["ok"])
    configured: bool = Field(
        ..., description="Whether the integration is configured for this runtime", examples=[True]
    )
    critical: bool = Field(
        default=False,
        description="Whether this integration affects the overall service status",
        examples=[True],
    )
    endpoint: str | None = Field(
        default=None,
        description="Resolved upstream endpoint or host used for the check",
        examples=["http://vecinita-agent:10000"],
    )
    health_url: str | None = Field(
        default=None,
        description="Health URL probed for the integration when applicable",
        examples=["http://vecinita-agent:10000/health"],
    )
    response_time_ms: int | None = Field(
        default=None,
        description="Probe latency in milliseconds when available",
        examples=[42],
    )
    detail: str | None = Field(
        default=None,
        description="Operator-friendly detail message for the current status",
        examples=["health endpoint returned 200"],
    )


class IntegrationsStatusResponse(BaseModel):
    """Aggregated gateway and dependency health for deploy checks and operators."""

    status: str = Field(..., description="Overall gateway integration status", examples=["ok"])
    gateway: IntegrationComponentStatus = Field(
        ..., description="Gateway service status for the current process"
    )
    components: dict[str, IntegrationComponentStatus] = Field(
        default_factory=dict,
        description="Per-integration health snapshots keyed by component name",
    )
    active_integrations: list[str] = Field(
        default_factory=list,
        description="Configured integrations currently reporting healthy status",
        examples=[["agent", "embedding_service", "database"]],
    )
    degraded_integrations: list[str] = Field(
        default_factory=list,
        description="Configured integrations currently degraded or unavailable",
        examples=[["scraper"]],
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "degraded",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "gateway process is running",
                    },
                    "components": {
                        "agent": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "http://vecinita-agent:10000",
                            "health_url": "http://vecinita-agent:10000/health",
                            "response_time_ms": 47,
                            "detail": "health endpoint returned 200",
                        },
                        "database": {
                            "status": "error",
                            "configured": True,
                            "critical": True,
                            "endpoint": "vecinita-postgres:5432",
                            "health_url": None,
                            "response_time_ms": 2000,
                            "detail": "database socket probe failed",
                        },
                    },
                    "active_integrations": ["agent"],
                    "degraded_integrations": ["database"],
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "status": "ok",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {
                        "agent": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "http://agent:10000",
                            "health_url": "http://agent:10000/health",
                            "response_time_ms": 30,
                            "detail": "ok",
                        },
                        "embedding_service": {
                            "status": "ok",
                            "configured": True,
                            "critical": False,
                            "endpoint": "http://embed:8000",
                            "health_url": "http://embed:8000/health",
                            "response_time_ms": 22,
                            "detail": "ok",
                        },
                    },
                    "active_integrations": ["agent", "embedding_service"],
                    "degraded_integrations": [],
                    "timestamp": "2024-02-09T11:00:00Z",
                },
                {
                    "status": "degraded",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {
                        "scraper": {
                            "status": "error",
                            "configured": True,
                            "critical": False,
                            "endpoint": "http://scraper:9000",
                            "health_url": None,
                            "response_time_ms": None,
                            "detail": "connection refused",
                        }
                    },
                    "active_integrations": [],
                    "degraded_integrations": ["scraper"],
                    "timestamp": "2024-02-09T12:00:00Z",
                },
                {
                    "status": "ok",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {},
                    "active_integrations": [],
                    "degraded_integrations": [],
                    "timestamp": "2024-02-09T13:00:00Z",
                },
                {
                    "status": "degraded",
                    "gateway": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-gateway",
                        "health_url": None,
                        "response_time_ms": 0,
                        "detail": "ok",
                    },
                    "components": {
                        "agent": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "http://agent:10000",
                            "health_url": "http://agent:10000/health",
                            "response_time_ms": 120,
                            "detail": "slow but up",
                        },
                        "database": {
                            "status": "ok",
                            "configured": True,
                            "critical": True,
                            "endpoint": "postgres:5432",
                            "health_url": None,
                            "response_time_ms": 400,
                            "detail": "slow queries",
                        },
                    },
                    "active_integrations": ["agent", "database"],
                    "degraded_integrations": [],
                    "timestamp": "2024-02-09T14:00:00Z",
                },
            ],
            "example": {
                "status": "degraded",
                "gateway": {
                    "status": "ok",
                    "configured": True,
                    "critical": True,
                    "endpoint": "vecinita-gateway",
                    "health_url": None,
                    "response_time_ms": 0,
                    "detail": "gateway process is running",
                },
                "components": {
                    "agent": {
                        "status": "ok",
                        "configured": True,
                        "critical": True,
                        "endpoint": "http://vecinita-agent:10000",
                        "health_url": "http://vecinita-agent:10000/health",
                        "response_time_ms": 47,
                        "detail": "health endpoint returned 200",
                    },
                    "database": {
                        "status": "error",
                        "configured": True,
                        "critical": True,
                        "endpoint": "vecinita-postgres:5432",
                        "health_url": None,
                        "response_time_ms": 2000,
                        "detail": "database socket probe failed",
                    },
                },
                "active_integrations": ["agent"],
                "degraded_integrations": ["database"],
                "timestamp": "2024-02-09T10:30:00Z",
            },
        }
    )


class EndpointInfo(BaseModel):
    """Information about a single endpoint."""

    method: str = Field(..., description="HTTP method", examples=["GET"])
    path: str = Field(..., description="Endpoint path", examples=["/api/ask/"])
    description: str = Field(
        ...,
        description="Brief endpoint description",
        examples=["Ask a question and get an answer with sources"],
    )
    authentication: bool = Field(
        default=False, description="Whether endpoint requires authentication", examples=[False]
    )


class GatewayInfoResponse(BaseModel):
    """Response with service information (GET /)."""

    service: str = Field(default="Vecinita Unified API Gateway", description="Service name")
    version: str = Field(default="1.0.0", description="API version", examples=["1.0.0"])
    status: str = Field(
        default="operational", description="Service status", examples=["operational"]
    )
    endpoints: dict[str, list[EndpointInfo]] = Field(
        default_factory=dict, description="Endpoints organized by category"
    )
    environment: dict[str, str] = Field(
        default_factory=dict,
        description="Environment info (deployed_at, region, etc.)",
        examples=[{"deployed_at": "2024-02-09T10:00:00Z", "region": "us-east-1"}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "status": "operational",
                    "endpoints": {
                        "Q&A": [
                            {
                                "method": "GET",
                                "path": "/api/ask/",
                                "description": "Ask a question",
                                "authentication": False,
                            }
                        ]
                    },
                    "environment": {
                        "deployed_at": "2024-02-09T10:00:00Z",
                        "region": "us-east-1",
                    },
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.1",
                    "status": "operational",
                    "endpoints": {"Scrape": []},
                    "environment": {"deployed_at": "2024-02-10T08:00:00Z", "region": "us-west-2"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "status": "maintenance",
                    "endpoints": {},
                    "environment": {"deployed_at": "2024-02-01T00:00:00Z", "region": "eu-west-1"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "0.9.0",
                    "status": "operational",
                    "endpoints": {
                        "Docs": [
                            {
                                "method": "GET",
                                "path": "/docs",
                                "description": "Swagger",
                                "authentication": False,
                            }
                        ]
                    },
                    "environment": {"deployed_at": "2024-01-15T00:00:00Z", "region": "local"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "status": "operational",
                    "endpoints": {
                        "Embeddings": [
                            {
                                "method": "POST",
                                "path": "/api/embed/",
                                "description": "Embed text",
                                "authentication": True,
                            }
                        ]
                    },
                    "environment": {"deployed_at": "2024-02-09T12:00:00Z", "region": "staging"},
                },
            ],
            "example": {
                "service": "Vecinita Unified API Gateway",
                "version": "1.0.0",
                "status": "operational",
                "endpoints": {
                    "Q&A": [
                        {
                            "method": "GET",
                            "path": "/api/ask/",
                            "description": "Ask a question",
                            "authentication": False,
                        }
                    ]
                },
                "environment": {"deployed_at": "2024-02-09T10:00:00Z", "region": "us-east-1"},
            },
        }
    )


class GatewayConfigResponse(BaseModel):
    """Response with gateway configuration (GET /config)."""

    agent_url: str = Field(..., description="Agent service URL", examples=["http://localhost:8000"])
    embedding_service_url: str = Field(
        ...,
        description="Embedding service URL",
        examples=["https://vecinita--vecinita-embedding-web-app.modal.run"],
    )
    database_url: str | None = Field(default=None, description="Database URL (masked for security)")
    max_urls_per_request: int = Field(
        ..., description="Max URLs per scrape request", examples=[100]
    )
    job_retention_hours: int = Field(
        ..., description="Job history retention period in hours", examples=[24]
    )
    embedding_model: str = Field(
        ...,
        description="Default embedding model",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    auth_enabled: bool = Field(
        default=False, description="Whether authentication is required", examples=[False]
    )
    rate_limiting: dict[str, int] | None = Field(
        default=None,
        description="Rate limit configuration",
        examples=[{"requests_per_hour": 100, "tokens_per_day": 1000}],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent_url": "http://localhost:8000",
                    "embedding_service_url": (
                        "https://vecinita--vecinita-embedding-web-app.modal.run"
                    ),
                    "database_url": None,
                    "max_urls_per_request": 100,
                    "job_retention_hours": 24,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "auth_enabled": False,
                    "rate_limiting": {"requests_per_hour": 100, "tokens_per_day": 1000},
                },
                {
                    "agent_url": "http://vecinita-agent:10000",
                    "embedding_service_url": "http://embedding:8000",
                    "database_url": "postgresql://***@postgres:5432/db",
                    "max_urls_per_request": 50,
                    "job_retention_hours": 48,
                    "embedding_model": "BAAI/bge-small-en-v1.5",
                    "auth_enabled": True,
                    "rate_limiting": None,
                },
                {
                    "agent_url": "http://127.0.0.1:10000",
                    "embedding_service_url": "http://127.0.0.1:8001",
                    "database_url": None,
                    "max_urls_per_request": 10,
                    "job_retention_hours": 12,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "auth_enabled": False,
                    "rate_limiting": {"requests_per_hour": 1000, "tokens_per_day": 10000},
                },
                {
                    "agent_url": "https://agent.example",
                    "embedding_service_url": "https://embed.example",
                    "database_url": None,
                    "max_urls_per_request": 200,
                    "job_retention_hours": 72,
                    "embedding_model": "intfloat/e5-small-v2",
                    "auth_enabled": True,
                    "rate_limiting": {"requests_per_hour": 60, "tokens_per_day": 500},
                },
                {
                    "agent_url": "http://agent.internal",
                    "embedding_service_url": "http://embed.internal",
                    "database_url": None,
                    "max_urls_per_request": 100,
                    "job_retention_hours": 6,
                    "embedding_model": "sentence-transformers/all-mpnet-base-v2",
                    "auth_enabled": False,
                    "rate_limiting": {},
                },
            ],
            "example": {
                "agent_url": "http://localhost:8000",
                "embedding_service_url": "https://vecinita--vecinita-embedding-web-app.modal.run",
                "database_url": None,
                "max_urls_per_request": 100,
                "job_retention_hours": 24,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "auth_enabled": False,
                "rate_limiting": {"requests_per_hour": 100, "tokens_per_day": 1000},
            },
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type/message", examples=["Not Found"])
    detail: str | None = Field(
        default=None,
        description="Detailed error explanation",
        examples=["The requested resource was not found"],
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "Not Found",
                    "detail": "The requested resource was not found",
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "error": "Unauthorized",
                    "detail": "Invalid API key",
                    "timestamp": "2024-02-09T10:31:00Z",
                },
                {
                    "error": "Bad Gateway",
                    "detail": "Upstream agent timeout",
                    "timestamp": "2024-02-09T10:32:00Z",
                },
                {
                    "error": "Internal Server Error",
                    "detail": None,
                    "timestamp": "2024-02-09T10:33:00Z",
                },
                {
                    "error": "Service Unavailable",
                    "detail": "Embedding service overloaded",
                    "timestamp": "2024-02-09T10:34:00Z",
                },
            ],
            "example": {
                "error": "Not Found",
                "detail": "The requested resource was not found",
                "timestamp": "2024-02-09T10:30:00Z",
            },
        }
    )


class ValidationErrorResponse(BaseModel):
    """FastAPI ``HTTPException`` / request validation error shape (422)."""

    detail: list[dict[str, Any]] | str = Field(
        ...,
        description="Validation issues or error message payload.",
        examples=[
            [
                {
                    "loc": ["query", "question"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
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
                            "loc": ["body", "texts", 0],
                            "msg": "ensure this value has at least 1 characters",
                            "type": "value_error.any_str.min_length",
                        }
                    ]
                },
                {"detail": "Invalid authentication credentials"},
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
                            "loc": ["body", "urls"],
                            "msg": "ensure this value has at least 1 items",
                            "type": "value_error.list.min_items",
                        }
                    ]
                },
            ]
        }
    )


# ---------------------------------------------------------------------------
# Public documents dashboard (GET /api/v1/documents/*)
# ---------------------------------------------------------------------------

DOCUMENTS_DEFAULT_SOURCE_URL = "https://example.org/community-resource-guide"


class DocumentsOverviewQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/overview``."""

    tags: str | None = Field(
        default=None,
        description="Comma-separated tags used to filter the source list.",
        examples=["housing,permits"],
    )
    tag_match_mode: Literal["any", "all"] = Field(
        default="any",
        description="Tag match mode for source filtering.",
        examples=["any"],
    )
    include_test_data: bool = Field(
        default=False,
        description="Include test/e2e-tagged artifacts in results.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"tags": None, "tag_match_mode": "any", "include_test_data": False},
                {"tags": "housing,permits", "tag_match_mode": "any", "include_test_data": False},
                {"tags": "health,clinics", "tag_match_mode": "all", "include_test_data": False},
                {"tags": "food", "tag_match_mode": "any", "include_test_data": True},
                {
                    "tags": "legal,housing,tenants",
                    "tag_match_mode": "all",
                    "include_test_data": False,
                },
            ]
        }
    )


class DocumentsPreviewQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/preview``."""

    source_url: str = Field(
        ...,
        min_length=1,
        description="Source URL to preview.",
        examples=[DOCUMENTS_DEFAULT_SOURCE_URL],
    )
    limit: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of chunk excerpts to return.",
        examples=[3],
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                {"source_url": DOCUMENTS_DEFAULT_SOURCE_URL, "limit": 3},
                {"source_url": "https://city.gov/housing/guide", "limit": 1},
                {"source_url": "https://health.example/clinics", "limit": 5},
                {"source_url": "https://schools.example/enrollment", "limit": 10},
                {"source_url": "https://transit.example/schedules", "limit": 2},
            ]
        },
    )


class DocumentsDownloadUrlQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/download-url``."""

    source_url: str = Field(
        ...,
        min_length=1,
        description="Source URL to resolve download link for.",
        examples=[DOCUMENTS_DEFAULT_SOURCE_URL],
    )

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                {"source_url": DOCUMENTS_DEFAULT_SOURCE_URL},
                {"source_url": "https://city.gov/housing/forms.pdf"},
                {"source_url": "https://ngo.org/resources/handbook"},
                {"source_url": "https://library.example/community-directory"},
                {"source_url": "https://clinic.example/patient-info"},
            ]
        },
    )


class DocumentsChunkStatisticsQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/chunk-statistics``."""

    limit: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum domains to return.",
        examples=[20],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 20},
                {"limit": 5},
                {"limit": 50},
                {"limit": 1},
                {"limit": 200},
            ]
        }
    )


class DocumentsTagsQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/documents/tags``."""

    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of tags to return.",
        examples=[50],
    )
    query: str = Field(
        default="",
        description="Optional case-insensitive tag search substring.",
        examples=["health"],
    )
    locale: Literal["en", "es"] = Field(
        default="en",
        description="Locale for tag labels (en or es).",
        examples=["en"],
    )
    include_test_data: bool = Field(
        default=False,
        description="Include tags from test/e2e artifacts.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 100, "query": "", "locale": "en", "include_test_data": False},
                {"limit": 50, "query": "health", "locale": "en", "include_test_data": False},
                {"limit": 25, "query": "viv", "locale": "es", "include_test_data": False},
                {"limit": 200, "query": "housing", "locale": "en", "include_test_data": True},
                {"limit": 10, "query": "perm", "locale": "es", "include_test_data": True},
            ]
        }
    )


class PublicDocumentsSourceItem(BaseModel):
    """One merged public source row (fields vary by SQL path; extras preserved)."""

    model_config = ConfigDict(extra="allow")

    url: str = Field(default="", examples=[DOCUMENTS_DEFAULT_SOURCE_URL])
    domain: str | None = Field(default=None, examples=["example.org"])
    title: str | None = Field(default=None, examples=["Community resource guide"])
    total_chunks: int = Field(default=0, ge=0, examples=[12])


class DocumentsOverviewResponse(BaseModel):
    """``GET /api/v1/documents/overview`` JSON body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_chunks": 1200,
                    "unique_sources": 42,
                    "filtered": False,
                    "avg_chunk_size": 900,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [],
                },
                {
                    "total_chunks": 0,
                    "unique_sources": 0,
                    "filtered": False,
                    "avg_chunk_size": 0,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [],
                },
                {
                    "total_chunks": 500,
                    "unique_sources": 12,
                    "filtered": True,
                    "avg_chunk_size": 820,
                    "embedding_model": "BAAI/bge-small-en-v1.5",
                    "embedding_dimension": 384,
                    "sources": [
                        {
                            "url": "https://city.gov/housing",
                            "domain": "city.gov",
                            "title": "Housing portal",
                            "total_chunks": 80,
                        }
                    ],
                },
                {
                    "total_chunks": 10000,
                    "unique_sources": 200,
                    "filtered": False,
                    "avg_chunk_size": 950,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [
                        {
                            "url": DOCUMENTS_DEFAULT_SOURCE_URL,
                            "domain": "example.org",
                            "title": "Community resource guide",
                            "total_chunks": 12,
                        }
                    ],
                },
                {
                    "total_chunks": 300,
                    "unique_sources": 25,
                    "filtered": True,
                    "avg_chunk_size": 700,
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "embedding_dimension": 384,
                    "sources": [],
                },
            ]
        }
    )

    total_chunks: int = Field(..., ge=0, examples=[1200])
    unique_sources: int = Field(..., ge=0, examples=[42])
    filtered: bool = Field(..., examples=[False])
    avg_chunk_size: int = Field(..., ge=0, examples=[900])
    embedding_model: str = Field(
        ...,
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    embedding_dimension: int = Field(..., ge=1, examples=[384])
    sources: list[PublicDocumentsSourceItem] = Field(default_factory=list)


class DocumentsPreviewChunk(BaseModel):
    """One chunk excerpt in a preview response."""

    chunk_index: int = Field(..., ge=0, examples=[0])
    chunk_size: int = Field(..., ge=0, examples=[400])
    content_preview: str = Field(..., examples=["Excerpt of indexed text…"])
    document_title: str = Field(..., examples=["Community resource guide"])


class DocumentsPreviewResponse(BaseModel):
    """``GET /api/v1/documents/preview`` JSON body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_url": DOCUMENTS_DEFAULT_SOURCE_URL,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 120,
                            "content_preview": "Sample chunk text…",
                            "document_title": "Example document",
                        }
                    ],
                },
                {"source_url": "https://city.gov/guide", "chunks": []},
                {
                    "source_url": "https://health.example/wic",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 200,
                            "content_preview": "WIC intake steps…",
                            "document_title": "WIC FAQ",
                        },
                        {
                            "chunk_index": 1,
                            "chunk_size": 180,
                            "content_preview": "Bring photo ID…",
                            "document_title": "WIC FAQ",
                        },
                    ],
                },
                {
                    "source_url": "https://transit.example/routes",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 90,
                            "content_preview": "Route 14 schedule…",
                            "document_title": "Rider guide",
                        }
                    ],
                },
                {
                    "source_url": "https://schools.example/enroll",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "chunk_size": 400,
                            "content_preview": "Proof of residency…",
                            "document_title": "Enrollment",
                        }
                    ],
                },
            ]
        }
    )

    source_url: str = Field(..., examples=[DOCUMENTS_DEFAULT_SOURCE_URL])
    chunks: list[DocumentsPreviewChunk] = Field(default_factory=list)


class DocumentsDownloadUrlResponse(BaseModel):
    """``GET /api/v1/documents/download-url`` JSON body."""

    source_url: str = Field(..., examples=[DOCUMENTS_DEFAULT_SOURCE_URL])
    title: str = Field(..., examples=["Example document"])
    download_url: str | None = Field(default=None, examples=["https://cdn.example.org/file.pdf"])
    downloadable: bool = Field(..., examples=[True])
    message: str | None = Field(
        default=None,
        description="Present when the source has no downloadable artifact.",
        examples=["Source is URL-based and has no downloadable file"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_url": DOCUMENTS_DEFAULT_SOURCE_URL,
                    "title": "Example document",
                    "download_url": "https://cdn.example.org/file.pdf",
                    "downloadable": True,
                    "message": None,
                },
                {
                    "source_url": "https://city.gov/forms.pdf",
                    "title": "Municipal forms",
                    "download_url": "https://cdn.city.gov/forms.pdf",
                    "downloadable": True,
                    "message": None,
                },
                {
                    "source_url": "https://news.example/article",
                    "title": "Article",
                    "download_url": None,
                    "downloadable": False,
                    "message": "Source is URL-based and has no downloadable file",
                },
                {
                    "source_url": "https://library.example/dir",
                    "title": "Directory listing",
                    "download_url": None,
                    "downloadable": False,
                    "message": "No single downloadable artifact",
                },
                {
                    "source_url": "https://clinic.example/handbook",
                    "title": "Patient handbook",
                    "download_url": "https://storage.clinic.example/hb.pdf",
                    "downloadable": True,
                    "message": None,
                },
            ]
        }
    )


class DocumentsChunkStatisticsRow(BaseModel):
    """One domain aggregate from chunk statistics."""

    model_config = ConfigDict(extra="allow")

    source_domain: str = Field(default="unknown", examples=["example.org"])
    chunk_count: int = Field(default=0, ge=0, examples=[100])
    avg_chunk_size: int = Field(default=0, ge=0, examples=[512])
    total_size: int = Field(default=0, ge=0, examples=[51200])
    document_count: int = Field(default=0, ge=0, examples=[5])


class DocumentsChunkStatisticsResponse(BaseModel):
    """``GET /api/v1/documents/chunk-statistics`` JSON body."""

    rows: list[DocumentsChunkStatisticsRow] = Field(default_factory=list)
    total: int = Field(..., ge=0, examples=[1])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"rows": [], "total": 0},
                {
                    "rows": [
                        {
                            "source_domain": "example.org",
                            "chunk_count": 100,
                            "avg_chunk_size": 512,
                            "total_size": 51200,
                            "document_count": 5,
                        }
                    ],
                    "total": 1,
                },
                {
                    "rows": [
                        {
                            "source_domain": "city.gov",
                            "chunk_count": 200,
                            "avg_chunk_size": 600,
                            "total_size": 120000,
                            "document_count": 10,
                        },
                        {
                            "source_domain": "health.example",
                            "chunk_count": 50,
                            "avg_chunk_size": 400,
                            "total_size": 20000,
                            "document_count": 3,
                        },
                    ],
                    "total": 2,
                },
                {
                    "rows": [
                        {
                            "source_domain": "unknown",
                            "chunk_count": 0,
                            "avg_chunk_size": 0,
                            "total_size": 0,
                            "document_count": 0,
                        }
                    ],
                    "total": 1,
                },
                {
                    "rows": [
                        {
                            "source_domain": "schools.example",
                            "chunk_count": 1200,
                            "avg_chunk_size": 900,
                            "total_size": 1080000,
                            "document_count": 40,
                        }
                    ],
                    "total": 1,
                },
            ]
        }
    )


class DocumentsTagRow(BaseModel):
    """One tag inventory row."""

    tag: str = Field(..., examples=["housing"])
    label: str = Field(..., examples=["Housing"])
    locale: Literal["en", "es"] = Field(..., examples=["en"])
    resource_count: int = Field(..., ge=0, examples=[3])
    chunk_count: int = Field(..., ge=0, examples=[40])
    source_count: int = Field(..., ge=0, examples=[3])


class DocumentsTagsResponse(BaseModel):
    """``GET /api/v1/documents/tags`` JSON body."""

    tags: list[DocumentsTagRow] = Field(default_factory=list)
    tag_counts: dict[str, int] = Field(
        default_factory=dict,
        examples=[{"housing": 3}],
    )
    locale: Literal["en", "es"] = Field(..., examples=["en"])
    total: int = Field(..., ge=0, examples=[1])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tags": [
                        {
                            "tag": "housing",
                            "label": "Housing",
                            "locale": "en",
                            "resource_count": 3,
                            "chunk_count": 40,
                            "source_count": 3,
                        }
                    ],
                    "tag_counts": {"housing": 3},
                    "locale": "en",
                    "total": 1,
                },
                {"tags": [], "tag_counts": {}, "locale": "en", "total": 0},
                {
                    "tags": [
                        {
                            "tag": "health",
                            "label": "Health",
                            "locale": "es",
                            "resource_count": 5,
                            "chunk_count": 100,
                            "source_count": 4,
                        }
                    ],
                    "tag_counts": {"health": 5},
                    "locale": "es",
                    "total": 1,
                },
                {
                    "tags": [
                        {
                            "tag": "food",
                            "label": "Food",
                            "locale": "en",
                            "resource_count": 2,
                            "chunk_count": 20,
                            "source_count": 2,
                        },
                        {
                            "tag": "permits",
                            "label": "Permits",
                            "locale": "en",
                            "resource_count": 1,
                            "chunk_count": 10,
                            "source_count": 1,
                        },
                    ],
                    "tag_counts": {"food": 2, "permits": 1},
                    "locale": "en",
                    "total": 2,
                },
                {
                    "tags": [],
                    "tag_counts": {},
                    "locale": "es",
                    "total": 0,
                },
            ]
        }
    )


class GatewayPublicRootResponse(BaseModel):
    """JSON body for ``GET /`` when returning service discovery (non-HTML clients)."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "description": "Consolidated API for Q&A and documents",
                    "api_base": "/api/v1",
                    "endpoints": {"health": "/health"},
                    "environment": {"region": "local"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.1",
                    "description": "Staging gateway",
                    "api_base": "/api/v1",
                    "endpoints": {"docs": "/api/v1/docs"},
                    "environment": {"region": "staging"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "description": "Production",
                    "api_base": "/api/v1",
                    "endpoints": {},
                    "environment": {"region": "us-east-1"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "0.9.0",
                    "description": "Canary",
                    "api_base": "/api/v1",
                    "endpoints": {"ask": "/api/v1/ask"},
                    "environment": {"canary": "true"},
                },
                {
                    "service": "Vecinita Unified API Gateway",
                    "version": "1.0.0",
                    "description": "Edge",
                    "api_base": "/api/v1",
                    "endpoints": {"embed": "/api/v1/embed"},
                    "environment": {"edge": "true"},
                },
            ]
        },
    )

    service: str = Field(..., examples=["Vecinita Unified API Gateway"])
    version: str = Field(..., examples=["1.0.0"])
    description: str = Field(..., examples=["Consolidated API for Q&A and documents"])
    api_base: str = Field(..., examples=["/api/v1"])
    endpoints: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)


class ScrapeGatewayStatsResponse(BaseModel):
    """``GET /api/v1/scrape/stats`` — in-memory job manager counters."""

    total_jobs: int = Field(..., ge=0, examples=[2])
    by_status: dict[str, int] = Field(
        default_factory=dict,
        examples=[{"queued": 1, "completed": 1}],
    )
    retention_hours: int = Field(..., ge=0, examples=[24])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_jobs": 2,
                    "by_status": {"queued": 1, "completed": 1},
                    "retention_hours": 24,
                },
                {"total_jobs": 0, "by_status": {}, "retention_hours": 48},
                {
                    "total_jobs": 10,
                    "by_status": {"completed": 8, "failed": 2},
                    "retention_hours": 12,
                },
                {
                    "total_jobs": 100,
                    "by_status": {"running": 3, "queued": 5, "completed": 92},
                    "retention_hours": 72,
                },
                {
                    "total_jobs": 1,
                    "by_status": {"cancelled": 1},
                    "retention_hours": 6,
                },
            ]
        }
    )


class ScrapeGatewayCleanupResponse(BaseModel):
    """``POST /api/v1/scrape/cleanup`` JSON body."""

    deleted_jobs: int = Field(..., ge=0, examples=[0])
    message: str = Field(..., examples=["Deleted 0 old jobs"])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"deleted_jobs": 0, "message": "Deleted 0 old jobs"},
                {"deleted_jobs": 5, "message": "Deleted 5 old jobs"},
                {"deleted_jobs": 1, "message": "Deleted 1 old job"},
                {"deleted_jobs": 100, "message": "Deleted 100 old jobs"},
                {"deleted_jobs": 12, "message": "Cleanup: removed 12 stale jobs"},
            ]
        }
    )


class GatewayReindexTriggerResponse(BaseModel):
    """``POST /api/v1/scrape/reindex`` — proxied payload plus ``service_url``."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "examples": [
                {
                    "service_url": (
                        "https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs"
                    ),
                    "status": "accepted",
                },
                {
                    "service_url": "http://scraper:9000/jobs",
                    "job_id": "reindex-1",
                },
                {
                    "service_url": "https://scraper.example/reindex",
                    "clean": True,
                },
                {"service_url": "http://localhost:9000/jobs", "verbose": True},
                {
                    "service_url": "https://staging-scraper.example/jobs",
                    "message": "reindex queued",
                },
            ]
        },
    )

    service_url: str = Field(
        ...,
        description="Base URL of the upstream reindex service that was called.",
        examples=["https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs"],
    )


class GatewayEmbeddingConfigUpdateParams(BaseModel):
    """Query bundle for ``POST /api/v1/embed/config``."""

    provider: str = Field(
        ...,
        description="Embedding provider (e.g. huggingface).",
        examples=["huggingface"],
    )
    model: str = Field(
        ...,
        description="Model identifier.",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    lock: bool | None = Field(
        default=None,
        description="When set, persist lock flag upstream when supported.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "provider": "huggingface",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "lock": False,
                },
                {
                    "provider": "huggingface",
                    "model": "BAAI/bge-small-en-v1.5",
                    "lock": None,
                },
                {
                    "provider": "huggingface",
                    "model": "sentence-transformers/all-mpnet-base-v2",
                    "lock": True,
                },
                {"provider": "huggingface", "model": "intfloat/e5-small-v2", "lock": False},
                {
                    "provider": "huggingface",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "lock": True,
                },
            ]
        }
    )


class ScrapeGatewayHistoryQueryParams(BaseModel):
    """Query bundle for ``GET /api/v1/scrape/history``."""

    limit: int = Field(default=50, ge=1, le=100, examples=[25])
    offset: int = Field(default=0, ge=0, examples=[0])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"limit": 50, "offset": 0},
                {"limit": 25, "offset": 0},
                {"limit": 100, "offset": 50},
                {"limit": 10, "offset": 100},
                {"limit": 1, "offset": 0},
            ]
        }
    )


class ScrapeGatewayReindexQueryParams(BaseModel):
    """Query bundle for ``POST /api/v1/scrape/reindex``."""

    clean: bool = Field(
        default=False, description="Run full clean reindex first.", examples=[False]
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose pipeline logging upstream.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"clean": False, "verbose": False},
                {"clean": True, "verbose": False},
                {"clean": False, "verbose": True},
                {"clean": True, "verbose": True},
                {"clean": False, "verbose": False},
            ]
        }
    )


class GatewayAskQueryParams(BaseModel):
    """Query bundle shared by ``GET /api/v1/ask`` and ``GET /api/v1/ask/stream``."""

    question: str = Field(
        ...,
        min_length=1,
        description="User question text.",
        examples=["What affordable housing programs exist in this neighborhood?"],
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread id for correlating follow-ups.",
        examples=["default"],
    )
    context_answer: str | None = Field(
        default=None,
        description="Prior assistant answer for short contextual follow-ups.",
        examples=["Nearby clinics include Eastside Community Health Center."],
    )
    lang: str | None = Field(
        default=None,
        description="Override language detection (e.g. en, es).",
        examples=["en"],
    )
    provider: str | None = Field(
        default=None,
        description="Local LLM provider override (ollama-compatible).",
        examples=["ollama"],
    )
    model: str | None = Field(
        default=None,
        description="Model id override; must exist in upstream ``/config`` when set.",
        examples=["gemma3"],
    )
    tags: str | None = Field(
        default=None,
        description="Comma-separated metadata tags for retrieval filtering.",
        examples=["housing,permits"],
    )
    tag_match_mode: Literal["any", "all"] = Field(
        default="any",
        description="Tag match mode: any|all.",
        examples=["any"],
    )
    include_untagged_fallback: bool = Field(
        default=True,
        description="Include untagged documents when a tag filter is active.",
        examples=[True],
    )
    rerank: bool = Field(
        default=False,
        description="Enable reranking of retrieved chunks upstream.",
        examples=[False],
    )
    rerank_top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of chunks to retain after reranking.",
        examples=[10],
    )

    @field_validator("lang", mode="before")
    @classmethod
    def normalize_ask_lang(cls, value: object) -> str | None:
        """Treat literal ``null`` / ``none`` query tokens as unset (Schemathesis / clients)."""
        if value is None:
            return None
        if isinstance(value, str):
            s = value.strip()
            if not s or s.lower() in {"null", "none", "undefined"}:
                return None
            return s
        return None

    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "examples": [
                {
                    "question": "What affordable housing programs exist in this neighborhood?",
                    "thread_id": None,
                    "context_answer": None,
                    "lang": None,
                    "provider": None,
                    "model": None,
                    "tags": None,
                    "tag_match_mode": "any",
                    "include_untagged_fallback": True,
                    "rerank": False,
                    "rerank_top_k": 10,
                },
                {
                    "question": "List eviction defense steps for non-payment notices.",
                    "thread_id": "sess-001",
                    "context_answer": None,
                    "lang": "en",
                    "provider": "ollama",
                    "model": "gemma3",
                    "tags": "housing,legal",
                    "tag_match_mode": "any",
                    "include_untagged_fallback": True,
                    "rerank": True,
                    "rerank_top_k": 20,
                },
                {
                    "question": "¿Qué documentos necesito para Medi-Cal?",
                    "thread_id": "es-thread-2",
                    "context_answer": None,
                    "lang": "es",
                    "provider": None,
                    "model": None,
                    "tags": "health",
                    "tag_match_mode": "all",
                    "include_untagged_fallback": False,
                    "rerank": False,
                    "rerank_top_k": 15,
                },
                {
                    "question": "Follow up: include weekend hours only.",
                    "thread_id": "clinic-thread-9",
                    "context_answer": "Nearby clinics include Eastside Community Health Center.",
                    "lang": "en",
                    "provider": "ollama",
                    "model": None,
                    "tags": None,
                    "tag_match_mode": "any",
                    "include_untagged_fallback": True,
                    "rerank": True,
                    "rerank_top_k": 8,
                },
                {
                    "question": "Compare food pantry eligibility vs CalFresh.",
                    "thread_id": None,
                    "context_answer": None,
                    "lang": "en",
                    "provider": "ollama",
                    "model": "gemma3",
                    "tags": "food,benefits",
                    "tag_match_mode": "all",
                    "include_untagged_fallback": True,
                    "rerank": False,
                    "rerank_top_k": 50,
                },
            ]
        },
    )


class GatewayAskConfigPayload(BaseModel):
    """Normalized JSON from ``GET /api/v1/ask/config`` (gateway-shaped, not agent-raw)."""

    model_config = ConfigDict(extra="allow")

    providers: list[dict[str, Any]] = Field(default_factory=list)
    models: dict[str, Any] = Field(default_factory=dict)
    defaultProvider: str | None = Field(default=None, examples=["ollama"])
    defaultModel: str | None = Field(default=None, examples=["gemma3"])
    service_status: str = Field(default="ok", examples=["ok", "degraded"])


# Backward compatibility aliases
HealthCheck = HealthCheckResponse
GatewayConfig = GatewayConfigResponse
IntegrationsStatus = IntegrationsStatusResponse

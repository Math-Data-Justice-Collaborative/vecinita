"""Gateway models — admin."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .scrape import LoaderType

# ============================================================================
# Admin Models
# ============================================================================


class AdminConfigResponse(BaseModel):
    """Response with admin configuration (GET /api/admin/config)."""

    require_confirmation: bool = Field(
        default=True,
        description="Require confirmation tokens for destructive operations",
        examples=[True],
    )
    confirmation_token_ttl_seconds: int = Field(
        default=300, description="Confirmation token expiration time in seconds", examples=[300]
    )
    max_jobs_to_retain: int = Field(
        default=1000, description="Maximum scraping jobs to keep in memory", examples=[1000]
    )
    auto_cleanup_hours: int = Field(
        default=24, description="Auto-cleanup job retention period in hours", examples=[24]
    )
    enable_document_deletion: bool = Field(
        default=True, description="Allow document deletion via admin endpoint", examples=[True]
    )
    enable_database_reset: bool = Field(
        default=False, description="Allow full database reset (dangerous!)", examples=[False]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 24,
                    "enable_document_deletion": True,
                    "enable_database_reset": False,
                },
                {
                    "require_confirmation": False,
                    "confirmation_token_ttl_seconds": 600,
                    "max_jobs_to_retain": 500,
                    "auto_cleanup_hours": 48,
                    "enable_document_deletion": True,
                    "enable_database_reset": False,
                },
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 120,
                    "max_jobs_to_retain": 2000,
                    "auto_cleanup_hours": 12,
                    "enable_document_deletion": False,
                    "enable_database_reset": False,
                },
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 72,
                    "enable_document_deletion": True,
                    "enable_database_reset": True,
                },
                {
                    "require_confirmation": True,
                    "confirmation_token_ttl_seconds": 900,
                    "max_jobs_to_retain": 300,
                    "auto_cleanup_hours": 6,
                    "enable_document_deletion": False,
                    "enable_database_reset": False,
                },
            ],
            "example": {
                "require_confirmation": True,
                "confirmation_token_ttl_seconds": 300,
                "max_jobs_to_retain": 1000,
                "auto_cleanup_hours": 24,
                "enable_document_deletion": True,
                "enable_database_reset": False,
            },
        }
    )


class AdminConfigUpdateRequest(BaseModel):
    """Request to update admin configuration (POST /api/admin/config) - PARTIAL IMPLEMENTATION."""

    require_confirmation: bool | None = Field(
        default=None, description="Update confirmation requirement setting", examples=[False]
    )
    auto_cleanup_hours: int | None = Field(
        default=None,
        description="Update job retention period (TODO: not yet implemented)",
        examples=[24],
    )
    enable_document_deletion: bool | None = Field(
        default=None,
        description="Allow/disallow document deletion (TODO: not yet implemented)",
        examples=[True],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "require_confirmation": False,
                    "auto_cleanup_hours": None,
                    "enable_document_deletion": None,
                },
                {
                    "require_confirmation": True,
                    "auto_cleanup_hours": None,
                    "enable_document_deletion": None,
                },
                {
                    "require_confirmation": None,
                    "auto_cleanup_hours": 48,
                    "enable_document_deletion": None,
                },
                {
                    "require_confirmation": None,
                    "auto_cleanup_hours": None,
                    "enable_document_deletion": True,
                },
                {
                    "require_confirmation": True,
                    "auto_cleanup_hours": 72,
                    "enable_document_deletion": False,
                },
            ],
            "example": {"require_confirmation": False},
        }
    )


class AdminConfigUpdateResponse(BaseModel):
    """Response from config update (POST /api/admin/config)."""

    updated: bool = Field(..., description="Whether update succeeded", examples=[True])
    updated_fields: list[str] = Field(
        ..., description="Fields that were updated", examples=[["require_confirmation"]]
    )
    config: AdminConfigResponse = Field(..., description="Updated configuration")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "updated": True,
                    "updated_fields": ["require_confirmation"],
                    "config": {
                        "require_confirmation": False,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 1000,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": True,
                    "updated_fields": ["auto_cleanup_hours"],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 1000,
                        "auto_cleanup_hours": 48,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": False,
                    "updated_fields": [],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 1000,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": True,
                    "updated_fields": ["enable_document_deletion", "require_confirmation"],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 600,
                        "max_jobs_to_retain": 500,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": False,
                        "enable_database_reset": False,
                    },
                },
                {
                    "updated": True,
                    "updated_fields": ["max_jobs_to_retain"],
                    "config": {
                        "require_confirmation": True,
                        "confirmation_token_ttl_seconds": 300,
                        "max_jobs_to_retain": 2000,
                        "auto_cleanup_hours": 24,
                        "enable_document_deletion": True,
                        "enable_database_reset": False,
                    },
                },
            ],
            "example": {
                "updated": True,
                "updated_fields": ["require_confirmation"],
                "config": {
                    "require_confirmation": False,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 24,
                    "enable_document_deletion": True,
                    "enable_database_reset": False,
                },
            },
        }
    )


# NOT YET IMPLEMENTED: Admin endpoints below


class AdminHealthResponse(BaseModel):
    """Response from health check (GET /api/admin/health) - NOT YET IMPLEMENTED."""

    status: str = Field(..., description="Overall system health status", examples=["healthy"])
    agent_service: dict[str, Any] | None = Field(
        default=None,
        description="Agent service health details",
        examples=[{"status": "ok", "response_time_ms": 45, "last_check": "2024-02-09T10:30:00Z"}],
    )
    embedding_service: dict[str, Any] | None = Field(
        default=None, description="Embedding service health details"
    )
    database: dict[str, Any] | None = Field(default=None, description="Database health details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "healthy",
                    "agent_service": {"status": "ok"},
                    "embedding_service": {"status": "ok"},
                    "database": {"status": "ok"},
                    "timestamp": "2024-02-09T10:30:00Z",
                },
                {
                    "status": "degraded",
                    "agent_service": {"status": "ok"},
                    "embedding_service": {"status": "timeout"},
                    "database": {"status": "ok"},
                    "timestamp": "2024-02-09T10:31:00Z",
                },
                {
                    "status": "unhealthy",
                    "agent_service": None,
                    "embedding_service": {"status": "ok"},
                    "database": {"status": "error"},
                    "timestamp": "2024-02-09T10:32:00Z",
                },
                {
                    "status": "healthy",
                    "agent_service": {"status": "ok", "response_time_ms": 40},
                    "embedding_service": {"status": "ok", "response_time_ms": 55},
                    "database": {"status": "ok", "connections": 4},
                    "timestamp": "2024-02-09T10:33:00Z",
                },
                {
                    "status": "degraded",
                    "agent_service": {"status": "slow"},
                    "embedding_service": {"status": "ok"},
                    "database": {"status": "slow"},
                    "timestamp": "2024-02-09T10:34:00Z",
                },
            ]
        }
    )


class DatabaseStats(BaseModel):
    """Database statistics."""

    total_chunks: int = Field(..., description="Total document chunks", examples=[45230])
    unique_sources: int = Field(..., description="Unique source URLs", examples=[892])
    total_embeddings: int = Field(..., description="Total embeddings generated", examples=[45230])
    average_chunk_size: float = Field(..., description="Mean chunk size bytes", examples=[2048.5])
    db_size_bytes: int | None = Field(
        default=None, description="Total database size in bytes", examples=[92593156]
    )
    last_updated: datetime | None = Field(default=None, description="Last update timestamp")


class AdminStatsResponse(BaseModel):
    """Response with admin statistics (GET /api/admin/stats) - NOT YET IMPLEMENTED."""

    database: DatabaseStats = Field(..., description="Database statistics")
    services: dict[str, dict[str, Any]] = Field(
        ...,
        description="Service metrics",
        examples=[
            {
                "agent_service": {
                    "uptime_seconds": 86400,
                    "requests_processed": 5432,
                    "average_latency_ms": 245,
                },
                "embedding_service": {
                    "uptime_seconds": 86400,
                    "embeddings_generated": 125600,
                    "cache_hit_rate": 0.67,
                },
            }
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "database": {
                        "total_chunks": 45230,
                        "unique_sources": 892,
                        "total_embeddings": 45230,
                        "average_chunk_size": 2048.5,
                        "db_size_bytes": 92593156,
                        "last_updated": "2024-02-09T10:00:00Z",
                    },
                    "services": {
                        "agent_service": {"uptime_seconds": 86400},
                        "embedding_service": {"cache_hit_rate": 0.67},
                    },
                },
                {
                    "database": {
                        "total_chunks": 0,
                        "unique_sources": 0,
                        "total_embeddings": 0,
                        "average_chunk_size": 0.0,
                        "db_size_bytes": None,
                        "last_updated": None,
                    },
                    "services": {"agent_service": {}},
                },
                {
                    "database": {
                        "total_chunks": 100,
                        "unique_sources": 10,
                        "total_embeddings": 100,
                        "average_chunk_size": 1500.0,
                        "db_size_bytes": 1024000,
                        "last_updated": "2024-02-09T09:00:00Z",
                    },
                    "services": {
                        "agent_service": {"requests_processed": 50},
                        "embedding_service": {"embeddings_generated": 200},
                    },
                },
                {
                    "database": {
                        "total_chunks": 9999,
                        "unique_sources": 200,
                        "total_embeddings": 9999,
                        "average_chunk_size": 1800.0,
                        "db_size_bytes": 50000000,
                        "last_updated": "2024-02-09T08:00:00Z",
                    },
                    "services": {
                        "agent_service": {"average_latency_ms": 300},
                        "embedding_service": {"average_latency_ms": 80},
                    },
                },
                {
                    "database": {
                        "total_chunks": 500000,
                        "unique_sources": 12000,
                        "total_embeddings": 500000,
                        "average_chunk_size": 2100.0,
                        "db_size_bytes": 200000000,
                        "last_updated": "2024-02-09T07:00:00Z",
                    },
                    "services": {
                        "agent_service": {"uptime_seconds": 172800},
                        "embedding_service": {"uptime_seconds": 172800},
                    },
                },
            ]
        }
    )


class DocumentChunk(BaseModel):
    """Document chunk metadata."""

    chunk_id: str = Field(..., description="Chunk identifier", examples=["chunk-abc123"])
    source_url: str = Field(..., description="Source document URL")
    content_preview: str = Field(
        ...,
        description="First 200 chars of content",
        examples=["Machine learning is a branch of artificial intelligence that..."],
    )
    embedding_dimension: int = Field(..., description="Embedding dimensionality", examples=[384])
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class DocumentsListResponse(BaseModel):
    """Response listing indexed documents (GET /api/admin/documents) - NOT YET IMPLEMENTED."""

    documents: list[DocumentChunk] = Field(..., description="List of document chunks")
    total: int = Field(..., description="Total chunks in database", examples=[45230])
    page: int = Field(..., description="Current page number", examples=[1])
    limit: int = Field(..., description="Results per page", examples=[20])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-001",
                            "source_url": "https://example.com/doc",
                            "content_preview": "Content here...",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-09T10:00:00Z",
                            "updated_at": None,
                        }
                    ],
                    "total": 45230,
                    "page": 1,
                    "limit": 20,
                },
                {"documents": [], "total": 0, "page": 1, "limit": 50},
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-a",
                            "source_url": "https://city.gov/a",
                            "content_preview": "Housing…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-09T09:00:00Z",
                            "updated_at": "2024-02-09T09:30:00Z",
                        },
                        {
                            "chunk_id": "chunk-b",
                            "source_url": "https://city.gov/b",
                            "content_preview": "Permits…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-09T09:05:00Z",
                            "updated_at": None,
                        },
                    ],
                    "total": 200,
                    "page": 2,
                    "limit": 10,
                },
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-wic",
                            "source_url": "https://health.example/wic",
                            "content_preview": "WIC intake…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-08T12:00:00Z",
                            "updated_at": None,
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "limit": 100,
                },
                {
                    "documents": [
                        {
                            "chunk_id": "chunk-last",
                            "source_url": "https://transit.example",
                            "content_preview": "Routes…",
                            "embedding_dimension": 384,
                            "created_at": "2024-02-07T15:00:00Z",
                            "updated_at": None,
                        }
                    ],
                    "total": 999,
                    "page": 10,
                    "limit": 1,
                },
            ],
            "example": {
                "documents": [
                    {
                        "chunk_id": "chunk-001",
                        "source_url": "https://example.com/doc",
                        "content_preview": "Content here...",
                        "embedding_dimension": 384,
                        "created_at": "2024-02-09T10:00:00Z",
                    }
                ],
                "total": 45230,
                "page": 1,
                "limit": 20,
            },
        }
    )


class DeleteChunkResponse(BaseModel):
    """Response from delete chunk (DELETE /api/admin/documents/{chunk_id}) - NOT YET IMPLEMENTED."""

    success: bool = Field(..., description="Whether deletion succeeded", examples=[True])
    deleted_chunk_id: str = Field(..., description="ID of deleted chunk", examples=["chunk-abc123"])
    message: str = Field(..., description="Confirmation message")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-abc123",
                    "message": "Chunk deleted",
                },
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-001",
                    "message": "Removed from index",
                },
                {
                    "success": False,
                    "deleted_chunk_id": "chunk-missing",
                    "message": "Chunk not found",
                },
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-stale",
                    "message": "Stale chunk purged",
                },
                {
                    "success": True,
                    "deleted_chunk_id": "chunk-test",
                    "message": "Test artifact removed",
                },
            ]
        }
    )


class CleanDatabaseRequest(BaseModel):
    """Request to clean database (POST /api/admin/database/clean) - NOT YET IMPLEMENTED."""

    confirmation_token: str = Field(
        ...,
        description="Token obtained from GET /api/admin/database/clean-request",
        examples=["token-abc123xyz789"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"confirmation_token": "token-abc123xyz789"},
                {"confirmation_token": "token-clean-db-2026-04-01-a7f3"},
                {"confirmation_token": "token-reset-staging-9c21e4b0"},
                {"confirmation_token": "token-operator-confirm-001"},
                {"confirmation_token": "token-e2e-cleanup-expires-300s"},
            ],
            "example": {"confirmation_token": "token-abc123xyz789"},
        }
    )


class CleanDatabaseResponse(BaseModel):
    """Response from database cleanup (POST /api/admin/database/clean)."""

    success: bool = Field(..., description="Whether cleanup succeeded", examples=[True])
    deleted_chunks: int = Field(..., description="Count of chunks deleted", examples=[45230])
    message: str = Field(
        ..., description="Cleanup summary", examples=["Database cleaned: 45230 chunks deleted"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "deleted_chunks": 45230,
                    "message": "Database cleaned: 45230 chunks deleted",
                },
                {
                    "success": True,
                    "deleted_chunks": 0,
                    "message": "No chunks matched cleanup criteria",
                },
                {
                    "success": False,
                    "deleted_chunks": 0,
                    "message": "Cleanup aborted: invalid token",
                },
                {
                    "success": True,
                    "deleted_chunks": 120,
                    "message": "Staging database wiped",
                },
                {
                    "success": True,
                    "deleted_chunks": 500000,
                    "message": "Full reset completed",
                },
            ]
        }
    )


class CleanRequestTokenResponse(BaseModel):
    """Response with cleanup confirmation token (GET /api/admin/database/clean-request) - NOT YET IMPLEMENTED."""

    token: str = Field(
        ..., description="One-time use confirmation token", examples=["token-abc123xyz789"]
    )
    expires_at: datetime = Field(..., description="Token expiration time")
    endpoint: str = Field(
        ...,
        description="Endpoint to use this token with",
        examples=["POST /api/admin/database/clean"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "token": "token-abc123xyz789",
                    "expires_at": "2024-02-09T11:00:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-expires-5m",
                    "expires_at": "2024-02-09T10:35:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-staging-wipe",
                    "expires_at": "2024-02-09T12:00:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-operator-2",
                    "expires_at": "2024-02-09T15:00:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
                {
                    "token": "token-e2e-only",
                    "expires_at": "2024-02-09T10:10:00Z",
                    "endpoint": "POST /api/admin/database/clean",
                },
            ]
        }
    )


class SourcesListResponse(BaseModel):
    """Response listing all document sources (GET /api/admin/sources) - NOT YET IMPLEMENTED."""

    sources: list[dict[str, Any]] = Field(
        ...,
        description="List of unique sources with metadata",
        examples=[
            [
                {
                    "url": "https://example.com/docs",
                    "chunk_count": 125,
                    "created_at": "2024-02-09T10:00:00Z",
                    "last_updated": "2024-02-09T12:00:00Z",
                }
            ]
        ],
    )
    total: int = Field(..., description="Total unique sources", examples=[892])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sources": [
                        {
                            "url": "https://example.com/docs",
                            "chunk_count": 125,
                            "created_at": "2024-02-09T10:00:00Z",
                            "last_updated": "2024-02-09T12:00:00Z",
                        }
                    ],
                    "total": 892,
                },
                {"sources": [], "total": 0},
                {
                    "sources": [
                        {
                            "url": "https://city.gov/housing",
                            "chunk_count": 40,
                            "created_at": "2024-02-08T08:00:00Z",
                            "last_updated": "2024-02-09T09:00:00Z",
                        }
                    ],
                    "total": 1,
                },
                {
                    "sources": [
                        {
                            "url": "https://a.example",
                            "chunk_count": 10,
                            "created_at": "2024-02-01T00:00:00Z",
                            "last_updated": "2024-02-05T00:00:00Z",
                        },
                        {
                            "url": "https://b.example",
                            "chunk_count": 20,
                            "created_at": "2024-02-02T00:00:00Z",
                            "last_updated": "2024-02-06T00:00:00Z",
                        },
                    ],
                    "total": 2,
                },
                {
                    "sources": [
                        {
                            "url": "https://health.example",
                            "chunk_count": 500,
                            "created_at": "2024-01-01T00:00:00Z",
                            "last_updated": "2024-02-09T00:00:00Z",
                        }
                    ],
                    "total": 50,
                },
            ]
        }
    )


class ValidateSourceRequest(BaseModel):
    """Request to validate a source (POST /api/admin/sources/validate) - NOT YET IMPLEMENTED."""

    url: str = Field(..., description="URL to validate", examples=["https://example.com"])
    loader_type: LoaderType = Field(
        ..., description="Loader to test with", examples=[LoaderType.AUTO]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"url": "https://example.com", "loader_type": "auto"},
                {"url": "https://city.gov/housing/forms", "loader_type": "playwright"},
                {"url": "https://docs.example/wiki", "loader_type": "recursive"},
                {"url": "https://reports.example/annual.pdf", "loader_type": "unstructured"},
                {"url": "https://news.example/article/123", "loader_type": "auto"},
            ]
        }
    )


class ValidateSourceResponse(BaseModel):
    """Response from source validation (POST /api/admin/sources/validate)."""

    url: str = Field(..., description="URL tested")
    is_accessible: bool = Field(..., description="Whether URL is accessible", examples=[True])
    is_scrapeable: bool = Field(..., description="Whether content is scrapeable", examples=[True])
    http_status: int | None = Field(default=None, description="HTTP status code", examples=[200])
    message: str = Field(
        ..., description="Validation result message", examples=["URL is accessible and scrapeable"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.com",
                    "is_accessible": True,
                    "is_scrapeable": True,
                    "http_status": 200,
                    "message": "URL is accessible and scrapeable",
                },
                {
                    "url": "https://missing.example",
                    "is_accessible": False,
                    "is_scrapeable": False,
                    "http_status": None,
                    "message": "DNS resolution failed",
                },
                {
                    "url": "https://forbidden.example/secret",
                    "is_accessible": True,
                    "is_scrapeable": False,
                    "http_status": 403,
                    "message": "HTTP 403: forbidden",
                },
                {
                    "url": "https://slow.example",
                    "is_accessible": False,
                    "is_scrapeable": False,
                    "http_status": 504,
                    "message": "Gateway timeout",
                },
                {
                    "url": "https://pdf.example/file.pdf",
                    "is_accessible": True,
                    "is_scrapeable": True,
                    "http_status": 200,
                    "message": "PDF reachable via GET",
                },
            ]
        }
    )

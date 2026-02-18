"""
Unified API Gateway - Request/Response Models

Defines Pydantic schemas for Q&A, scraping, embeddings, and admin endpoints.
Enhanced with comprehensive Field descriptions, examples, and Pydantic v3 ConfigDict
for rich Swagger/OpenAPI documentation at /docs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Scrape/Job Management Models
# ============================================================================


class LoaderType(str, Enum):
    """Document loader types for scraping."""
    PLAYWRIGHT = "playwright"
    RECURSIVE = "recursive"
    UNSTRUCTURED = "unstructured"
    AUTO = "auto"


class JobStatus(str, Enum):
    """Status of async scrape job."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeStartRequest(BaseModel):
    """Request to start a web scraping job (POST /api/scrape/)."""
    urls: List[str] = Field(
        ...,
        min_length=1,
        description="URLs to scrape (minimum 1, maximum configured in gateway)",
        examples=["https://example.com/docs", "https://example.com/blog"]
    )
    force_loader: LoaderType = Field(
        default=LoaderType.AUTO,
        description="Document loader strategy (auto=try standard first then Playwright, playwright=JS-heavy sites only)",
        example=LoaderType.AUTO
    )
    stream: bool = Field(
        default=False,
        description="Stream chunks to database as scraping proceeds (vs batch on completion)",
        example=False
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "urls": ["https://example.com/docs", "https://example.com/blog"],
                "force_loader": "auto",
                "stream": False
            },
            "description": "POST /api/scrape/ - Initiate async web scraping job"
        }
    )


# Backward compatibility alias
ScrapeRequest = ScrapeStartRequest


class ScrapeJobMetadata(BaseModel):
    """Metadata about a scraping job."""
    job_id: str = Field(..., description="Unique job identifier")
    urls: List[str] = Field(..., description="URLs being scraped")
    force_loader: LoaderType = Field(..., description="Loader strategy used")
    stream: bool = Field(..., description="Whether streaming to DB is enabled")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion timestamp")
    cancelled_at: Optional[datetime] = Field(default=None, description="Job cancellation timestamp")


class ScrapeJobResult(BaseModel):
    """Result data for completed scrape job."""
    total_chunks: int = Field(
        default=0,
        description="Total chunks extracted from all URLs",
        example=125
    )
    successful_urls: List[str] = Field(
        default_factory=list,
        description="URLs that were successfully scraped",
        example=["https://example.com/page1", "https://example.com/page2"]
    )
    failed_urls: List[str] = Field(
        default_factory=list,
        description="URLs that failed to scrape",
        example=["https://example.com/404"]
    )
    failed_urls_log: Dict[str, str] = Field(
        default_factory=dict,
        description="URL to error message mapping for failed URLs",
        example={"https://example.com/404": "HTTP 404: Page not found"}
    )


class ScrapeJob(BaseModel):
    """Complete representation of a scraping job."""
    job_id: str = Field(..., description="Job ID", example="scrape-job-abc123xyz")
    status: JobStatus = Field(..., description="Current job status")
    progress_percent: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage 0-100%",
        example=65
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Scraped 2/3 URLs, 45 chunks extracted"
    )
    metadata: ScrapeJobMetadata = Field(..., description="Job metadata")
    result: Optional[ScrapeJobResult] = Field(
        default=None,
        description="Results (populated when status=completed)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status=failed"
    )


class ScrapeInitResponse(BaseModel):
    """Response when submitting scrape request (POST /api/scrape/)."""
    job_id: str = Field(
        ...,
        description="Unique job identifier for tracking",
        example="scrape-job-abc123xyz"
    )
    status: JobStatus = Field(
        default=JobStatus.QUEUED,
        description="Initial status (always queued)",
        example=JobStatus.QUEUED
    )
    message: str = Field(
        ...,
        description="Human-readable message with polling instructions",
        example="Scrape job enqueued. Poll GET /api/scrape/scrape-job-abc123xyz for status."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "scrape-job-abc123xyz",
                "status": "queued",
                "message": "Scrape job enqueued. Poll GET /api/scrape/scrape-job-abc123xyz for status."
            }
        }
    )


class ScrapeStatusResponse(BaseModel):
    """Response for job status queries (GET /api/scrape/{job_id})."""
    job: ScrapeJob = Field(..., description="Complete job representation with status and results")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job": {
                    "job_id": "scrape-job-abc123xyz",
                    "status": "completed",
                    "progress_percent": 100,
                    "message": "Scrape completed successfully",
                    "metadata": {
                        "job_id": "scrape-job-abc123xyz",
                        "urls": ["https://example.com/page1"],
                        "force_loader": "auto",
                        "stream": False,
                        "created_at": "2024-02-09T10:00:00Z",
                        "started_at": "2024-02-09T10:00:05Z",
                        "completed_at": "2024-02-09T10:02:30Z",
                        "cancelled_at": None
                    },
                    "result": {
                        "total_chunks": 125,
                        "successful_urls": ["https://example.com/page1"],
                        "failed_urls": [],
                        "failed_urls_log": {}
                    },
                    "error": None
                }
            }
        }
    )


class ScrapeCancelResponse(BaseModel):
    """Response for cancel job request (POST /api/scrape/{job_id}/cancel)."""
    job: ScrapeJob = Field(..., description="Updated job with cancelled status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job": {
                    "job_id": "scrape-job-abc123xyz",
                    "status": "cancelled",
                    "progress_percent": 45,
                    "message": "Job cancelled by user",
                    "metadata": {},
                    "result": None,
                    "error": None
                }
            }
        }
    )


class ScrapeHistoryRequest(BaseModel):
    """Query params for scrape history (GET /api/scrape/history)."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)", example=1)
    limit: int = Field(default=10, ge=1, le=100, description="Results per page", example=10)
    status: Optional[JobStatus] = Field(default=None, description="Filter by job status")


class ScrapeHistoryResponse(BaseModel):
    """Response listing job history (GET /api/scrape/history)."""
    jobs: List[ScrapeJob] = Field(..., description="List of jobs for current page")
    total: int = Field(..., description="Total number of jobs", example=24)
    page: int = Field(..., description="Current page number", example=1)
    limit: int = Field(..., description="Results per page", example=10)
    total_pages: Optional[int] = Field(default=None, description="Total page count", example=3)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "jobs": [
                    {
                        "job_id": "scrape-job-1",
                        "status": "completed",
                        "progress_percent": 100,
                        "message": "Scrape completed",
                        "metadata": {},
                        "result": {"total_chunks": 50}
                    }
                ],
                "total": 24,
                "page": 1,
                "limit": 10,
                "total_pages": 3
            }
        }
    )


class ScrapeStatsResponse(BaseModel):
    """Response with scraping statistics (GET /api/scrape/stats)."""
    total_jobs: int = Field(..., description="Total jobs created", example=152)
    by_status: Dict[str, int] = Field(
        ...,
        description="Count of jobs by status",
        example={
            "completed": 130,
            "running": 3,
            "queued": 5,
            "failed": 12,
            "cancelled": 2
        }
    )
    total_chunks_processed: int = Field(
        ...,
        description="Total chunks extracted across all jobs",
        example=45230
    )
    total_urls_processed: int = Field(
        ...,
        description="Total URLs processed",
        example=892
    )
    success_rate: float = Field(
        ...,
        ge=0,
        le=1,
        description="Proportion of successful URLs (0-1)",
        example=0.92
    )
    average_chunks_per_url: float = Field(
        ...,
        description="Mean chunks extracted per URL",
        example=50.7
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_jobs": 152,
                "by_status": {
                    "completed": 130,
                    "running": 3,
                    "queued": 5,
                    "failed": 12,
                    "cancelled": 2
                },
                "total_chunks_processed": 45230,
                "total_urls_processed": 892,
                "success_rate": 0.92,
                "average_chunks_per_url": 50.7
            }
        }
    )


class ScrapeCleanupRequest(BaseModel):
    """Request for job cleanup (POST /api/scrape/cleanup)."""
    hours_old: int = Field(
        default=24,
        ge=1,
        description="Delete jobs older than this many hours",
        example=24
    )
    dry_run: bool = Field(
        default=False,
        description="Simulate cleanup without deleting",
        example=False
    )


class ScrapeCleanupResponse(BaseModel):
    """Response from cleanup operation (POST /api/scrape/cleanup)."""
    deleted_jobs: int = Field(..., description="Count of jobs deleted", example=15)
    deleted_chunks: Optional[int] = Field(
        default=None,
        description="Count of chunks removed if available",
        example=750
    )
    deleted_bytes: Optional[int] = Field(
        default=None,
        description="Storage reclaimed in bytes",
        example=2097152
    )
    dry_run: bool = Field(..., description="Whether this was a dry run", example=False)
    message: str = Field(
        ...,
        description="Human-readable cleanup summary",
        example="Cleanup completed: 15 jobs deleted"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "deleted_jobs": 15,
                "deleted_chunks": 750,
                "deleted_bytes": 2097152,
                "dry_run": False,
                "message": "Cleanup completed: 15 jobs deleted"
            }
        }
    )


# Backward compatibility
class ScrapeResponse(BaseModel):
    """Deprecated: Use ScrapeInitResponse instead."""
    job_id: str
    status: JobStatus
    message: str


class ScrapeHistoryResponse(BaseModel):
    """Response listing job history."""
    jobs: List[ScrapeJob]
    total: int


# ============================================================================
# Embedding Models
# ============================================================================


class EmbedRequest(BaseModel):
    """Request to generate embedding for single text (POST /api/embed/) - NOT YET IMPLEMENTED."""
    text: str = Field(
        ...,
        description="Text to embed",
        example="The quick brown fox jumps over the lazy dog"
    )
    model: Optional[str] = Field(
        default=None,
        description="Override embedding model (uses default if None)",
        example="sentence-transformers/all-MiniLM-L6-v2"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "The quick brown fox jumps over the lazy dog",
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }
    )


class EmbedBatchRequest(BaseModel):
    """Request to generate embeddings for multiple texts (POST /api/embed/batch) - NOT YET IMPLEMENTED."""
    texts: List[str] = Field(
        ...,
        min_length=1,
        description="List of texts to embed",
        examples=[
            ["First document to embed", "Second document to embed", "Third document to embed"]
        ]
    )
    model: Optional[str] = Field(
        default=None,
        description="Override embedding model (uses default if None)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texts": [
                    "First document to embed",
                    "Second document to embed",
                    "Third document to embed"
                ],
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }
    )


class EmbedResponse(BaseModel):
    """Response with embedding vector (POST /api/embed/)."""
    text: str = Field(..., description="Original text that was embedded")
    embedding: List[float] = Field(
        ...,
        description="384-dimensional embedding vector from HuggingFace sentence-transformers",
        example=[0.123, -0.456, 0.789]  # truncated for display
    )
    model: str = Field(..., description="Model used for embedding", example="sentence-transformers/all-MiniLM-L6-v2")
    dimension: int = Field(..., description="Embedding dimensionality", example=384)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "The quick brown fox",
                "embedding": [0.123, -0.456, 0.789, "... 381 more values ..."],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384
            }
        }
    )


class EmbedBatchResponse(BaseModel):
    """Response with batch embeddings (POST /api/embed/batch)."""
    embeddings: List[EmbedResponse] = Field(..., description="List of embedding responses")
    model: str = Field(..., description="Model used", example="sentence-transformers/all-MiniLM-L6-v2")
    dimension: int = Field(..., description="Embedding dimensionality", example=384)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "embeddings": [
                    {"text": "First document", "embedding": ["... 384 dims ..."], "model": "...", "dimension": 384},
                    {"text": "Second document", "embedding": ["... 384 dims ..."], "model": "...", "dimension": 384}
                ],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384
            }
        }
    )


class SimilarityRequest(BaseModel):
    """Request to compute similarity between texts (POST /api/embed/similarity) - NOT YET IMPLEMENTED."""
    text1: str = Field(
        ...,
        description="First text",
        example="Machine learning is AI"
    )
    text2: str = Field(
        ...,
        description="Second text",
        example="Deep learning is machine learning"
    )
    model: Optional[str] = Field(
        default=None,
        description="Override embedding model"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text1": "Machine learning is AI",
                "text2": "Deep learning is machine learning",
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }
    )


class SimilarityResponse(BaseModel):
    """Response with similarity score (POST /api/embed/similarity)."""
    text1: str = Field(..., description="First text")
    text2: str = Field(..., description="Second text")
    similarity: float = Field(
        ...,
        ge=-1,
        le=1,
        description="Cosine similarity score (-1 to 1, higher=more similar)",
        example=0.87
    )
    model: str = Field(..., description="Model used", example="sentence-transformers/all-MiniLM-L6-v2")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text1": "Machine learning is AI",
                "text2": "Deep learning is machine learning",
                "similarity": 0.87,
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }
    )


class EmbeddingConfigResponse(BaseModel):
    """Response with current embedding model configuration (GET /api/embed/config)."""
    model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Current embedding model identifier",
        example="sentence-transformers/all-MiniLM-L6-v2"
    )
    provider: str = Field(
        default="huggingface",
        description="Embedding provider (huggingface, openai, etc.)",
        example="huggingface"
    )
    dimension: int = Field(
        default=384,
        description="Embedding vector dimensionality",
        example=384
    )
    description: str = Field(
        default="Fast, efficient 384-dimensional embeddings",
        description="Model description",
        example="Fast, efficient 384-dimensional embeddings"
    )
    batch_size: Optional[int] = Field(
        default=128,
        description="Maximum batch size for embedding requests",
        example=128
    )
    cache_enabled: Optional[bool] = Field(
        default=True,
        description="Whether embedding cache is enabled",
        example=True
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "provider": "huggingface",
                "dimension": 384,
                "description": "Fast, efficient 384-dimensional embeddings",
                "batch_size": 128,
                "cache_enabled": True
            }
        }
    )


# ============================================================================
# Q&A Models
# ============================================================================


class SourceCitation(BaseModel):
    """Source document cited in Q&A response."""
    url: str = Field(..., description="Source document URL", example="https://example.com/docs/ml-guide")
    title: Optional[str] = Field(default=None, description="Document title", example="Machine Learning Guide")
    chunk_id: Optional[str] = Field(default=None, description="Chunk ID from vector store", example="chunk-456")
    relevance: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Vector similarity score (0-1, higher=more relevant)",
        example=0.95
    )
    excerpt: Optional[str] = Field(
        default=None,
        description="Relevant text excerpt from source",
        example="Machine learning is a branch of artificial intelligence..."
    )


class AskQuestionRequest(BaseModel):
    """Request for Q&A query (GET /api/ask/)."""
    question: str = Field(
        ...,
        description="User's question to answer",
        example="What is machine learning?"
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Conversation thread ID for maintaining context across messages",
        example="conv-session-abc123xyz"
    )
    lang: Optional[str] = Field(
        default=None,
        description="Language code (es=Spanish, en=English). Auto-detected from question if omitted.",
        example="en",
        pattern="^(es|en)?$"
    )
    provider: Optional[str] = Field(
        default=None,
        description="Override LLM provider (groq, openai, etc.)",
        example="groq"
    )
    model: Optional[str] = Field(
        default=None,
        description="Override LLM model name",
        example="llama-3.1-8b-instant"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What is vector embeddings?",
                "thread_id": "conv-session-user-123",
                "lang": "en",
                "provider": "groq",
                "model": "llama-3.1-8b-instant"
            }
        }
    )


class AskQuestionResponse(BaseModel):
    """Response to Q&A query (GET /api/ask/)."""
    question: str = Field(..., description="Original user question", example="What is machine learning?")
    answer: str = Field(
        ...,
        description="Generated answer based on vector search results",
        example="Machine learning is a branch of artificial intelligence that enables systems to learn and improve from experience..."
    )
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="List of source documents cited in the answer"
    )
    language: str = Field(
        ...,
        description="Detected/used language code",
        example="en"
    )
    model: str = Field(
        ...,
        description="LLM model used to generate answer",
        example="llama-3.1-8b-instant"
    )
    response_time_ms: Optional[int] = Field(
        default=None,
        description="Total response time in milliseconds",
        example=2340
    )
    token_usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token usage breakdown (prompt_tokens, completion_tokens, total_tokens)",
        example={
            "prompt_tokens": 512,
            "completion_tokens": 256,
            "total_tokens": 768
        }
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of AI that enables systems to learn and improve from experience...",
                "sources": [
                    {
                        "url": "https://example.com/ml-basics",
                        "title": "ML Basics",
                        "chunk_id": "chunk-001",
                        "relevance": 0.98,
                        "excerpt": "Machine learning enables systems to learn..."
                    }
                ],
                "language": "en",
                "model": "llama-3.1-8b-instant",
                "response_time_ms": 2340,
                "token_usage": {
                    "prompt_tokens": 512,
                    "completion_tokens": 256,
                    "total_tokens": 768
                }
            }
        }
    )


class StreamEventType(str, Enum):
    """Server-Sent Event types for streaming Q&A."""
    THINKING = "thinking"
    COMPLETE = "complete"
    CLARIFICATION = "clarification"
    ERROR = "error"


class ThinkingEvent(BaseModel):
    """Streaming event: intermediate thinking step (GET /api/ask/stream)."""
    type: str = Field(
        default="thinking",
        description="Event type identifier"
    )
    content: str = Field(
        ...,
        description="Thinking step content",
        example="The question asks about vector embeddings. I need to search for relevant docs..."
    )
    step_number: int = Field(
        ...,
        description="Sequential step number",
        example=1
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "thinking",
                "content": "The question asks about vector embeddings. I need to search for relevant docs...",
                "step_number": 1
            }
        }
    )


class CompleteEvent(BaseModel):
    """Streaming event: complete answer with sources (GET /api/ask/stream)."""
    type: str = Field(default="complete", description="Event type identifier")
    answer: str = Field(..., description="Final complete answer")
    sources: List[SourceCitation] = Field(
        default_factory=list,
        description="Source citations"
    )
    response_time_ms: int = Field(..., description="Total response time", example=3200)
    token_usage: Dict[str, int] = Field(
        ...,
        description="Token consumption breakdown",
        example={
            "prompt_tokens": 512,
            "completion_tokens": 256,
            "total_tokens": 768
        }
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "complete",
                "answer": "Vector embeddings are numerical representations of text...",
                "sources": [
                    {
                        "url": "https://example.com/embeddings",
                        "relevance": 0.95
                    }
                ],
                "response_time_ms": 3200,
                "token_usage": {
                    "prompt_tokens": 512,
                    "completion_tokens": 256,
                    "total_tokens": 768
                }
            }
        }
    )


class ClarificationEvent(BaseModel):
    """Streaming event: request for clarification (GET /api/ask/stream)."""
    type: str = Field(default="clarification", description="Event type identifier")
    clarifications: List[str] = Field(
        ...,
        min_length=1,
        description="List of clarifying questions to narrow down the answer",
        example=[
            "Are you asking about embeddings in NLP or general vector embeddings?",
            "Do you want implementation details or conceptual understanding?"
        ]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "clarification",
                "clarifications": [
                    "Are you asking about embeddings in NLP or general vector embeddings?",
                    "Do you want implementation details or conceptual understanding?"
                ]
            }
        }
    )


class StreamErrorEvent(BaseModel):
    """Streaming event: error occurred (GET /api/ask/stream)."""
    type: str = Field(default="error", description="Event type identifier")
    error: str = Field(..., description="Error message", example="No relevant documents found for this question")
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code",
        example="NO_CONTEXT"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "error",
                "error": "No relevant documents found for this question",
                "error_code": "NO_CONTEXT"
            }
        }
    )


class AskConfigResponse(BaseModel):
    """Response with Q&A service configuration (GET /api/ask/config)."""
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en", "es"],
        description="List of supported language codes",
        example=["en", "es"]
    )
    default_language: str = Field(
        default="en",
        description="Default language for questions",
        example="en"
    )
    default_provider: str = Field(
        default="groq",
        description="Default LLM provider",
        example="groq"
    )
    available_models: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of available LLM models with specs"
    )
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "streaming_enabled": True,
            "thread_context": True,
            "model_override": True,
            "web_search": False
        },
        description="Feature availability flags"
    )
    limits: Dict[str, int] = Field(
        default_factory=lambda: {
            "max_question_length": 4000,
            "max_response_tokens": 2048,
            "request_timeout_seconds": 30
        },
        description="Request/response limits"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "supported_languages": ["en", "es"],
                "default_language": "en",
                "default_provider": "groq",
                "available_models": [
                    {
                        "provider": "groq",
                        "name": "llama-3.1-8b-instant",
                        "context_window": 8192,
                        "cost_per_1k_tokens": 0.05
                    }
                ],
                "features": {
                    "streaming_enabled": True,
                    "thread_context": True,
                    "model_override": True,
                    "web_search": False
                },
                "limits": {
                    "max_question_length": 4000,
                    "max_response_tokens": 2048,
                    "request_timeout_seconds": 30
                }
            }
        }
    )


# Backward compatibility aliases
AskRequest = AskQuestionRequest
AskResponse = AskQuestionResponse


# ============================================================================
# Admin Models
# ============================================================================


class AdminConfigResponse(BaseModel):
    """Response with admin configuration (GET /api/admin/config)."""
    require_confirmation: bool = Field(
        default=True,
        description="Require confirmation tokens for destructive operations",
        example=True
    )
    confirmation_token_ttl_seconds: int = Field(
        default=300,
        description="Confirmation token expiration time in seconds",
        example=300
    )
    max_jobs_to_retain: int = Field(
        default=1000,
        description="Maximum scraping jobs to keep in memory",
        example=1000
    )
    auto_cleanup_hours: int = Field(
        default=24,
        description="Auto-cleanup job retention period in hours",
        example=24
    )
    enable_document_deletion: bool = Field(
        default=True,
        description="Allow document deletion via admin endpoint",
        example=True
    )
    enable_database_reset: bool = Field(
        default=False,
        description="Allow full database reset (dangerous!)",
        example=False
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "require_confirmation": True,
                "confirmation_token_ttl_seconds": 300,
                "max_jobs_to_retain": 1000,
                "auto_cleanup_hours": 24,
                "enable_document_deletion": True,
                "enable_database_reset": False
            }
        }
    )


class AdminConfigUpdateRequest(BaseModel):
    """Request to update admin configuration (POST /api/admin/config) - PARTIAL IMPLEMENTATION."""
    require_confirmation: Optional[bool] = Field(
        default=None,
        description="Update confirmation requirement setting",
        example=False
    )
    auto_cleanup_hours: Optional[int] = Field(
        default=None,
        description="Update job retention period (TODO: not yet implemented)",
        example=24
    )
    enable_document_deletion: Optional[bool] = Field(
        default=None,
        description="Allow/disallow document deletion (TODO: not yet implemented)",
        example=True
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "require_confirmation": False
            }
        }
    )


class AdminConfigUpdateResponse(BaseModel):
    """Response from config update (POST /api/admin/config)."""
    updated: bool = Field(..., description="Whether update succeeded", example=True)
    updated_fields: List[str] = Field(
        ...,
        description="Fields that were updated",
        example=["require_confirmation"]
    )
    config: AdminConfigResponse = Field(..., description="Updated configuration")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "updated": True,
                "updated_fields": ["require_confirmation"],
                "config": {
                    "require_confirmation": False,
                    "confirmation_token_ttl_seconds": 300,
                    "max_jobs_to_retain": 1000,
                    "auto_cleanup_hours": 24,
                    "enable_document_deletion": True,
                    "enable_database_reset": False
                }
            }
        }
    )


# NOT YET IMPLEMENTED: Admin endpoints below

class AdminHealthResponse(BaseModel):
    """Response from health check (GET /api/admin/health) - NOT YET IMPLEMENTED."""
    status: str = Field(
        ...,
        description="Overall system health status",
        example="healthy"
    )
    agent_service: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Agent service health details",
        example={
            "status": "ok",
            "response_time_ms": 45,
            "last_check": "2024-02-09T10:30:00Z"
        }
    )
    embedding_service: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Embedding service health details"
    )
    database: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Database health details"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DatabaseStats(BaseModel):
    """Database statistics."""
    total_chunks: int = Field(..., description="Total document chunks", example=45230)
    unique_sources: int = Field(..., description="Unique source URLs", example=892)
    total_embeddings: int = Field(..., description="Total embeddings generated", example=45230)
    average_chunk_size: float = Field(..., description="Mean chunk size bytes", example=2048.5)
    db_size_bytes: Optional[int] = Field(
        default=None,
        description="Total database size in bytes",
        example=92593156
    )
    last_updated: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )


class AdminStatsResponse(BaseModel):
    """Response with admin statistics (GET /api/admin/stats) - NOT YET IMPLEMENTED."""
    database: DatabaseStats = Field(..., description="Database statistics")
    services: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Service metrics",
        example={
            "agent_service": {
                "uptime_seconds": 86400,
                "requests_processed": 5432,
                "average_latency_ms": 245
            },
            "embedding_service": {
                "uptime_seconds": 86400,
                "embeddings_generated": 125600,
                "cache_hit_rate": 0.67
            }
        }
    )


class DocumentChunk(BaseModel):
    """Document chunk metadata."""
    chunk_id: str = Field(..., description="Chunk identifier", example="chunk-abc123")
    source_url: str = Field(..., description="Source document URL")
    content_preview: str = Field(
        ...,
        description="First 200 chars of content",
        example="Machine learning is a branch of artificial intelligence that..."
    )
    embedding_dimension: int = Field(..., description="Embedding dimensionality", example=384)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class DocumentsListResponse(BaseModel):
    """Response listing indexed documents (GET /api/admin/documents) - NOT YET IMPLEMENTED."""
    documents: List[DocumentChunk] = Field(..., description="List of document chunks")
    total: int = Field(..., description="Total chunks in database", example=45230)
    page: int = Field(..., description="Current page number", example=1)
    limit: int = Field(..., description="Results per page", example=20)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "chunk_id": "chunk-001",
                        "source_url": "https://example.com/doc",
                        "content_preview": "Content here...",
                        "embedding_dimension": 384,
                        "created_at": "2024-02-09T10:00:00Z"
                    }
                ],
                "total": 45230,
                "page": 1,
                "limit": 20
            }
        }
    )


class DeleteChunkResponse(BaseModel):
    """Response from delete chunk (DELETE /api/admin/documents/{chunk_id}) - NOT YET IMPLEMENTED."""
    success: bool = Field(..., description="Whether deletion succeeded", example=True)
    deleted_chunk_id: str = Field(..., description="ID of deleted chunk", example="chunk-abc123")
    message: str = Field(..., description="Confirmation message")


class CleanDatabaseRequest(BaseModel):
    """Request to clean database (POST /api/admin/database/clean) - NOT YET IMPLEMENTED."""
    confirmation_token: str = Field(
        ...,
        description="Token obtained from GET /api/admin/database/clean-request",
        example="token-abc123xyz789"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "confirmation_token": "token-abc123xyz789"
            }
        }
    )


class CleanDatabaseResponse(BaseModel):
    """Response from database cleanup (POST /api/admin/database/clean)."""
    success: bool = Field(..., description="Whether cleanup succeeded", example=True)
    deleted_chunks: int = Field(..., description="Count of chunks deleted", example=45230)
    message: str = Field(
        ...,
        description="Cleanup summary",
        example="Database cleaned: 45230 chunks deleted"
    )


class CleanRequestTokenResponse(BaseModel):
    """Response with cleanup confirmation token (GET /api/admin/database/clean-request) - NOT YET IMPLEMENTED."""
    token: str = Field(
        ...,
        description="One-time use confirmation token",
        example="token-abc123xyz789"
    )
    expires_at: datetime = Field(..., description="Token expiration time")
    endpoint: str = Field(
        ...,
        description="Endpoint to use this token with",
        example="POST /api/admin/database/clean"
    )


class SourcesListResponse(BaseModel):
    """Response listing all document sources (GET /api/admin/sources) - NOT YET IMPLEMENTED."""
    sources: List[Dict[str, Any]] = Field(
        ...,
        description="List of unique sources with metadata",
        example=[
            {
                "url": "https://example.com/docs",
                "chunk_count": 125,
                "created_at": "2024-02-09T10:00:00Z",
                "last_updated": "2024-02-09T12:00:00Z"
            }
        ]
    )
    total: int = Field(..., description="Total unique sources", example=892)


class ValidateSourceRequest(BaseModel):
    """Request to validate a source (POST /api/admin/sources/validate) - NOT YET IMPLEMENTED."""
    url: str = Field(
        ...,
        description="URL to validate",
        example="https://example.com"
    )
    loader_type: LoaderType = Field(
        ...,
        description="Loader to test with",
        example=LoaderType.AUTO
    )


class ValidateSourceResponse(BaseModel):
    """Response from source validation (POST /api/admin/sources/validate)."""
    url: str = Field(..., description="URL tested")
    is_accessible: bool = Field(..., description="Whether URL is accessible", example=True)
    is_scrapeable: bool = Field(..., description="Whether content is scrapeable", example=True)
    http_status: Optional[int] = Field(default=None, description="HTTP status code", example=200)
    message: str = Field(
        ...,
        description="Validation result message",
        example="URL is accessible and scrapeable"
    )


# ============================================================================
# Gateway Health & Config Models
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Response from health check endpoint (GET /health)."""
    status: str = Field(
        ...,
        description="Overall health status",
        example="ok"
    )
    agent_service: Optional[str] = Field(
        default=None,
        description="Agent service health status",
        example="ok"
    )
    embedding_service: Optional[str] = Field(
        default=None,
        description="Embedding service health status",
        example="ok"
    )
    database: Optional[str] = Field(
        default=None,
        description="Database health status",
        example="ok"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Check timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "agent_service": "ok",
                "embedding_service": "ok",
                "database": "ok",
                "timestamp": "2024-02-09T10:30:00Z"
            }
        }
    )


class EndpointInfo(BaseModel):
    """Information about a single endpoint."""
    method: str = Field(
        ...,
        description="HTTP method",
        example="GET"
    )
    path: str = Field(
        ...,
        description="Endpoint path",
        example="/api/ask/"
    )
    description: str = Field(
        ...,
        description="Brief endpoint description",
        example="Ask a question and get an answer with sources"
    )
    authentication: bool = Field(
        default=False,
        description="Whether endpoint requires authentication",
        example=False
    )


class GatewayInfoResponse(BaseModel):
    """Response with service information (GET /)."""
    service: str = Field(
        default="Vecinita Unified API Gateway",
        description="Service name"
    )
    version: str = Field(
        default="1.0.0",
        description="API version",
        example="1.0.0"
    )
    status: str = Field(
        default="operational",
        description="Service status",
        example="operational"
    )
    endpoints: Dict[str, List[EndpointInfo]] = Field(
        default_factory=dict,
        description="Endpoints organized by category"
    )
    environment: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment info (deployed_at, region, etc.)",
        example={
            "deployed_at": "2024-02-09T10:00:00Z",
            "region": "us-east-1"
        }
    )

    model_config = ConfigDict(
        json_schema_extra={
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
                            "authentication": False
                        }
                    ]
                },
                "environment": {
                    "deployed_at": "2024-02-09T10:00:00Z",
                    "region": "us-east-1"
                }
            }
        }
    )


class GatewayConfigResponse(BaseModel):
    """Response with gateway configuration (GET /config)."""
    agent_url: str = Field(
        ...,
        description="Agent service URL",
        example="http://localhost:8000"
    )
    embedding_service_url: str = Field(
        ...,
        description="Embedding service URL",
        example="http://localhost:8001"
    )
    database_url: Optional[str] = Field(
        default=None,
        description="Database URL (masked for security)"
    )
    max_urls_per_request: int = Field(
        ...,
        description="Max URLs per scrape request",
        example=100
    )
    job_retention_hours: int = Field(
        ...,
        description="Job history retention period in hours",
        example=24
    )
    embedding_model: str = Field(
        ...,
        description="Default embedding model",
        example="sentence-transformers/all-MiniLM-L6-v2"
    )
    auth_enabled: bool = Field(
        default=False,
        description="Whether authentication is required",
        example=False
    )
    rate_limiting: Optional[Dict[str, int]] = Field(
        default=None,
        description="Rate limit configuration",
        example={
            "requests_per_hour": 100,
            "tokens_per_day": 1000
        }
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_url": "http://localhost:8000",
                "embedding_service_url": "http://localhost:8001",
                "database_url": None,
                "max_urls_per_request": 100,
                "job_retention_hours": 24,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "auth_enabled": False,
                "rate_limiting": {
                    "requests_per_hour": 100,
                    "tokens_per_day": 1000
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(
        ...,
        description="Error type/message",
        example="Not Found"
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error explanation",
        example="The requested resource was not found"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Not Found",
                "detail": "The requested resource was not found",
                "timestamp": "2024-02-09T10:30:00Z"
            }
        }
    )


# Backward compatibility aliases
HealthCheck = HealthCheckResponse
GatewayConfig = GatewayConfigResponse

# ============================================================================
# API ENDPOINT DOCUMENTATION & STATUS SUMMARY
# ============================================================================
"""
COMPREHENSIVE ENDPOINT STATUS & DOCUMENTATION
==============================================

This documentation is automatically exposed in FastAPI Swagger UI at /docs
All models above are used to generate OpenAPI schemas with full descriptions and examples.

ACTIVE ENDPOINTS (12 total) ✅
=====================================

Q&A ROUTER (/api/ask/) - 3 ACTIVE
  ✅ GET  /              → AskQuestionRequest query params → AskQuestionResponse
  ✅ GET  /stream        → Query params (same as /) → SSE stream [ThinkingEvent, CompleteEvent, ClarificationEvent, StreamErrorEvent]
  ✅ GET  /config        → (no params) → AskConfigResponse

SCRAPING ROUTER (/api/scrape/) - 6 ENDPOINTS (5 partial, 1 callback)
  ⚠️  POST /             → ScrapeStartRequest → ScrapeInitResponse (job management ✅, scraper integration TODO)
  ⚠️  GET  /{job_id}     → (no body) → ScrapeStatusResponse
  ⚠️  POST /{job_id}/cancel → (no body) → ScrapeCancelResponse
  ⚠️  GET  /history      → ScrapeHistoryRequest query params → ScrapeHistoryResponse
  ⚠️  GET  /stats        → (no params) → ScrapeStatsResponse
  ⚠️  POST /cleanup      → ScrapeCleanupRequest → ScrapeCleanupResponse

EMBEDDINGS ROUTER (/api/embed/) - 1 ACTIVE
  ✅ GET  /config        → (no params) → EmbeddingConfigResponse (hardcoded HuggingFace config)

ADMIN ROUTER (/api/admin/) - 2 PARTIAL
  ⚠️  GET  /config       → (no params) → AdminConfigResponse
  ⚠️  POST /config       → AdminConfigUpdateRequest → AdminConfigUpdateResponse (only updates require_confirmation)

GATEWAY ROOT ENDPOINTS - 3 ENDPOINTS
  ✅ GET  /              → (no params) → GatewayInfoResponse
  ✅ GET  /config        → (no params) → GatewayConfigResponse
  ⚠️  GET  /health       → (no params) → HealthCheckResponse (hardcoded, should probe services)


NOT IMPLEMENTED ENDPOINTS (8 total) ❌
=====================================

EMBEDDINGS ROUTER (/api/embed/) - 5 ACTIVE (Phase 5 Complete)
  ✅ POST /             → EmbedRequest → EmbedResponse (proxies to embedding service)
  ✅ POST /batch        → EmbedBatchRequest → EmbedBatchResponse (proxies to embedding service)
  ✅ POST /similarity   → SimilarityRequest → SimilarityResponse (generates embeddings + computes cosine similarity)
  ✅ GET  /config       → (no params) → EmbeddingConfigResponse (returns current config)
  ✅ POST /config       → Query params (provider, model, lock) → EmbeddingConfigResponse (updates embedding service config)

ADMIN ROUTER (/api/admin/) - 8 ACTIVE (Phase 4 Complete)
  ✅ GET  /health       → (no params) → AdminHealthResponse (checks agent, embedding, database)
  ✅ GET  /stats        → (no params) → AdminStatsResponse (database statistics)
  ✅ GET  /documents    → Query params (limit, offset, source_filter) → DocumentsListResponse (paginated list)
  ✅ DELETE /documents/{chunk_id} → (no body) → DeleteChunkResponse (deletes specific chunk)
  ✅ POST /database/clean → CleanDatabaseRequest → CleanDatabaseResponse (requires confirmation token)
  ✅ GET  /database/clean-request → (no params) → CleanRequestTokenResponse (generates token)
  ✅ GET  /sources      → (no params) → SourcesListResponse (lists all sources with counts)
  ✅ POST /sources/validate → ValidateSourceRequest → ValidateSourceResponse (tests URL accessibility)

SCRAPING ROUTER - 1 CRITICAL GAP (Phase 6 Pending)
  ⚠️  Background task: Job creation framework is complete, but background_scrape_task()
      in router_scrape.py lacks actual scraper integration (TODO: import VecinaScraper)



SWAGGER/OPENAPI DOCUMENTATION
=============================

All models above are automatically documented in Swagger UI:
  - Navigate to: http://localhost:8002/docs
  - Each model shows:
    * Field names and types
    * Description text (from Field description=)
    * Example values (from Field example= and model_config json_schema_extra)
    * Validation constraints (min_length, max, pattern, etc.)
    * Default values
    * Required vs optional fields

The OpenAPI schema is available at: http://localhost:8002/openapi.json


CURL REFERENCE EXAMPLES
========================

Ask Question:
  curl -X GET 'http://localhost:8002/api/ask/?question=What%20is%20AI&lang=en'

Stream Question (SSE):
  curl -X GET 'http://localhost:8002/api/ask/stream?question=What%20is%20AI'

Get Q&A Config:
  curl -X GET 'http://localhost:8002/api/ask/config'

Start Web Scraping:
  curl -X POST 'http://localhost:8002/api/scrape' \\
    -H 'Content-Type: application/json' \\
    -d '{"urls":["https://example.com"],"force_loader":"auto"}'

Check Scrape Status:
  curl -X GET 'http://localhost:8002/api/scrape/scrape-job-abc123xyz'

Cancel Scrape Job:
  curl -X POST 'http://localhost:8002/api/scrape/scrape-job-abc123xyz/cancel' \\
    -H 'Content-Type: application/json'

Get Scrape History:
  curl -X GET 'http://localhost:8002/api/scrape/history?page=1&limit=10'

Get Scrape Stats:
  curl -X GET 'http://localhost:8002/api/scrape/stats'

Clean Old Jobs:
  curl -X POST 'http://localhost:8002/api/scrape/cleanup' \\
    -H 'Content-Type: application/json' \\
    -d '{"hours_old":24,"dry_run":false}'

Get Embedding Config:
  curl -X GET 'http://localhost:8002/api/embed/config'

Get Admin Config:
  curl -X GET 'http://localhost:8002/api/admin/config' \\
    -H 'Authorization: Bearer <api-key>'

Update Admin Config:
  curl -X POST 'http://localhost:8002/api/admin/config' \\
    -H 'Content-Type: application/json' \\
    -H 'Authorization: Bearer <api-key>' \\
    -d '{"require_confirmation":false}'

Get Gateway Info:
  curl -X GET 'http://localhost:8002/'

Get Gateway Config:
  curl -X GET 'http://localhost:8002/config'

Health Check:
  curl -X GET 'http://localhost:8002/health'


BACKWARD COMPATIBILITY ALIASES
===============================

For migration/compatibility with existing code:
  - ScrapeRequest → Use ScrapeStartRequest instead
  - AskRequest → Use AskQuestionRequest instead
  - AskResponse → Use AskQuestionResponse instead
  - HealthCheck → Use HealthCheckResponse instead
  - GatewayConfig → Use GatewayConfigResponse instead

Old names still resolve to new models but are deprecated in favor of the new explicit names.


IMPLEMENTATION NOTES & TODOS
============================

1. CRITICAL: Embed Endpoints (5 endpoints)
   - Status: All return 501 Not Implemented
   - Required: Integrate with embedding service at EMBEDDING_SERVICE_URL
   - Expected: Delegate model/inference to external service or Modal function

2. SCRAPING Background Task
   - Status: Job framework complete (create, track, poll), actual scraping TODO
   - Required: Import VecinaScraper and invoke from background_scrape_task()
   - File: backend/src/api/router_scrape.py line ~120 has placeholder

3. Admin Endpoints (8 endpoints)
   - Status: All return 501 Not Implemented except config GET/POST
   - Required: Database queries to Supabase for documents, stats, sources
   - Required: Implement cleanup token generation and validation

4. Health Checks
   - Status: /health returns hardcoded "ok"
   - Required: Actually probe agent_service, embedding_service, database
   - File: backend/src/api/main.py lifespan startup event

5. Rate Limiting & Auth
   - Status: Middleware exists, in-memory state
   - Required: Use Redis for distributed deployments
   - File: backend/src/api/middleware.py

6. Job Persistence
   - Status: In-memory AsyncJobManager
   - Required: Persist to Redis or database for production
   - File: backend/src/api/job_manager.py

"""

"""Gateway models — embeddings."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# Embedding Models
# ============================================================================


class EmbedRequest(BaseModel):
    """Request body for ``POST /api/v1/embed`` (gateway proxy to embedding service)."""

    text: str = Field(
        ...,
        min_length=1,
        description="Text or query to embed (non-empty).",
        examples=[
            "The quick brown fox jumps over the lazy dog",
            "Community clinic walk-in hours and eligibility.",
        ],
        validation_alias=AliasChoices("text", "query"),
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional embedding model id; server default is used when omitted.",
        examples=["sentence-transformers/all-MiniLM-L6-v2", "BAAI/bge-small-en-v1.5"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"text": "The quick brown fox jumps over the lazy dog", "model": None},
                {
                    "text": "Summarize tenant rights for informal housing.",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text": "Where can I renew a municipal ID card downtown?",
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {"text": "SNAP interview checklist for first-time applicants", "model": None},
                {
                    "text": "After-school program enrollment deadlines spring 2026",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "text": "The quick brown fox jumps over the lazy dog",
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class EmbedBatchRequest(BaseModel):
    """Request body for ``POST /api/v1/embed/batch`` (gateway proxy to embedding service)."""

    texts: list[str] = Field(
        ...,
        min_length=1,
        description="Non-empty list of texts to embed (upstream service may enforce a batch limit).",
        examples=[
            ["First document to embed", "Second document to embed", "Third document to embed"]
        ],
        validation_alias=AliasChoices("texts", "queries"),
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional embedding model id; server default is used when omitted.",
    )

    @field_validator("texts")
    @classmethod
    def texts_must_be_non_whitespace(cls, value: list[str]) -> list[str]:
        """Reject empty or whitespace-only entries (aligns with embedding service validation)."""
        for item in value:
            if not item.strip():
                raise ValueError("Each text must be non-empty and not whitespace-only.")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "texts": ["Short note one", "Short note two"],
                    "model": None,
                },
                {
                    "texts": [
                        "First document to embed",
                        "Second document to embed",
                        "Third document to embed",
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "texts": [
                        "Clinic hours: Mon–Fri 8am–5pm.",
                        "Walk-ins accepted for flu shots.",
                    ],
                    "model": None,
                },
                {
                    "texts": [
                        "Eviction moratorium FAQ paragraph one.",
                        "Eviction moratorium FAQ paragraph two.",
                        "Eviction moratorium FAQ paragraph three.",
                    ],
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "texts": [
                        "Bus route 14 stops near the food pantry.",
                        "Last pickup Sunday is 6:15pm at Main St.",
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "texts": [
                    "First document to embed",
                    "Second document to embed",
                    "Third document to embed",
                ],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class EmbedResponse(BaseModel):
    """Response with embedding vector (POST /api/embed/)."""

    text: str = Field(..., description="Original text that was embedded")
    embedding: list[float] = Field(
        ...,
        description="384-dimensional embedding vector from HuggingFace sentence-transformers",
        examples=[[0.123, -0.456, 0.789]],
    )
    model: str = Field(
        ...,
        description="Model used for embedding",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    dimension: int = Field(..., description="Embedding dimensionality", examples=[384])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "The quick brown fox",
                    "embedding": [0.1, -0.2, 0.3],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "text": "SNAP office intake hours",
                    "embedding": [0.01, 0.02, -0.03],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "text": "Tenant rights workshop RSVP",
                    "embedding": [-0.5, 0.0, 0.4],
                    "model": "BAAI/bge-small-en-v1.5",
                    "dimension": 384,
                },
                {
                    "text": "Cooling center map legend",
                    "embedding": [0.2, 0.2, 0.2],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "text": "Bus pass discount for seniors",
                    "embedding": [0.0, 0.1, -0.1],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
            ],
            "example": {
                "text": "The quick brown fox",
                "embedding": [0.123, -0.456, 0.789, "... 381 more values ..."],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
            },
        }
    )


class EmbedBatchResponse(BaseModel):
    """Response with batch embeddings (POST /api/embed/batch)."""

    embeddings: list[EmbedResponse] = Field(..., description="List of embedding responses")
    model: str = Field(
        ..., description="Model used", examples=["sentence-transformers/all-MiniLM-L6-v2"]
    )
    dimension: int = Field(..., description="Embedding dimensionality", examples=[384])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "embeddings": [
                        {
                            "text": "First document",
                            "embedding": [0.1, -0.1],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                        {
                            "text": "Second document",
                            "embedding": [0.2, 0.0],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "Clinic triage",
                            "embedding": [0.0, 0.05],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        }
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "Line A",
                            "embedding": [1.0, 0.0],
                            "model": "BAAI/bge-small-en-v1.5",
                            "dimension": 384,
                        },
                        {
                            "text": "Line B",
                            "embedding": [0.0, 1.0],
                            "model": "BAAI/bge-small-en-v1.5",
                            "dimension": 384,
                        },
                        {
                            "text": "Line C",
                            "embedding": [-1.0, 0.0],
                            "model": "BAAI/bge-small-en-v1.5",
                            "dimension": 384,
                        },
                    ],
                    "model": "BAAI/bge-small-en-v1.5",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "Housing lottery",
                            "embedding": [0.3, 0.3],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                        {
                            "text": "Food pantry hours",
                            "embedding": [-0.3, 0.3],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        },
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
                {
                    "embeddings": [
                        {
                            "text": "School enrollment",
                            "embedding": [0.01],
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "dimension": 384,
                        }
                    ],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimension": 384,
                },
            ],
            "example": {
                "embeddings": [
                    {
                        "text": "First document",
                        "embedding": ["... 384 dims ..."],
                        "model": "...",
                        "dimension": 384,
                    },
                    {
                        "text": "Second document",
                        "embedding": ["... 384 dims ..."],
                        "model": "...",
                        "dimension": 384,
                    },
                ],
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "dimension": 384,
            },
        }
    )


class SimilarityRequest(BaseModel):
    """Request body for ``POST /api/v1/embed/similarity`` (cosine similarity via embedding service)."""

    text1: str = Field(
        ...,
        min_length=1,
        description="First text to embed and compare.",
        examples=["Machine learning is AI", "Tenant organizing workshop next Tuesday."],
    )
    text2: str = Field(
        ...,
        min_length=1,
        description="Second text to embed and compare.",
        examples=["Deep learning is machine learning", "RSVP for the housing rights clinic."],
    )
    model: str | None = Field(
        default=None,
        max_length=200,
        description="Optional embedding model id; server default is used when omitted.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text1": "Machine learning is AI",
                    "text2": "Deep learning is machine learning",
                    "model": None,
                },
                {
                    "text1": "Where can I get a flu shot?",
                    "text2": "Community health center offers walk-in vaccines.",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Rent increase notice 30 days",
                    "text2": "Tenant rights when landlord raises rent",
                    "model": None,
                },
                {
                    "text1": "Summer cooling center locations",
                    "text2": "City opens libraries as heat relief sites",
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "text1": "Food bank Tuesday distribution",
                    "text2": "Weekly grocery pickup for registered households",
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "text1": "Machine learning is AI",
                "text2": "Deep learning is machine learning",
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
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
        examples=[0.87],
    )
    model: str = Field(
        ..., description="Model used", examples=["sentence-transformers/all-MiniLM-L6-v2"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text1": "Machine learning is AI",
                    "text2": "Deep learning is machine learning",
                    "similarity": 0.87,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Flu shot walk-in",
                    "text2": "Vaccine clinic same day",
                    "similarity": 0.72,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Unrelated topic A",
                    "text2": "Different domain B",
                    "similarity": 0.05,
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "text1": "Rent control basics",
                    "text2": "Tenant protection overview",
                    "similarity": 0.91,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "text1": "Bus route 14",
                    "text2": "Transit map downtown",
                    "similarity": 0.55,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ],
            "example": {
                "text1": "Machine learning is AI",
                "text2": "Deep learning is machine learning",
                "similarity": 0.87,
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    )


class EmbeddingConfigResponse(BaseModel):
    """Response with current embedding model configuration (GET /api/embed/config)."""

    model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Current embedding model identifier",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    provider: str = Field(
        default="huggingface",
        description="Embedding provider name",
        examples=["huggingface"],
    )
    dimension: int = Field(
        default=384, description="Embedding vector dimensionality", examples=[384]
    )
    description: str = Field(
        default="Fast, efficient 384-dimensional embeddings",
        description="Model description",
        examples=["Fast, efficient 384-dimensional embeddings"],
    )
    batch_size: int | None = Field(
        default=128, description="Maximum batch size for embedding requests", examples=[128]
    )
    cache_enabled: bool | None = Field(
        default=True, description="Whether embedding cache is enabled", examples=[True]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "Fast, efficient 384-dimensional embeddings",
                    "batch_size": 128,
                    "cache_enabled": True,
                },
                {
                    "model": "BAAI/bge-small-en-v1.5",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "Small English retrieval model",
                    "batch_size": 64,
                    "cache_enabled": True,
                },
                {
                    "model": "intfloat/e5-small-v2",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "E5 small for dense retrieval",
                    "batch_size": 32,
                    "cache_enabled": False,
                },
                {
                    "model": "sentence-transformers/all-mpnet-base-v2",
                    "provider": "huggingface",
                    "dimension": 768,
                    "description": "Higher quality, larger vectors",
                    "batch_size": 16,
                    "cache_enabled": True,
                },
                {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "provider": "huggingface",
                    "dimension": 384,
                    "description": "Default staging profile",
                    "batch_size": None,
                    "cache_enabled": None,
                },
            ],
            "example": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "provider": "huggingface",
                "dimension": 384,
                "description": "Fast, efficient 384-dimensional embeddings",
                "batch_size": 128,
                "cache_enabled": True,
            },
        }
    )

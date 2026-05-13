from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QueryRequest(BaseModel):
    """Request model for embedding a single natural language query."""

    query: str | None = Field(
        default=None,
        description="Primary text field (gateway and legacy clients).",
        examples=["What housing assistance programs exist in Alameda County?"],
    )
    text: str | None = Field(
        default=None,
        description="Alias used by some callers (matches backend embedding service).",
        examples=["Affordable childcare waitlist policy"],
    )
    model: str | None = Field(
        default=None,
        description=(
            "Optional embedding model name. Defaults to the server's configured model."
        ),
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )

    @model_validator(mode="after")
    def require_query_or_text(self) -> "QueryRequest":
        if self.query is None and self.text is None:
            raise ValueError("Provide query or text.")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What housing assistance programs exist in this county?",
                    "text": None,
                    "model": None,
                },
                {
                    "query": None,
                    "text": "Legacy single-field body for embedding service parity.",
                    "model": None,
                },
                {
                    "query": "SNAP office hours walk-in policy",
                    "text": None,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "query": None,
                    "text": "Cooling center locations during heat advisories",
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "query": "Tenant rights workshop RSVP deadline",
                    "text": None,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
            ]
        }
    )


class BatchQueryRequest(BaseModel):
    """Request model for embedding a batch of natural language queries."""

    queries: list[str] | None = Field(
        default=None,
        description="List of queries (preferred field name).",
        examples=[["First short query", "Second short query"]],
    )
    texts: list[str] | None = Field(
        default=None,
        description=(
            "Alias used by gateway fallback (matches backend ``/embed-batch``)."
        ),
        examples=[["Legacy batch line one", "Legacy batch line two"]],
    )
    model: str | None = Field(
        default=None,
        description=(
            "Optional embedding model name. Defaults to the server's configured model."
        ),
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )

    @model_validator(mode="after")
    def require_queries_or_texts(self) -> "BatchQueryRequest":
        items = self.queries if self.queries is not None else self.texts
        if not items or len(items) < 1:
            raise ValueError("Provide non-empty queries or texts.")
        normalized: list[str] = list(items)
        for q in normalized:
            if not q.strip():
                raise ValueError(
                    "Each query must be non-empty and not whitespace-only."
                )
        return self.model_copy(update={"queries": normalized})

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "queries": [
                        "First housing intake question",
                        "Second housing intake question",
                    ],
                    "texts": None,
                    "model": None,
                },
                {
                    "queries": None,
                    "texts": ["Legacy batch line one", "Legacy batch line two"],
                    "model": None,
                },
                {
                    "queries": [
                        "WIC eligibility",
                        "WIC appointment documents",
                        "WIC clinic phone",
                    ],
                    "texts": None,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "queries": [
                        "Bus pass discount for seniors",
                        "Reduced fare application site",
                    ],
                    "texts": None,
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "queries": [
                        "Food bank Tuesday hours",
                        "Food bank address",
                        "Food bank ID requirements",
                    ],
                    "texts": None,
                    "model": None,
                },
            ]
        }
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "queries": [
                        "First housing intake question",
                        "Second housing intake question",
                    ],
                    "texts": None,
                    "model": None,
                },
                {
                    "queries": None,
                    "texts": ["Legacy batch line one", "Legacy batch line two"],
                    "model": None,
                },
                {
                    "queries": [
                        "WIC eligibility",
                        "WIC appointment documents",
                        "WIC clinic phone",
                    ],
                    "texts": None,
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                },
                {
                    "queries": [
                        "Bus pass discount for seniors",
                        "Reduced fare application site",
                    ],
                    "texts": None,
                    "model": "BAAI/bge-small-en-v1.5",
                },
                {
                    "queries": [
                        "Food bank Tuesday hours",
                        "Food bank address",
                        "Food bank ID requirements",
                    ],
                    "texts": None,
                    "model": None,
                },
            ]
        }
    )


class EmbeddingResponse(BaseModel):
    """Response model for a single query embedding."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "embedding": [0.01, -0.02, 0.03],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensions": 384,
                },
                {
                    "embedding": [0.1, 0.0, -0.1],
                    "model": "BAAI/bge-small-en-v1.5",
                    "dimensions": 384,
                },
                {
                    "embedding": [-0.5, 0.2],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensions": 384,
                },
                {
                    "embedding": [0.0, 0.0, 0.01],
                    "model": "intfloat/e5-small-v2",
                    "dimensions": 384,
                },
                {
                    "embedding": [0.3, -0.3, 0.0],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensions": 384,
                },
            ]
        }
    )

    embedding: list[float] = Field(
        ...,
        description="The embedding vector.",
        examples=[[0.01, -0.02, 0.03]],
    )
    model: str = Field(
        ...,
        description="The model used to generate the embedding.",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    dimensions: int = Field(
        ...,
        description="The number of dimensions in the embedding.",
        examples=[384],
    )


class BatchEmbeddingResponse(BaseModel):
    """Response model for a batch of query embeddings."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "embeddings": [[0.01, -0.02], [0.0, 0.05]],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensions": 384,
                },
                {
                    "embeddings": [[0.1, 0.1]],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensions": 384,
                },
                {
                    "embeddings": [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]],
                    "model": "BAAI/bge-small-en-v1.5",
                    "dimensions": 384,
                },
                {
                    "embeddings": [[0.0], [0.02], [-0.02]],
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "dimensions": 384,
                },
                {
                    "embeddings": [[0.2, -0.1, 0.0]],
                    "model": "intfloat/e5-small-v2",
                    "dimensions": 384,
                },
            ]
        }
    )

    embeddings: list[list[float]] = Field(
        ...,
        description="The list of embedding vectors.",
        examples=[[[0.01, -0.02], [0.0, 0.05]]],
    )
    model: str = Field(
        ...,
        description="The model used to generate the embeddings.",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )
    dimensions: int = Field(
        ...,
        description="The number of dimensions in each embedding.",
        examples=[384],
    )


class EmbeddingServiceRootResponse(BaseModel):
    """`GET /` — service heartbeat and configured default model."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "ok", "model": "sentence-transformers/all-MiniLM-L6-v2"},
                {"status": "ok", "model": "BAAI/bge-small-en-v1.5"},
                {"status": "ok", "model": "intfloat/e5-small-v2"},
                {"status": "ok", "model": "sentence-transformers/all-mpnet-base-v2"},
                {
                    "status": "ok",
                    "model": "sentence-transformers/paraphrase-MiniLM-L3-v2",
                },
            ]
        }
    )

    status: str = Field(..., description="Liveness flag.", examples=["ok"])
    model: str = Field(
        ...,
        description="Default embedding model for this deployment.",
        examples=["sentence-transformers/all-MiniLM-L6-v2"],
    )


class EmbeddingLivenessResponse(BaseModel):
    """`GET /health` — minimal JSON for probes."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "ok"},
                {"status": "starting"},
                {"status": "ready"},
                {"status": "degraded"},
                {"status": "error"},
            ]
        }
    )

    status: str = Field(..., description="Liveness flag.", examples=["ok"])

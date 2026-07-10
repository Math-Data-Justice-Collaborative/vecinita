"""Modal playground LLM model list + pull models (ADR-035 section 6, RD-139-141)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PlaygroundModelPullStatus = Literal["pulling", "available"]


class PlaygroundModelSummary(BaseModel):
    """One model entry from the Modal playground LLM volume."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=128)
    available: bool


class PlaygroundModelListResponse(BaseModel):
    """GET /internal/v1/models/ollama response."""

    model_config = ConfigDict(extra="forbid")

    items: list[PlaygroundModelSummary]


class PlaygroundModelPullRequest(BaseModel):
    """POST /internal/v1/models/ollama/pull body."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=128)


class PlaygroundModelPullResponse(BaseModel):
    """POST /internal/v1/models/ollama/pull response."""

    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    model_id: str = Field(min_length=1, max_length=128)
    status: PlaygroundModelPullStatus


class PlaygroundModelCatalogFamily(BaseModel):
    """One model family slug from ollama.com/library."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=128)


class PlaygroundModelCatalogFamiliesResponse(BaseModel):
    """GET /internal/v1/models/ollama/catalog response."""

    model_config = ConfigDict(extra="forbid")

    families: list[PlaygroundModelCatalogFamily]


class PlaygroundModelCatalogTag(BaseModel):
    """One downloadable tag under a model family."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=128)
    available: bool


class PlaygroundModelCatalogFamilyTagsResponse(BaseModel):
    """GET /internal/v1/models/ollama/catalog/{slug} response."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=128)
    tags: list[PlaygroundModelCatalogTag]

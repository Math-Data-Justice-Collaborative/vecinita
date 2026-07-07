"""Modal Ollama model list + pull models (ADR-035 section 6, RD-139-141)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OllamaModelPullStatus = Literal["pulling", "available"]


class OllamaModelSummary(BaseModel):
    """One model entry from the Modal Ollama volume."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=128)
    available: bool


class OllamaModelListResponse(BaseModel):
    """GET /internal/v1/models/ollama response."""

    model_config = ConfigDict(extra="forbid")

    items: list[OllamaModelSummary]


class OllamaModelPullRequest(BaseModel):
    """POST /internal/v1/models/ollama/pull body."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=128)


class OllamaModelPullResponse(BaseModel):
    """POST /internal/v1/models/ollama/pull response."""

    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    model_id: str = Field(min_length=1, max_length=128)
    status: OllamaModelPullStatus


class OllamaModelCatalogFamily(BaseModel):
    """One model family slug from ollama.com/library."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=128)


class OllamaModelCatalogFamiliesResponse(BaseModel):
    """GET /internal/v1/models/ollama/catalog response."""

    model_config = ConfigDict(extra="forbid")

    families: list[OllamaModelCatalogFamily]


class OllamaModelCatalogTag(BaseModel):
    """One downloadable tag under a model family."""

    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=128)
    available: bool


class OllamaModelCatalogFamilyTagsResponse(BaseModel):
    """GET /internal/v1/models/ollama/catalog/{slug} response."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=128)
    tags: list[OllamaModelCatalogTag]

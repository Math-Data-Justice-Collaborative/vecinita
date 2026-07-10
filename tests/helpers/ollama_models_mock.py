"""Mock Ollama models client for integration tests (TC-134)."""

from __future__ import annotations

from uuid import uuid4

from vecinita_shared_schemas.ollama_models import (
    OllamaModelListResponse,
    OllamaModelPullResponse,
    OllamaModelSummary,
)


class MockOllamaModelsClient:
    """In-memory stand-in for Modal Ollama list/pull API."""

    def __init__(self) -> None:
        """Seed with the default playground model."""
        self.models: list[OllamaModelSummary] = [
            OllamaModelSummary(model_id="qwen2.5:1.5b-instruct", available=True),
        ]
        self.pull_requests: list[str] = []

    def list_models(self) -> OllamaModelListResponse:
        """Return the in-memory model catalog."""
        return OllamaModelListResponse(items=list(self.models))

    def start_pull(self, model_id: str) -> OllamaModelPullResponse:
        """Record a pull request and return a pending job response."""
        self.pull_requests.append(model_id)
        if not any(entry.model_id == model_id for entry in self.models):
            self.models.append(OllamaModelSummary(model_id=model_id, available=False))
        return OllamaModelPullResponse(
            job_id=uuid4(),
            model_id=model_id,
            status="pulling",
        )

    def close(self) -> None:
        """Match LlmClient lifecycle for create_app teardown."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.fakes import FakeEmbedder
from vecinita.api import create_app
from vecinita.service import EmbeddingService


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def service(fake_embedder: FakeEmbedder) -> EmbeddingService:
    return EmbeddingService(fake_embedder)


@pytest.fixture
def client(service: EmbeddingService) -> TestClient:
    return TestClient(create_app(service))

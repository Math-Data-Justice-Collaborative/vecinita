"""Contract sync tests for backend embedding models vs service schemas.

These tests ensure backend request/response models remain compatible with the
canonical service contracts exposed by services/embedding-modal.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from src.api.models import EmbedBatchRequest, EmbedRequest, EmbedResponse

pytestmark = pytest.mark.unit


def _load_embedding_service_schemas_module():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "services" / "embedding-modal" / "src" / "vecinita" / "schemas.py"

    spec = importlib.util.spec_from_file_location("embedding_modal_schemas", module_path)
    assert spec and spec.loader, f"Unable to load service schemas from {module_path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_backend_embed_request_accepts_canonical_service_field_name() -> None:
    request = EmbedRequest.model_validate({"query": "hello vecinita"})

    assert request.text == "hello vecinita"


def test_backend_embed_batch_request_accepts_canonical_service_field_name() -> None:
    request = EmbedBatchRequest.model_validate({"queries": ["uno", "dos"]})

    assert request.texts == ["uno", "dos"]


def test_service_request_field_names_remain_supported_by_backend_models() -> None:
    schemas = _load_embedding_service_schemas_module()

    service_query_request = schemas.QueryRequest(query="hola")
    service_batch_request = schemas.BatchQueryRequest(queries=["hola", "adios"])

    backend_single = EmbedRequest.model_validate(service_query_request.model_dump())
    backend_batch = EmbedBatchRequest.model_validate(service_batch_request.model_dump())

    assert backend_single.text == "hola"
    assert backend_batch.texts == ["hola", "adios"]


def test_backend_embed_response_accepts_service_dimensions_field() -> None:
    service_like_payload = {
        "embedding": [0.1, 0.2, 0.3],
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimensions": 3,
    }

    response = EmbedResponse(
        text="sample",
        embedding=service_like_payload["embedding"],
        model=service_like_payload["model"],
        dimension=service_like_payload["dimensions"],
    )

    assert response.dimension == 3

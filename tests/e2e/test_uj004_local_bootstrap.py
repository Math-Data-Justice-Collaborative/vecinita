"""UJ-004 / TC-020: local bootstrap smoke (docker-compose + migrations + seed)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
import yaml
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_database.seeds.load import load_corpus
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_shared_schemas.json_types import as_json_object

from tests.e2e.local_bootstrap import (
    default_database_url,
    postgres_is_ready,
    run_alembic_upgrade_head,
)
from tests.helpers.json_response import json_int, json_object_get, json_str, response_json_object
from tests.unit.rag.conftest import attach_embeddings, basis_vector

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VECINITA_YAML = _REPO_ROOT / "infra" / "vecinita.yaml"


class _MockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        return "Local bootstrap smoke answer."

    def generate_stream(self, prompt: str, **kwargs: object):
        yield "Local "
        yield "bootstrap "
        yield "smoke."

    def close(self) -> None:
        return None


@pytest.fixture(scope="module")
def bootstrapped_stack() -> str:
    if not postgres_is_ready():
        pytest.skip(
            "Postgres not available — run: docker compose -f infra/docker-compose.yml up -d postgres"
        )

    url = default_database_url()
    run_alembic_upgrade_head(url)
    load_corpus(database_url=url)
    attach_embeddings(
        database_url=url,
        match_substrings={"Food pantry": 0, "banco de alimentos": 2},
        default_index=1,
    )
    return url


@pytest.fixture
def bootstrap_client(bootstrapped_stack: str) -> TestClient:
    settings = ChatRagSettings(
        database_url=bootstrapped_stack,
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=settings.database_url,
        top_k=settings.top_k,
    )
    service = ChatRagService(retriever=retriever, llm_client=_MockLlmClient())  # type: ignore[arg-type]
    return TestClient(create_app(settings=settings, chat_service=service))


def test_vecinita_yaml_documents_local_defaults() -> None:
    assert _VECINITA_YAML.is_file(), (
        "infra/vecinita.yaml required for local defaults (config-spec.md)"
    )
    data = as_json_object(
        cast("object", yaml.safe_load(_VECINITA_YAML.read_text(encoding="utf-8")))
    )
    assert data["env"] == "development"
    chat_rag = json_object_get(data, "chat_rag")
    assert json_int(chat_rag, "top_k") == 5
    services = json_object_get(data, "services")
    assert "localhost" in json_str(services, "chat_rag_backend")


def test_uj004_bootstrap_health_and_ask(bootstrap_client: TestClient) -> None:
    health = bootstrap_client.get("/health")
    assert health.status_code == 200
    body = response_json_object(health)
    assert body["status"] == "ok"
    dependencies = json_object_get(body, "dependencies")
    assert json_str(dependencies, "postgres") == "ok"

    ask = bootstrap_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert ask.status_code == 200
    payload = response_json_object(ask)
    assert payload["language"] == "en"
    assert payload["answer"]
    assert isinstance(payload["sources"], list)

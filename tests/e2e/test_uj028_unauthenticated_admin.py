"""UJ-028 / TC-078 / TC-083: unauthenticated admin requests rejected; ChatRAG stays anonymous."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever

from tests.helpers.json_response import response_json_object
from tests.unit.rag.conftest import basis_vector, seed_corpus_with_embeddings
from tests.unit.shared_schemas.auth_fixtures import sign_test_jwt

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey

pytestmark = pytest.mark.e2e


class _MockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        return "The food pantry posts hours on the city website each Monday."

    def generate_stream(self, prompt: str, **kwargs: object):
        yield "The food pantry posts hours."

    def close(self) -> None:
        return None


@pytest.fixture
def chat_anonymous_client() -> TestClient:
    """ChatRAG app — no auth layer (F34 regression: stays anonymous)."""
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    seed_corpus_with_embeddings(
        database_url=db_url,
        match_substrings={"Food pantry": 0},
        default_index=0,
    )
    settings = ChatRagSettings(
        database_url=db_url,
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        browse_page_size=20,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=settings.database_url,
        top_k=settings.top_k,
    )
    service = ChatRagService(retriever=retriever, llm_client=_MockLlmClient())  # type: ignore[arg-type]
    return TestClient(create_app(settings=settings, chat_service=service))


def test_dm_jobs_without_jwt_returns_401(dm_auth_client: TestClient) -> None:
    response = dm_auth_client.get("/jobs")
    assert response.status_code == 401


def test_dm_create_job_without_jwt_returns_401_no_side_effect(dm_auth_client: TestClient) -> None:
    response = dm_auth_client.post(
        "/jobs",
        json={"urls": ["https://example.com/unauth"]},
    )
    assert response.status_code == 401
    listed = dm_auth_client.get("/jobs")
    assert listed.status_code == 401


@pytest.mark.parametrize("authorization", ["Bearer not-a-jwt", "Bearer "])
def test_dm_jobs_with_invalid_jwt_returns_401(
    dm_auth_client: TestClient,
    authorization: str,
) -> None:
    response = dm_auth_client.get("/jobs", headers={"Authorization": authorization})
    assert response.status_code == 401


def test_dm_jobs_with_expired_jwt_returns_401(
    dm_auth_client: TestClient,
    supabase_auth_env: EllipticCurvePrivateKey,
) -> None:
    token = sign_test_jwt(supabase_auth_env, role="admin", exp_offset=-3600)
    response = dm_auth_client.get("/jobs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_internal_write_without_jwt_returns_401(write_auth_client: TestClient) -> None:
    response = write_auth_client.get("/internal/v1/documents")
    assert response.status_code == 401


def test_internal_write_with_invalid_jwt_returns_401(write_auth_client: TestClient) -> None:
    response = write_auth_client.get(
        "/internal/v1/documents",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


def test_chatrag_ask_without_auth_stays_anonymous(chat_anonymous_client: TestClient) -> None:
    response = chat_anonymous_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert response.status_code == 200
    assert response_json_object(response).get("answer")


def test_chatrag_documents_without_auth_stays_anonymous(chat_anonymous_client: TestClient) -> None:
    response = chat_anonymous_client.get("/api/v1/documents")
    assert response.status_code == 200

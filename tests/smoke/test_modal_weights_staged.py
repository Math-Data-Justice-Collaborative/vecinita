"""Live smoke: deployed Modal embed/LLM after D6/D7 volume staging (QA-003)."""

from __future__ import annotations

import os

import httpx
import pytest
from tests.helpers.json_response import json_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

EMBED_DIM = 384


def _embed_base() -> str | None:
    return os.environ.get("VECINITA_MODAL_EMBED_URL")


def _llm_base() -> str | None:
    return os.environ.get("VECINITA_MODAL_LLM_URL")


@pytest.fixture
def embed_base() -> str:
    url = _embed_base()
    if not url:
        pytest.skip("Set VECINITA_MODAL_EMBED_URL to run Modal embed smoke")
    return url.rstrip("/")


@pytest.fixture
def llm_base() -> str:
    url = _llm_base()
    if not url:
        pytest.skip("Set VECINITA_MODAL_LLM_URL to run Modal LLM smoke")
    return url.rstrip("/")


def test_modal_embed_health(embed_base: str) -> None:
    response = httpx.get(f"{embed_base}/health", timeout=60.0)
    assert response.status_code == 200
    assert json_str(response_json_object(response), "status") == "ok"


def test_modal_embed_dimension(embed_base: str) -> None:
    response = httpx.post(
        f"{embed_base}/embed",
        json={"text": "vecinita modal weights smoke"},
        timeout=120.0,
    )
    assert response.status_code == 200
    embedding = json_list(response_json_object(response), "embedding")
    assert len(embedding) == EMBED_DIM


def test_modal_llm_health(llm_base: str) -> None:
    response = httpx.get(f"{llm_base}/health", timeout=60.0)
    assert response.status_code == 200
    assert json_str(response_json_object(response), "status") == "ok"

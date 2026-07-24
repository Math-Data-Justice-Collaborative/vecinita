"""Tests for Modal URL validation before DO/Modal secret sync."""

from __future__ import annotations

import pytest
from deploy.modal_url_validate import validate_modal_service_url

pytestmark = pytest.mark.unit

GOOD_EMBED = "https://vecinita--vecinita-embedding-embedding-api.modal.run"
GOOD_LLM = "https://vecinita--vecinita-llm-fastapi-app.modal.run"
GOOD_LLM_PLAYGROUND = "https://vecinita--vecinita-llm-playground-fastapi-app.modal.run"


def test_validate_accepts_correct_embed_url() -> None:
    validate_modal_service_url("VECINITA_MODAL_EMBED_URL", GOOD_EMBED)


def test_validate_rejects_fontface_embed_prefix() -> None:
    with pytest.raises(ValueError, match="fontface--"):
        validate_modal_service_url(
            "VECINITA_MODAL_EMBED_URL",
            "https://fontface--vecinita-embedding-embedding-api.modal.run",
        )


def test_validate_rejects_health_suffix() -> None:
    with pytest.raises(ValueError, match="/health"):
        validate_modal_service_url("VECINITA_MODAL_EMBED_URL", f"{GOOD_EMBED}/health")


def test_validate_rejects_wrong_embedding_app_host() -> None:
    with pytest.raises(ValueError, match="vecinita-embedding"):
        validate_modal_service_url(
            "VECINITA_MODAL_EMBED_URL",
            "https://vecinita--other-app.modal.run",
        )


def test_validate_accepts_correct_llm_url() -> None:
    validate_modal_service_url("VECINITA_MODAL_LLM_URL", GOOD_LLM)


def test_validate_rejects_wrong_llm_app_host() -> None:
    with pytest.raises(ValueError, match="vecinita-llm"):
        validate_modal_service_url(
            "VECINITA_MODAL_LLM_URL",
            "https://vecinita--vecinita-embedding-embedding-api.modal.run",
        )


def test_validate_rejects_playground_url_as_prod_llm() -> None:
    """Prod VECINITA_MODAL_LLM_URL must not point at the playground app (TP-S010-27)."""
    with pytest.raises(ValueError, match="vecinita-llm"):
        validate_modal_service_url("VECINITA_MODAL_LLM_URL", GOOD_LLM_PLAYGROUND)


def test_validate_accepts_correct_llm_playground_url() -> None:
    validate_modal_service_url("VECINITA_MODAL_LLM_PLAYGROUND_URL", GOOD_LLM_PLAYGROUND)


def test_validate_rejects_prod_url_as_playground() -> None:
    with pytest.raises(ValueError, match="vecinita-llm-playground"):
        validate_modal_service_url("VECINITA_MODAL_LLM_PLAYGROUND_URL", GOOD_LLM)

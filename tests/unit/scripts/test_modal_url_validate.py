"""Tests for Modal URL validation before DO/Modal secret sync."""

from __future__ import annotations

import pytest
from deploy.modal_url_validate import (
    assert_mirrored_staging_embed_url,
    validate_modal_service_url,
)

pytestmark = pytest.mark.unit

GOOD_EMBED = "https://vecinita--vecinita-embedding-embedding-api.modal.run"
GOOD_LLM = "https://vecinita--vecinita-llm-fastapi-app.modal.run"
GOOD_LLM_PLAYGROUND = "https://vecinita--vecinita-llm-playground-fastapi-app.modal.run"
GOOD_RERANK = "https://vecinita--vecinita-rerank-rerank-api.modal.run"
STAGING_EMBED = "https://vecinita-staging--vecinita-embedding-embedding-api.modal.run"
STAGING_LLM = "https://vecinita-staging--vecinita-llm-fastapi-app.modal.run"
STAGING_LLM_PLAYGROUND = "https://vecinita-staging--vecinita-llm-playground-fastapi-app.modal.run"
STAGING_RERANK = "https://vecinita-staging--vecinita-rerank-rerank-api.modal.run"


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


def test_validate_accepts_correct_rerank_url() -> None:
    validate_modal_service_url("VECINITA_MODAL_RERANK_URL", GOOD_RERANK)


def test_validate_rejects_wrong_rerank_app_host() -> None:
    with pytest.raises(ValueError, match="vecinita-rerank"):
        validate_modal_service_url(
            "VECINITA_MODAL_RERANK_URL",
            "https://vecinita--vecinita-embedding-embedding-api.modal.run",
        )


def test_validate_accepts_staging_env_embed_url() -> None:
    """F83 / ADR-054 — Modal Environment staging web suffix → vecinita-staging--."""
    validate_modal_service_url("VECINITA_MODAL_EMBED_URL", STAGING_EMBED)


def test_validate_accepts_staging_env_llm_urls() -> None:
    validate_modal_service_url("VECINITA_MODAL_LLM_URL", STAGING_LLM)
    validate_modal_service_url("VECINITA_MODAL_LLM_PLAYGROUND_URL", STAGING_LLM_PLAYGROUND)


def test_validate_accepts_staging_env_rerank_url() -> None:
    validate_modal_service_url("VECINITA_MODAL_RERANK_URL", STAGING_RERANK)


def test_validate_rejects_staging_playground_as_prod_llm() -> None:
    with pytest.raises(ValueError, match="vecinita-llm"):
        validate_modal_service_url("VECINITA_MODAL_LLM_URL", STAGING_LLM_PLAYGROUND)


def test_mirrored_staging_embed_rejects_staging_environment_host() -> None:
    """EV-338 / BUG-2026-09-03 — mirrored prod vectors need vecinita-- embed on staging DO."""
    with pytest.raises(ValueError, match="vecinita--"):
        assert_mirrored_staging_embed_url(STAGING_EMBED, allow_staging_embed=False)


def test_mirrored_staging_embed_accepts_prod_host() -> None:

    assert_mirrored_staging_embed_url(GOOD_EMBED, allow_staging_embed=False)


def test_mirrored_staging_embed_waiver_allows_staging_host() -> None:

    assert_mirrored_staging_embed_url(STAGING_EMBED, allow_staging_embed=True)

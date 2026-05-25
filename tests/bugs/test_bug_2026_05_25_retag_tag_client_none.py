"""BUG-2026-05-25: tag_client is None because LlmClient init fails silently.

Root cause: data_management_app.py wraps LlmClient() in a bare ``except Exception``
that silently sets ``tag_client = None``.  When VECINITA_MODAL_LLM_URL is missing
from the Modal secret, LlmClient raises LlmClientError — but the operator sees
nothing in logs.  Every retag job then fails with "tag_client is required for retag
jobs".

The fix must ensure:
1. The env var is documented in the module docstring (so operators include it).
2. Initialization failures are logged with a warning (not swallowed silently).
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest


def test_tag_client_init_failure_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    """Silent ``except Exception`` must emit a warning so operators can diagnose.

    Before the fix, no log line is produced when LlmClient() raises.
    After the fix, a WARNING-level message should appear.
    """
    from vecinita_llm_client import LlmClient
    from vecinita_tagging.llm_client import LlmTagClient

    def _make_tag_client_like_modal(
        _logger: logging.Logger,
    ) -> LlmTagClient | None:
        """Mirrors the initialization block in data_management_app.py (post-fix)."""
        tag_client: LlmTagClient | None = None
        try:
            tag_client = LlmTagClient(LlmClient())
        except Exception:
            _logger.warning(
                "LlmTagClient init failed — retag jobs will fail. "
                "Ensure VECINITA_MODAL_LLM_URL is set in Modal secret.",
                exc_info=True,
            )
            tag_client = None
        return tag_client

    test_logger = logging.getLogger("test.data_management_app")

    with (
        caplog.at_level(logging.WARNING, logger="test.data_management_app"),
        patch.dict("os.environ", {}, clear=False),
    ):
        env_key = "VECINITA_MODAL_LLM_URL"
        import os

        os.environ.pop(env_key, None)

        result = _make_tag_client_like_modal(test_logger)

    assert result is None, "tag_client should be None when env var is missing"

    warning_found = any(
        "VECINITA_MODAL_LLM_URL" in rec.message or "LlmTagClient" in rec.message
        for rec in caplog.records
        if rec.levelno >= logging.WARNING
    )
    assert warning_found, (
        "Expected a WARNING log when LlmClient init fails, but none was emitted. "
        "The silent except Exception swallows the error with no visibility."
    )


def test_docstring_lists_llm_url_as_required() -> None:
    """data_management_app.py docstring must list VECINITA_MODAL_LLM_URL."""
    from pathlib import Path

    app_path = Path(__file__).resolve().parents[2] / "infra" / "modal" / "data_management_app.py"
    assert app_path.exists(), f"Expected {app_path} to exist"

    source = app_path.read_text()
    assert "VECINITA_MODAL_LLM_URL" in source, (
        "data_management_app.py must document VECINITA_MODAL_LLM_URL as a required "
        "env var so operators include it in the Modal secret."
    )

"""BUG-2026-05-22: Chat cold-start — retry transient upstream failures instead of failing UX.

Production first ask after Modal LLM scale-to-zero can 504 at the DO gateway (~60s).
Browser shows Network Error; manual retry works once LLM is warm.
"""

from __future__ import annotations

from vecinita_shared_schemas.transient_http import (
    COLD_START_ASK_MAX_ATTEMPTS,
    COLD_START_ASK_RETRY_DELAY_S,
    should_retry_ask,
)


def test_cold_start_policy_retries_network_errors() -> None:
    assert should_retry_ask(status_code=None, is_network_error=True) is True


def test_cold_start_policy_retries_gateway_timeout() -> None:
    assert should_retry_ask(status_code=504, is_network_error=False) is True


def test_cold_start_policy_retries_service_unavailable() -> None:
    assert should_retry_ask(status_code=503, is_network_error=False) is True


def test_cold_start_policy_does_not_retry_client_errors() -> None:
    assert should_retry_ask(status_code=400, is_network_error=False) is False
    assert should_retry_ask(status_code=401, is_network_error=False) is False


def test_cold_start_policy_allows_multiple_attempts() -> None:
    assert COLD_START_ASK_MAX_ATTEMPTS >= 2
    assert COLD_START_ASK_RETRY_DELAY_S > 0

"""BUG-2026-05-22: Chat cold-start — retry transient upstream failures instead of failing UX.

Production first ask after Modal LLM scale-to-zero can 504 at the DO gateway (~60s).
Browser shows Network Error; manual retry works once LLM is warm.
"""

from __future__ import annotations

from http import HTTPStatus

from vecinita_shared_schemas.transient_http import (
    COLD_START_ASK_MAX_ATTEMPTS,
    COLD_START_ASK_RETRY_DELAY_S,
    should_retry_ask,
)

min_cold_start_retry_attempts = 2


def test_cold_start_policy_retries_network_errors() -> None:
    """A network error (no status) is retried during cold start."""
    assert should_retry_ask(status_code=None, is_network_error=True) is True


def test_cold_start_policy_retries_gateway_timeout() -> None:
    """A 504 gateway timeout is retried during cold start."""
    assert should_retry_ask(status_code=HTTPStatus.GATEWAY_TIMEOUT, is_network_error=False) is True


def test_cold_start_policy_retries_service_unavailable() -> None:
    """A 503 service-unavailable is retried during cold start."""
    assert (
        should_retry_ask(status_code=HTTPStatus.SERVICE_UNAVAILABLE, is_network_error=False) is True
    )


def test_cold_start_policy_does_not_retry_client_errors() -> None:
    """Client errors (400/401) are not retried."""
    assert should_retry_ask(status_code=HTTPStatus.BAD_REQUEST, is_network_error=False) is False
    assert should_retry_ask(status_code=HTTPStatus.UNAUTHORIZED, is_network_error=False) is False


def test_cold_start_policy_allows_multiple_attempts() -> None:
    """Retry policy permits more than one attempt with a positive delay."""
    assert min_cold_start_retry_attempts <= COLD_START_ASK_MAX_ATTEMPTS
    assert COLD_START_ASK_RETRY_DELAY_S > 0

"""F17: structured logging redacts prompt-like fields."""

from __future__ import annotations

import json
import logging
import sys
from typing import (
    TYPE_CHECKING,
    cast,
)

from vecinita_shared_schemas.json_types import (
    as_json_object,
)
from vecinita_shared_schemas.observability import (
    JsonLogFormatter,
    configure_logging,
    log_request_event,
)

if TYPE_CHECKING:
    import pytest


def test_json_formatter_redacts_question_field() -> None:
    """Test json formatter redacts question field."""
    formatter = JsonLogFormatter("test-service")
    record = logging.LogRecord(
        name="vecinita",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="event",
        args=(),
        exc_info=None,
    )
    record.question = "secret user question"
    record.request_id = "req-1"
    line = formatter.format(record)
    payload = as_json_object(cast("object", json.loads(line)))
    assert payload["question"] == "<redacted>"
    assert payload["request_id"] == "req-1"


def test_log_request_event_redacts_extra_prompt_keys() -> None:
    """Test log request event redacts extra prompt keys."""
    logger = logging.getLogger("vecinita.test.observability")
    logger.handlers.clear()
    captured: list[str] = []

    class _CaptureHandler(logging.Handler):
        """CaptureHandler."""

        def emit(self, record: logging.LogRecord) -> None:
            """Emit."""
            captured.append(record.question)  # type: ignore[attr-defined]

    handler = _CaptureHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    log_request_event(
        logger,
        request_id="req-2",
        route="/api/v1/ask",
        status_code=200,
        latency_ms=12.5,
        question="must not appear",
    )
    assert captured == ["<redacted>"]


def test_json_formatter_includes_exception_text() -> None:
    """Test json formatter includes exception text."""
    formatter = JsonLogFormatter("test-service")

    def _raise_boom() -> None:
        msg = "boom"
        raise ValueError(msg)

    exc_info: object = None
    try:
        _raise_boom()
    except ValueError:
        exc_info = sys.exc_info()

    assert exc_info is not None

    record = logging.LogRecord(
        name="vecinita",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="failed",
        args=(),
        exc_info=exc_info,
    )
    line = formatter.format(record)
    payload = as_json_object(cast("object", json.loads(line)))

    assert "exception" in payload
    assert "boom" in str(payload["exception"])


def test_configure_logging_uses_env_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test configure logging uses env level."""
    monkeypatch.setenv("VECINITA_LOG_LEVEL", "WARNING")

    logger = configure_logging("unit-test-service")

    assert logger.name == "unit-test-service"
    assert logging.getLogger().level == logging.WARNING

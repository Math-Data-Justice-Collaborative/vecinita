"""F17: structured logging redacts prompt-like fields."""

from __future__ import annotations

import json
import logging

from vecinita_shared_schemas.observability import JsonLogFormatter, log_request_event


def test_json_formatter_redacts_question_field() -> None:
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
    payload = json.loads(line)
    assert payload["question"] == "<redacted>"
    assert payload["request_id"] == "req-1"


def test_log_request_event_redacts_extra_prompt_keys() -> None:
    logger = logging.getLogger("vecinita.test.observability")
    logger.handlers.clear()
    captured: list[str] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
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

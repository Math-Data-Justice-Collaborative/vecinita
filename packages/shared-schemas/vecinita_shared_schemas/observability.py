"""Structured logging baseline (F17) — no raw prompts in log records."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Final, cast

from vecinita_shared_schemas.json_types import JsonObject

LOG_LEVEL_ENV: Final[str] = "VECINITA_LOG_LEVEL"
REQUEST_ID_KEY: Final[str] = "request_id"
SERVICE_NAME_KEY: Final[str] = "service"

_REDACTED_KEYS: Final[frozenset[str]] = frozenset(
    {
        "question",
        "prompt",
        "answer",
        "text",
        "raw_prompt",
        "messages",
    }
)


class JsonLogFormatter(logging.Formatter):
    """Emit one JSON object per log line without prompt-like fields."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: JsonObject = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            SERVICE_NAME_KEY: self._service_name,
            "message": record.getMessage(),
        }
        for key in record.__dict__:
            value = cast(object, record.__dict__[key])
            if key.startswith("_") or key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            }:
                continue
            if key in _REDACTED_KEYS:
                payload[key] = "<redacted>"
            else:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(service_name: str) -> logging.Logger:
    """Configure root logger from VECINITA_LOG_LEVEL (default INFO)."""
    level_name = os.environ.get(LOG_LEVEL_ENV, "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonLogFormatter(service_name))
    root.addHandler(handler)
    root.setLevel(level)

    return logging.getLogger(service_name)


def log_request_event(
    logger: logging.Logger,
    *,
    request_id: str,
    route: str,
    status_code: int,
    latency_ms: float,
    **extra: str | int | float | bool | None,
) -> None:
    """Log an HTTP request summary without prompt content."""
    safe_extra = {k: "<redacted>" if k in _REDACTED_KEYS else v for k, v in extra.items()}
    logger.info(
        "request_completed",
        extra={
            REQUEST_ID_KEY: request_id,
            "route": route,
            "status_code": status_code,
            "latency_ms": latency_ms,
            **safe_extra,
        },
    )

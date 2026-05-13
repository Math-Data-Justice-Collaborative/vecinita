"""Structured logging configuration."""

import logging
import sys
from typing import Any

try:
    import structlog as _structlog
except ImportError:  # pragma: no cover - fallback for minimal test environments
    _structlog = None


class _StdlibLoggerProxy:
    """Small adapter that accepts structlog-style keyword context."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._context: dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "_StdlibLoggerProxy":
        proxy = _StdlibLoggerProxy(self._logger)
        proxy._context = {**self._context, **kwargs}
        return proxy

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, extra=self._build_extra(kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, extra=self._build_extra(kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, extra=self._build_extra(kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(message, extra=self._build_extra(kwargs))

    def exception(self, message: str, **kwargs: Any) -> None:
        self._logger.exception(message, extra=self._build_extra(kwargs))

    def _build_extra(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        return {"context": {**self._context, **kwargs}}


def configure_logging() -> None:
    """Configure structured logging with structlog."""
    from vecinita_scraper.core.config import get_config

    config = get_config()

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.log_level),
    )

    # Configure structlog
    if _structlog is not None:
        _structlog.configure(
            processors=[
                _structlog.stdlib.filter_by_level,
                _structlog.stdlib.add_logger_name,
                _structlog.stdlib.add_log_level,
                _structlog.stdlib.PositionalArgumentsFormatter(),
                _structlog.processors.TimeStamper(fmt="iso"),
                _structlog.processors.StackInfoRenderer(),
                _structlog.processors.format_exc_info,
                _structlog.processors.UnicodeDecoder(),
                _structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=_structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> Any:
    """Get a logger instance."""
    if _structlog is not None:
        return _structlog.get_logger(name)
    return _StdlibLoggerProxy(logging.getLogger(name))


class LoggerAdapter:
    """Adapter for logging with context."""

    def __init__(self, name: str) -> None:
        """Initialize logger adapter."""
        self.logger = get_logger(name)

    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """Bind context to logger."""
        bind = getattr(self.logger, "bind", None)
        if callable(bind):
            self.logger = bind(**kwargs)
        return self

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs if kwargs else None)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs if kwargs else None)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs if kwargs else None)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs if kwargs else None)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception message."""
        self.logger.exception(message, extra=kwargs if kwargs else None)

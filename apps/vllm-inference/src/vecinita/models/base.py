"""Abstract base class for all model backends."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from ..api.schemas import Message


class BaseModelBackend(ABC):
    """Minimal interface every model backend must implement."""

    @abstractmethod
    def chat(self, messages: list[Message], **kwargs: Any) -> str:
        """Return a complete response string for the given message history."""

    @abstractmethod
    def stream(self, messages: list[Message], **kwargs: Any) -> Iterator[str]:
        """Yield response tokens one at a time for the given message history."""

    @abstractmethod
    def is_healthy(self) -> bool:
        """Return True when the backend is ready to serve requests."""

"""Ollama model backend.

Communicates with a locally running Ollama server via the official
Python client.  The server is expected to already be running (it is
started by the Modal container entry-point in app.py).

The default deployment model tag is **Gemma 3** (``gemma3``); see
``vecinita.config.Settings.default_model`` and ``SUPPORTED_MODELS``.
"""

import logging
import subprocess
import time
from collections.abc import Iterator
from typing import Any

import ollama

from ..api.schemas import Message
from .base import BaseModelBackend

logger = logging.getLogger(__name__)

TRANSIENT_CONNECTION_MARKERS = (
    "connection refused",
    "temporarily unavailable",
    "timeout",
    "timed out",
    "try again",
)


def classify_connection_error(error: Exception) -> str:
    """Classify Ollama startup/runtime failures for retry policy decisions."""
    text = str(error).lower()
    if any(marker in text for marker in TRANSIENT_CONNECTION_MARKERS):
        return "transient_failure"
    return "permanent_failure"


class OllamaBackend(BaseModelBackend):
    """Talk to an Ollama server running on localhost."""

    def __init__(
        self,
        model_name: str,
        host: str = "http://localhost:11434",
        models_path: str = "/models",
    ) -> None:
        self.model_name = model_name
        self.host = host
        self.models_path = models_path
        self._client = ollama.Client(host=host)

    # ------------------------------------------------------------------
    # Server lifecycle helpers (called from app.py / tests)
    # ------------------------------------------------------------------

    @classmethod
    def start_server(cls, models_path: str = "/models") -> subprocess.Popen:
        """Launch the Ollama daemon and wait until it is ready.

        Returns the :class:`subprocess.Popen` handle so the caller can
        terminate the process cleanly.
        """
        import os

        env = os.environ.copy()
        env["OLLAMA_MODELS"] = models_path
        proc = subprocess.Popen(
            ["ollama", "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Poll until the server responds (up to 30 s).
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                ollama.Client().list()
                logger.info("Ollama server is ready.")
                return proc
            except Exception:
                time.sleep(0.5)
        # If we reach here, the server did not become ready; make sure we
        # clean up the background process before raising.
        try:
            proc.terminate()
        except Exception:
            # Best-effort cleanup; log and continue to raise the timeout.
            logger.warning(
                "Failed to terminate Ollama server process on timeout.",
                exc_info=True,
            )
        else:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    logger.warning(
                        "Failed to kill Ollama server process after timeout.",
                        exc_info=True,
                    )
        raise RuntimeError("Ollama server did not start within 30 seconds.")

    # ------------------------------------------------------------------
    # BaseModelBackend implementation
    # ------------------------------------------------------------------

    def chat(self, messages: list[Message], **kwargs: Any) -> str:
        """Return a complete response string."""
        response = self._client.chat(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            options=self._build_options(kwargs),
        )
        return response.message.content

    def stream(self, messages: list[Message], **kwargs: Any) -> Iterator[str]:
        """Yield response tokens one at a time."""
        for chunk in self._client.chat(
            model=self.model_name,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True,
            options=self._build_options(kwargs),
        ):
            yield chunk.message.content

    def is_healthy(self) -> bool:
        try:
            self._client.list()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_options(self, kwargs: dict) -> dict:
        options: dict[str, Any] = {}
        if "temperature" in kwargs and kwargs["temperature"] is not None:
            options["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs and kwargs["max_tokens"] is not None:
            options["num_predict"] = kwargs["max_tokens"]
        return options

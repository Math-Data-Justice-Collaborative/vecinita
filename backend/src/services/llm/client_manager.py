"""Central local-only LLM client manager.

This project intentionally routes all chat-model usage through a single local
Ollama-compatible endpoint. External hosted providers are not supported.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import urlparse

import httpx
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

logger = logging.getLogger(__name__)

ChatOllama = None
_CHATOLLAMA_IMPORT_ERROR: Exception | None = None


def _get_chatollama_class():
    global ChatOllama, _CHATOLLAMA_IMPORT_ERROR
    if ChatOllama is not None:
        return ChatOllama
    if _CHATOLLAMA_IMPORT_ERROR is not None:
        return None
    try:
        from langchain_ollama import ChatOllama as _ChatOllama  # type: ignore[import-not-found]

        ChatOllama = _ChatOllama
        return ChatOllama
    except Exception as exc:
        _CHATOLLAMA_IMPORT_ERROR = exc
        logger.warning("langchain_ollama unavailable (%s).", exc)
        return None


class Selection(TypedDict):
    provider: str
    model: str | None
    locked: bool


class _ModalNativeChatClient:
    """Minimal chat client for Modal-native /chat endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        headers: dict[str, str],
        temperature: float = 0,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.headers = headers
        self.temperature = temperature
        self.timeout = timeout

    def bind_tools(self, _tools: list[Any]):
        return self

    def invoke(self, messages: list[BaseMessage]):
        payload_messages: list[dict[str, str]] = []
        for msg in messages:
            role = "user"
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            payload_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": self.temperature,
        }

        target_url = f"{self.base_url}/chat"
        logger.info(
            "llm_modal_invoke_start target=%s model=%s timeout_s=%.1f message_count=%s has_auth_header=%s",
            target_url,
            self.model,
            float(self.timeout),
            len(payload_messages),
            "Authorization" in self.headers,
        )

        with httpx.Client(timeout=self.timeout) as client:
            try:
                response = client.post(
                    target_url,
                    json=payload,
                    headers={"Content-Type": "application/json", **self.headers},
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                logger.exception(
                    "llm_modal_invoke_error target=%s model=%s error=%s",
                    target_url,
                    self.model,
                    exc,
                )
                raise

        message = data.get("message") if isinstance(data, dict) else None
        content = ""
        if isinstance(message, dict):
            content = str(message.get("content") or "")
        if not content:
            content = str(data)
        return AIMessage(content=content)


class LocalLLMClientManager:
    """Manage local-only LLM selection, validation, and client construction."""

    def __init__(
        self,
        *,
        base_url: str | None,
        default_model: str,
        api_key: str | None = None,
        selection_file_path: str | None = None,
        locked: bool = False,
        use_native_api: bool = True,
        enforce_proxy: bool = False,
        **legacy_kwargs: Any,
    ):
        # Ignore retired compatibility kwargs passed by older call sites.
        _ = legacy_kwargs
        self.base_url = str(base_url or "").strip().rstrip("/")
        self.default_model = default_model
        self.api_key = api_key
        self.selection_file_path = selection_file_path
        self.use_native_api = use_native_api
        self.enforce_proxy = False
        self.current_selection: Selection = {
            "provider": "ollama",
            "model": default_model,
            "locked": bool(locked),
        }
        self._load_selection_from_file()
        self.validate_selection()

    @staticmethod
    def normalize_provider(provider_name: str | None) -> str:
        normalized = str(provider_name or "").lower().strip()
        if normalized in {"", "ollama", "llama", "local"}:
            return "ollama"
        return normalized

    def headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _via_proxy(self) -> bool:
        return False

    def _is_local_proxy(self) -> bool:
        return False

    def current_model(self) -> str:
        return self.current_selection.get("model") or self.default_model

    def get_selection(self) -> Selection:
        return self.current_selection

    def _load_selection_from_file(self) -> None:
        if not self.selection_file_path:
            return
        try:
            path = Path(self.selection_file_path)
            if not path.exists():
                return
            data = json.loads(path.read_text())
            provider = self.normalize_provider(data.get("provider"))
            if provider == "ollama":
                self.current_selection["provider"] = "ollama"
            self.current_selection["model"] = data.get("model") or self.current_selection["model"]
            self.current_selection["locked"] = bool(
                data.get("locked", self.current_selection["locked"])
            )
        except Exception as exc:
            logger.warning("Failed to load local LLM selection file: %s", exc)

    def save_selection(
        self,
        provider: str,
        model: str | None,
        locked: bool | None = None,
    ) -> None:
        normalized_provider = self.normalize_provider(provider)
        if normalized_provider != "ollama":
            raise ValueError("Only the local Ollama provider is supported")
        payload = {
            "provider": "ollama",
            "model": model or self.default_model,
            "locked": self.current_selection["locked"] if locked is None else bool(locked),
        }
        self.current_selection["provider"] = payload["provider"]
        self.current_selection["model"] = payload["model"]
        self.current_selection["locked"] = payload["locked"]
        if self.selection_file_path:
            path = Path(self.selection_file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2))

    def validate_selection(self) -> None:
        selected = self.normalize_provider(self.current_selection.get("provider"))
        reset_model = False
        if selected != "ollama":
            if self.current_selection.get("locked"):
                raise RuntimeError(
                    f"Model selection is locked to unsupported provider '{selected}'. Only local Ollama is supported."
                )
            logger.warning(
                "Ignoring unsupported provider '%s' and switching to local Ollama.",
                selected,
            )
            self.current_selection["provider"] = "ollama"
            reset_model = True
        if reset_model or not self.current_selection.get("model"):
            self.current_selection["model"] = self.default_model

    def validate_runtime(self) -> None:
        self.validate_selection()
        if not self.base_url:
            raise RuntimeError(
                "No local LLM endpoint configured. Set OLLAMA_BASE_URL or MODAL_OLLAMA_ENDPOINT."
            )
        if self.uses_modal_native_chat_api():
            return
        if _get_chatollama_class() is None:
            raise RuntimeError(
                "Local LLM requested but langchain_ollama import failed. "
                f"Original error: {_CHATOLLAMA_IMPORT_ERROR}"
            )

    def resolve_request(
        self,
        provider: str | None,
        model: str | None,
    ) -> tuple[str, str]:
        requested = self.normalize_provider(provider or self.current_selection.get("provider"))
        if requested != "ollama":
            logger.info(
                "Ignoring requested provider '%s'; local Ollama is the only supported provider.",
                requested,
            )
            return "ollama", self.current_model()
        return "ollama", model or self.current_model()

    def uses_modal_native_chat_api(self) -> bool:
        if not (self.use_native_api and self.base_url):
            return False
        lowered = self.base_url.lower()
        # Native Modal endpoints are hosted under *.modal.run.
        if "modal.run" in lowered:
            return True
        # Local dev may still route model traffic through localhost:10000/model.
        parsed = urlparse(self.base_url)
        host = (parsed.hostname or "").lower()
        port = parsed.port
        path = (parsed.path or "").lower()
        return bool(
            host in {"localhost", "127.0.0.1"} and port == 10000 and path.startswith("/model")
        )

    def is_reachable(self, timeout: float = 1.5) -> bool:
        if not self.base_url:
            return False
        endpoints = ["/health"]
        if not self.uses_modal_native_chat_api():
            endpoints.insert(0, "/api/tags")
        for endpoint in endpoints:
            try:
                with urllib.request.urlopen(
                    f"{self.base_url}{endpoint}", timeout=timeout
                ) as response:
                    status = getattr(response, "status", 200)
                    if int(status) < 500:
                        return True
            except Exception:
                continue
        return False

    def config_payload(self) -> dict[str, Any]:
        model = self.current_model()
        return {
            "providers": [
                {
                    "key": "ollama",
                    "label": "Modal (Ollama-compatible)",
                    "default": True,
                }
            ],
            "models": {"ollama": [model]},
            "defaultProvider": "ollama",
            "defaultModel": model,
        }

    def build_client(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0,
        tools: list[Any] | None = None,
        structured_output_schema: Any | None = None,
    ):
        _provider, resolved_model = self.resolve_request(provider, model)
        logger.info(
            "llm_client_build provider=%s model=%s base_url=%s uses_native_api=%s",
            _provider,
            resolved_model,
            self.base_url,
            self.uses_modal_native_chat_api(),
        )
        if self.uses_modal_native_chat_api():
            if structured_output_schema is not None:
                raise RuntimeError(
                    "Structured-output tagging is unavailable with the Modal native chat endpoint."
                )
            client = _ModalNativeChatClient(
                base_url=self.base_url,
                model=resolved_model,
                headers=self.headers(),
                temperature=temperature,
            )
            return client.bind_tools(tools or []) if tools else client

        chat_ollama_class = _get_chatollama_class()
        if chat_ollama_class is None:
            raise RuntimeError(
                "Local LLM requested but langchain_ollama import failed. "
                f"Original error: {_CHATOLLAMA_IMPORT_ERROR}"
            )
        client = chat_ollama_class(
            temperature=temperature,
            model=resolved_model,
            base_url=self.base_url,
            client_kwargs={"headers": self.headers()},
        )
        if structured_output_schema is not None:
            return client.with_structured_output(structured_output_schema)
        if tools is not None:
            return client.bind_tools(tools)
        return client

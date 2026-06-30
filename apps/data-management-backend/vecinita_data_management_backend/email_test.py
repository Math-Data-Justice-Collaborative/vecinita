"""Resend REST client for the admin deliverability test-send (EV-006 F35, ADR-031 §TP-S005-22).

Sends a branded test email through the Resend REST API (``POST https://api.resend.com/emails``)
to prove the verified sending domain + DNS (SPF/DKIM/DMARC) and the ``RESEND_API_KEY`` work
end-to-end, without creating a spurious Supabase user. The key is server-side only (Modal DM
secret bundle) and never reaches the browser.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import Final, cast

import httpx
from vecinita_shared_schemas.json_types import as_json_object

_ENV_KEY: Final[str] = "RESEND_API_KEY"
_ENV_SENDER: Final[str] = "RESEND_SENDER_EMAIL"
_RESEND_URL: Final[str] = "https://api.resend.com/emails"
_SUBJECT: Final[str] = "Vecinita Admin · deliverability test"
_HTML_BODY: Final[str] = (
    "<p>This is a Vecinita Admin deliverability test email.</p>"
    "<p>Si recibes este mensaje, la entrega de correo de Vecinita funciona.</p>"
)


class ResendError(RuntimeError):
    """Raised when a Resend REST request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 0,
        provider_name: str = "",
        provider_message: str = "",
    ) -> None:
        """Capture the failing HTTP status code (0 for transport/config errors)."""
        super().__init__(message)
        self.status_code = status_code
        self.provider_name = provider_name
        self.provider_message = provider_message


class ResendClient:
    """Send transactional email through the Resend REST API."""

    def __init__(
        self,
        *,
        api_key: str,
        sender: str,
        http_client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Configure the client with a Resend API key and verified sender address."""
        self._api_key = api_key
        self._sender = sender
        self._owns = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    @classmethod
    def from_env(cls) -> ResendClient | None:
        """Build a client from ``RESEND_API_KEY``/``RESEND_SENDER_EMAIL`` or ``None`` if unset."""
        api_key = os.environ.get(_ENV_KEY)
        sender = os.environ.get(_ENV_SENDER)
        if not api_key or not sender:
            return None
        return cls(api_key=api_key, sender=sender)

    def close(self) -> None:
        """Close the owned HTTP client when this wrapper created it."""
        if self._owns:
            self._client.close()

    def send_test_email(self, to: str) -> str:
        """Send the test email to ``to`` and return the Resend message id."""
        response = self._client.post(
            _RESEND_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "from": self._sender,
                "to": [to],
                "subject": _SUBJECT,
                "html": _HTML_BODY,
            },
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            provider_name = ""
            provider_message = ""
            try:
                body = as_json_object(cast("object", response.json()))
                name = body.get("name")
                message = body.get("message")
                if isinstance(name, str):
                    provider_name = name
                if isinstance(message, str):
                    provider_message = message
            except (ValueError, TypeError):
                pass
            msg = f"Resend send failed: {response.status_code} {response.text}"
            raise ResendError(
                msg,
                status_code=response.status_code,
                provider_name=provider_name,
                provider_message=provider_message,
            ) from None
        message_id = as_json_object(cast("object", response.json())).get("id")
        return message_id if isinstance(message_id, str) else ""


def resend_error_http_detail(err: ResendError) -> tuple[int, dict[str, str]] | None:
    """Map known operator-fixable Resend failures to structured HTTP error bodies."""
    if err.status_code == HTTPStatus.FORBIDDEN and "not verified" in err.provider_message.lower():
        return (
            HTTPStatus.SERVICE_UNAVAILABLE,
            {
                "code": "domain_unverified",
                "message": err.provider_message or "Sending domain is not verified in Resend",
            },
        )
    return None

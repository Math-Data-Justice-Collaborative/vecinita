"""Optional operator notify after anonymous feedback insert (F68 / #214 / ADR-046 §6).

Webhook and/or Resend email; fail-open — never raises to the write caller.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Final

import httpx

logger = logging.getLogger(__name__)

_ENV_WEBHOOK: Final[str] = "VECINITA_FEEDBACK_NOTIFY_WEBHOOK"
_ENV_EMAIL: Final[str] = "VECINITA_FEEDBACK_NOTIFY_EMAIL"
_ENV_RESEND_KEY: Final[str] = "RESEND_API_KEY"
_ENV_RESEND_SENDER: Final[str] = "RESEND_SENDER_EMAIL"
_RESEND_URL: Final[str] = "https://api.resend.com/emails"
_DEFAULT_TIMEOUT: Final[float] = 5.0


@dataclass(frozen=True, slots=True)
class FeedbackNotifyPayload:
    """Operator-safe notify fields (no invented visitor identity)."""

    id: str
    category: str
    locale: str | None
    created_at: str
    message: str

    def as_dict(self) -> dict[str, str | None]:
        """JSON-serializable payload for webhook bodies."""
        return {
            "id": self.id,
            "category": self.category,
            "locale": self.locale,
            "created_at": self.created_at,
            "message": self.message,
        }


def notify_feedback_operators(
    payload: FeedbackNotifyPayload,
    *,
    http_client: httpx.Client | None = None,
) -> None:
    """Send webhook and/or email when configured; swallow all notify errors."""
    owns = http_client is None
    client = http_client or httpx.Client(timeout=_DEFAULT_TIMEOUT)
    try:
        _notify_webhook(client, payload)
        _notify_email(client, payload)
    finally:
        if owns:
            client.close()


def _notify_webhook(client: httpx.Client, payload: FeedbackNotifyPayload) -> None:
    url = (os.environ.get(_ENV_WEBHOOK) or "").strip()
    if not url:
        return
    try:
        response = client.post(url, json=payload.as_dict())
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            logger.warning(
                "feedback webhook notify failed: status=%s body=%s",
                response.status_code,
                response.text[:200],
            )
    except httpx.HTTPError:
        logger.exception("feedback webhook notify transport error")


def _notify_email(client: httpx.Client, payload: FeedbackNotifyPayload) -> None:
    to_addr = (os.environ.get(_ENV_EMAIL) or "").strip()
    api_key = (os.environ.get(_ENV_RESEND_KEY) or "").strip()
    sender = (os.environ.get(_ENV_RESEND_SENDER) or "").strip()
    if not to_addr or not api_key or not sender:
        return
    locale = payload.locale or "—"
    subject = f"Vecinita feedback · {payload.category}"
    text_body = (
        f"New anonymous feedback received.\n\n"
        f"id: {payload.id}\n"
        f"category: {payload.category}\n"
        f"locale: {locale}\n"
        f"created_at: {payload.created_at}\n\n"
        f"message:\n{payload.message}\n"
    )
    html_body = (
        "<p>New anonymous feedback received.</p>"
        f"<p><strong>id</strong>: {payload.id}<br/>"
        f"<strong>category</strong>: {payload.category}<br/>"
        f"<strong>locale</strong>: {locale}<br/>"
        f"<strong>created_at</strong>: {payload.created_at}</p>"
        f"<pre>{payload.message}</pre>"
    )
    try:
        response = client.post(
            _RESEND_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": sender,
                "to": [to_addr],
                "subject": subject,
                "text": text_body,
                "html": html_body,
            },
        )
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            logger.warning(
                "feedback email notify failed: status=%s body=%s",
                response.status_code,
                response.text[:200],
            )
    except httpx.HTTPError:
        logger.exception("feedback email notify transport error")

"""Stable enums for crawl outcomes (spec 011 / data-model)."""

from __future__ import annotations

from enum import StrEnum


class ResponseKind(StrEnum):
    """Document family for the job target response."""

    HTML = "html"
    PDF = "pdf"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


class FailureCategory(StrEnum):
    """Normalized failure labels for operators and downstream jobs."""

    TRANSPORT_ERROR = "transport_error"
    HTTP_ERROR = "http_error"
    POLICY_BLOCKED = "policy_blocked"
    NON_EXTRACTABLE_HTML = "non_extractable_html"
    LIKELY_BOT_OR_CLIENT_LIMITATION = "likely_bot_or_client_limitation"
    CONTENT_NOT_READY = "content_not_ready"
    PDF_CORRUPT_OR_UNREADABLE = "pdf_corrupt_or_unreadable"
    PDF_PASSWORD_PROTECTED = "pdf_password_protected"
    PDF_EMPTY_NON_EXTRACTIVE = "pdf_empty_non_extractive"
    TEXT_ENCODING_FAILURE = "text_encoding_failure"
    FORMAT_MISMATCH = "format_mismatch"
    TEXT_EMPTY = "text_empty"

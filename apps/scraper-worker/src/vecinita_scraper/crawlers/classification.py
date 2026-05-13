"""Heuristics for substantive content and HTML failure classification."""

from __future__ import annotations

import re
from typing import Any

from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind

# Spec rubric: "order of hundreds of characters" for substantive body text.
SUBSTANTIVE_MIN_CHARS = 200


def substantive_char_count(
    markdown: str,
    extracted_content: str | None,
    cleaned_html: str,
) -> int:
    """Approximate extractable text length from crawl outputs."""
    for candidate in (markdown, (extracted_content or "").strip()):
        if candidate and len(candidate.strip()) >= SUBSTANTIVE_MIN_CHARS:
            return len(candidate.strip())
    stripped_html = _strip_tags(cleaned_html)
    if stripped_html and len(stripped_html) >= SUBSTANTIVE_MIN_CHARS:
        return len(stripped_html)
    if markdown and markdown.strip():
        return len(markdown.strip())
    if extracted_content and str(extracted_content).strip():
        return len(str(extracted_content).strip())
    return len(stripped_html)


def _strip_tags(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"(?s)<script[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"(?s)<style[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def map_crawl4ai_error_message(message: str | None) -> FailureCategory | None:
    """Map raw Crawl4AI / browser diagnostics to stable FailureCategory."""
    if not message:
        return None
    m = message.lower()
    if "connection" in m and ("refused" in m or "reset" in m or "timed out" in m or "timeout" in m):
        return FailureCategory.TRANSPORT_ERROR
    if "http" in m and ("403" in m or "401" in m or "429" in m):
        return FailureCategory.HTTP_ERROR
    if "robots" in m or "robotstxt" in m or "disallowed" in m:
        return FailureCategory.POLICY_BLOCKED
    if "anti-bot" in m or "bot protection" in m or "blocked by anti-bot" in m:
        return FailureCategory.LIKELY_BOT_OR_CLIENT_LIMITATION
    if "minimal_text" in m or "no_content_elements" in m or "script_heavy" in m:
        return FailureCategory.NON_EXTRACTABLE_HTML
    if "content not ready" in m or "wait" in m and "timeout" in m:
        return FailureCategory.CONTENT_NOT_READY
    return FailureCategory.NON_EXTRACTABLE_HTML


def operator_summary_for_category(category: FailureCategory, legacy: str | None) -> str:
    """Short plain-language summary for operators."""
    tips: dict[FailureCategory, str] = {
        FailureCategory.TRANSPORT_ERROR: "Network or TLS error reaching the server.",
        FailureCategory.HTTP_ERROR: "The server returned an HTTP error for this URL.",
        FailureCategory.POLICY_BLOCKED: (
            "Automated fetch appears blocked by robots.txt or site policy."
        ),
        FailureCategory.NON_EXTRACTABLE_HTML: "Page loaded but yielded almost no readable text "
        "(often client-rendered shell or interstitial).",
        FailureCategory.LIKELY_BOT_OR_CLIENT_LIMITATION: "The site may be serving a minimal page "
        "to automated clients.",
        FailureCategory.CONTENT_NOT_READY: "Timed out waiting for main content to appear.",
        FailureCategory.PDF_CORRUPT_OR_UNREADABLE: "PDF bytes could not be read.",
        FailureCategory.PDF_PASSWORD_PROTECTED: "PDF is password-protected.",
        FailureCategory.PDF_EMPTY_NON_EXTRACTIVE: (
            "PDF has no extractable text (may be image-only)."
        ),
        FailureCategory.TEXT_ENCODING_FAILURE: "Plain text could not be decoded reliably.",
        FailureCategory.FORMAT_MISMATCH: "Declared content type did not match the response body.",
        FailureCategory.TEXT_EMPTY: "Plain text response was empty.",
    }
    base = tips.get(category, "Crawl did not produce usable extractable content.")
    if legacy and len(legacy) < 400:
        return f"{base} ({legacy})"
    return base


def finalize_html_crawled_page(page: Any) -> None:
    """Set response_kind and, on failure or thin success, failure_category + operator_summary."""
    if page.response_kind is None:
        page.response_kind = ResponseKind.HTML

    chars = substantive_char_count(
        page.markdown,
        page.extracted_content,
        page.cleaned_html,
    )

    if page.success and chars >= SUBSTANTIVE_MIN_CHARS:
        page.failure_category = None
        page.operator_summary = None
        return

    if page.success and chars < SUBSTANTIVE_MIN_CHARS:
        page.success = False
        mapped = map_crawl4ai_error_message(page.error_message)
        page.failure_category = mapped or FailureCategory.NON_EXTRACTABLE_HTML
        page.operator_summary = operator_summary_for_category(
            page.failure_category,
            page.error_message,
        )
        page.error_message = page.error_message or (
            "Page loaded but produced insufficient extractable text."
        )
        return

    mapped = map_crawl4ai_error_message(page.error_message)
    page.failure_category = mapped or FailureCategory.NON_EXTRACTABLE_HTML
    page.operator_summary = operator_summary_for_category(
        page.failure_category,
        page.error_message,
    )

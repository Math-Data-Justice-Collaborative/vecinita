"""Validate Modal service base URLs before syncing to DigitalOcean or Modal secrets."""

from __future__ import annotations

import re

# Prod workspace ``vecinita`` (Environment main) or staging Environment web suffix
# ``staging`` → host source ``vecinita-staging--`` (F83 / ADR-054).
_WS = r"(?:vecinita-staging|vecinita)"
_EMBED_HOST_PATTERN = re.compile(rf"{_WS}--vecinita-embedding")
_LLM_HOST_PATTERN = re.compile(rf"{_WS}--vecinita-llm(?!-playground)")
_LLM_PLAYGROUND_HOST_PATTERN = re.compile(rf"{_WS}--vecinita-llm-playground")
_RERANK_HOST_PATTERN = re.compile(rf"{_WS}--vecinita-rerank")

_MODAL_URL_KEYS = frozenset(
    {
        "VECINITA_MODAL_EMBED_URL",
        "VECINITA_MODAL_LLM_URL",
        "VECINITA_MODAL_LLM_PLAYGROUND_URL",
        "VECINITA_MODAL_RERANK_URL",
    }
)


def validate_modal_service_url(key: str, url: str) -> None:
    """Raise ValueError when a Modal base URL is misconfigured."""
    trimmed = url.strip()
    if key not in _MODAL_URL_KEYS:
        return
    if not trimmed.startswith("https://"):
        msg = f"{key} must be an https base URL (got {trimmed!r})"
        raise ValueError(msg)
    if "fontface--" in trimmed:
        msg = (
            f"{key} must use the vecinita-- (prod) or vecinita-staging-- (Modal Environment "
            + f"staging) URL source prefix, not fontface-- (got {trimmed!r})"
        )
        raise ValueError(msg)
    normalized = trimmed.rstrip("/")
    if normalized.endswith("/health"):
        msg = f"{key} must be the Modal ASGI base URL without a /health suffix (got {trimmed!r})"
        raise ValueError(msg)
    if key == "VECINITA_MODAL_EMBED_URL" and not _EMBED_HOST_PATTERN.search(trimmed):
        msg = (
            f"{key} should target the vecinita-embedding app "
            + "(expected host containing vecinita--vecinita-embedding or "
            + f"vecinita-staging--vecinita-embedding; got {trimmed!r})"
        )
        raise ValueError(msg)
    if key == "VECINITA_MODAL_LLM_URL" and not _LLM_HOST_PATTERN.search(trimmed):
        msg = (
            f"{key} should target the prod/staging vecinita-llm app "
            + "(expected host containing vecinita[--staging]--vecinita-llm without "
            + f"-playground; got {trimmed!r})"
        )
        raise ValueError(msg)
    if key == "VECINITA_MODAL_LLM_PLAYGROUND_URL" and not _LLM_PLAYGROUND_HOST_PATTERN.search(
        trimmed
    ):
        msg = (
            f"{key} should target the vecinita-llm-playground app "
            + "(expected host containing vecinita[--staging]--vecinita-llm-playground; "
            + f"got {trimmed!r})"
        )
        raise ValueError(msg)
    if key == "VECINITA_MODAL_RERANK_URL" and not _RERANK_HOST_PATTERN.search(trimmed):
        msg = (
            f"{key} should target the vecinita-rerank app "
            + "(expected host containing vecinita[--staging]--vecinita-rerank; "
            + f"got {trimmed!r})"
        )
        raise ValueError(msg)


def main(argv: list[str] | None = None) -> int:
    """CLI: validate_modal_service_url KEY URL (exit 0/1)."""
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("Usage: modal_url_validate.py KEY URL", file=sys.stderr)
        return 2
    key, url = args
    try:
        validate_modal_service_url(key, url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

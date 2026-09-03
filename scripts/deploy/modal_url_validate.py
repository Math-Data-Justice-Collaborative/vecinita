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


def assert_mirrored_staging_embed_url(url: str, *, allow_staging_embed: bool = False) -> None:
    """Require prod ``vecinita--`` embed when staging DO serves a mirrored prod corpus.

    Staging Modal Environment embed (``vecinita-staging--``) may pin a different model
    (e.g. BGE) than prod e5. After EV-338 prod→staging mirror, ChatRAG query vectors must
    come from the same embed app that produced the stored embeddings — see
    ``docs/staging-runbook.md`` §mirror and BUG-2026-09-03-staging-embed-url-mirror-regress.

    Set ``allow_staging_embed=True`` (or env ``VECINITA_ALLOW_STAGING_EMBED=1``) only when
    staging intentionally uses a staging-rebuilt corpus under the staging embed pin.
    """
    validate_modal_service_url("VECINITA_MODAL_EMBED_URL", url)
    trimmed = url.strip()
    if allow_staging_embed:
        return
    if "vecinita-staging--" in trimmed:
        msg = (
            "VECINITA_MODAL_EMBED_URL for mirrored staging corpus must use the prod "
            "vecinita--vecinita-embedding host (not vecinita-staging--). "
            "See docs/staging-runbook.md §Prod → staging corpus mirror. "
            "Waiver: VECINITA_ALLOW_STAGING_EMBED=1 when staging re-embeds with the "
            f"staging Modal Environment pin (got {trimmed!r})"
        )
        raise ValueError(msg)
    if "vecinita--vecinita-embedding" not in trimmed:
        msg = (
            "VECINITA_MODAL_EMBED_URL for mirrored staging corpus must contain "
            f"vecinita--vecinita-embedding (got {trimmed!r})"
        )
        raise ValueError(msg)


def main(argv: list[str] | None = None) -> int:
    """CLI: validate_modal_service_url KEY URL, or mirror-embed check.

    Usage:
      modal_url_validate.py KEY URL
      modal_url_validate.py --mirrored-staging-embed URL
    """
    import os
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == "--mirrored-staging-embed":
        allow = os.environ.get("VECINITA_ALLOW_STAGING_EMBED", "").strip() in {
            "1",
            "true",
            "TRUE",
            "yes",
            "YES",
        }
        try:
            assert_mirrored_staging_embed_url(args[1], allow_staging_embed=allow)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0
    if len(args) != 2:
        print(
            "Usage: modal_url_validate.py KEY URL | --mirrored-staging-embed URL",
            file=sys.stderr,
        )
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

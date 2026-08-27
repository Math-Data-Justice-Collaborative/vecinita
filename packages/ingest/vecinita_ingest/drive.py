"""Google Drive / Docs / Sheets URL handling for public ingest (F7 / #235)."""

from __future__ import annotations

import re
from typing import Final
from urllib.parse import urlparse

_DRIVE_HOSTS: Final[frozenset[str]] = frozenset(
    {
        "drive.google.com",
        "docs.google.com",
    }
)

_FILE_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"/file/d/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
_DOC_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"/document/d/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
_SHEET_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"/spreadsheets/d/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)
_PRESENTATION_ID_RE: Final[re.Pattern[str]] = re.compile(
    r"/presentation/d/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)

# Auth / loading shells are short chrome, not real document bodies.
_MAX_SHELL_CHARS: Final[int] = 400


class DriveFetchError(ValueError):
    """Raised when a Drive/Docs URL cannot yield extractable public content."""

    def __init__(self, message: str, *, error_code: str) -> None:
        """Attach a stable operator-facing ``error_code`` for job surfaces."""
        super().__init__(message)
        self.error_code = error_code


def is_google_drive_url(url: str) -> bool:
    """Return True when ``url`` targets Google Drive or Docs hosts."""
    host = urlparse(url).hostname
    if host is None:
        return False
    return host.lower() in _DRIVE_HOSTS


def is_drive_auth_shell(text: str) -> bool:
    """Return True when extracted text looks like a Drive auth/loading shell."""
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    if not normalized:
        return True
    if len(normalized) > _MAX_SHELL_CHARS:
        return False
    has_loading = "loading" in normalized
    has_sign_in = any(marker in normalized for marker in ("sign in", "signin", "log in", "login"))
    if has_loading and has_sign_in:
        return True
    # Very short chrome that is only a known marker phrase.
    compact = normalized.replace("…", "").replace("...", "")
    return compact in {"loading", "sign in", "signin", "log in", "login"}


def rewrite_drive_fetch_url(url: str) -> str:
    """Rewrite a share/view URL to a public export or download endpoint when known.

    Unsupported shapes (folders, unknown paths) raise ``DriveFetchError``.
    """
    parsed = urlparse(url)
    path = parsed.path or ""

    doc_match = _DOC_ID_RE.search(path)
    if doc_match is not None:
        doc_id = doc_match.group(1)
        return f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    sheet_match = _SHEET_ID_RE.search(path)
    if sheet_match is not None:
        sheet_id = sheet_match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    presentation_match = _PRESENTATION_ID_RE.search(path)
    if presentation_match is not None:
        presentation_id = presentation_match.group(1)
        return f"https://docs.google.com/presentation/d/{presentation_id}/export/txt"

    file_match = _FILE_ID_RE.search(path)
    if file_match is not None:
        file_id = file_match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    # Already an export/download URL — leave as-is.
    if "/export" in path or "export=download" in (parsed.query or ""):
        return url

    msg = (
        "Unsupported Google Drive URL shape — use a public file/Docs/Sheets "
        + "share link, upload the file, or paste an export URL"
    )
    raise DriveFetchError(msg, error_code="drive_unsupported")

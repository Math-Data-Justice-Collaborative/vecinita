"""Compatibility wrapper for the Modal entrypoint."""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from vecinita.app import app  # noqa: E402

__all__ = ["app"]

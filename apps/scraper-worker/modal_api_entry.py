"""Deploy HTTP API app: ``cd modal-apps/scraper && modal deploy modal_api_entry.py``."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from vecinita_scraper.api.app import app  # noqa: E402

__all__ = ["app"]

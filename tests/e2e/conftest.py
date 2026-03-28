"""Pytest configuration for E2E tests with Playwright."""

import sys
from pathlib import Path

# Ensure src/utils can be imported
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

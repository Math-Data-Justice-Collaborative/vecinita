#!/usr/bin/env python3
"""Deprecated wrapper for scraper pipeline.

Use scripts/run_scraper.sh directly. This file is kept for backwards compatibility.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    runner = script_dir / "run_scraper.sh"

    if not runner.exists():
        print(f"Runner script not found: {runner}", file=sys.stderr)
        return 1

    print("[DEPRECATED] scripts/data_scrape_load.py now delegates to scripts/run_scraper.sh")
    result = subprocess.run([str(runner), *sys.argv[1:]], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

"""
Configuration management for the VECINA scraper.
Loads and manages site categorization and scraper settings.
"""

import os
import logging
from typing import Dict, List
from pathlib import Path

log = logging.getLogger(__name__)


def _find_repo_root() -> Path:
    """
    Find the top-level repository root by searching upward for marker files.

    This function is intended to locate the project repository directory that
    contains the ``backend/`` folder, not the ``backend`` directory itself.
    A typical layout is::

        <repo_root>/
            backend/
                src/
                    scraper/
                        config.py
            pyproject.toml
            docker-compose.yml
            .git/

    The search walks upward from this file and stops at the first directory
    that contains any of the following marker entries, which are expected to
    live at the repository root:
      - ``.git`` directory
      - ``docker-compose.yml`` file
      - ``pyproject.toml`` file

    If no markers are found, the function falls back to a hardcoded relative
    path based on this file's location.

    Returns:
        Path to the repository root directory (parent of ``backend/``).
    """
    current = Path(__file__).resolve()
    marker_files = ['.git', 'docker-compose.yml', 'pyproject.toml']

    # Search upward from this file's location
    while current != current.parent:  # Stop at filesystem root
        for marker in marker_files:
            if (current / marker).exists():
                log.debug(f"Found repo root marker '{marker}' at {current}")
                return current
        current = current.parent

    # Fallback: use relative path (backend/src/scraper/config.py -> parent of backend)
    fallback_root = Path(__file__).resolve().parents[3]
    log.debug(
        f"No repo root marker found; using fallback path: {fallback_root}")
    return fallback_root


class ScraperConfig:
    """Manages all scraper configuration."""

    # Resolve config directory:
    # 1. Use SCRAPER_CONFIG_DIR if set.
    # 2. Otherwise, use relative path from current file location
    _env_config_dir = os.getenv("SCRAPER_CONFIG_DIR")
    if _env_config_dir:
        _config_dir_path = Path(_env_config_dir).expanduser().resolve()
    else:
        # From backend/src/scraper/config.py, go up 3 levels to project root, then data/config
        _config_dir_path = Path(
            __file__).resolve().parents[3] / "data" / "config"

    if not _config_dir_path.exists():
        log.warning(
            "ScraperConfig config directory does not exist at %s. "
            "Configuration lists may be empty.",
            _config_dir_path,
        )

    CONFIG_DIR = _config_dir_path

    RECURSIVE_SITES_FILE = str(CONFIG_DIR / "recursive_sites.txt")
    PLAYWRIGHT_SITES_FILE = str(CONFIG_DIR / "playwright_sites.txt")
    SKIP_SITES_FILE = str(CONFIG_DIR / "skip_sites.txt")
    DATA_DIR = "data/"

    # Scraper settings
    RATE_LIMIT_DELAY = 2  # seconds
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    def __init__(self):
        """Initialize configuration by loading all site lists."""
        self.sites_to_crawl: Dict[str, Dict[str, int]] = {}
        self.sites_needing_playwright: List[str] = []
        self.sites_to_skip: List[str] = []
        self.load_all_configs()

    def load_all_configs(self) -> None:
        """Load all configuration files."""
        self.sites_to_crawl = self._load_recursive_config(
            self.RECURSIVE_SITES_FILE)
        self.sites_needing_playwright = self._load_config_list(
            self.PLAYWRIGHT_SITES_FILE)
        self.sites_to_skip = self._load_config_list(self.SKIP_SITES_FILE)

        log.info(
            f"Loaded {len(self.sites_to_crawl)} recursive sites, "
            f"{len(self.sites_needing_playwright)} playwright sites, "
            f"{len(self.sites_to_skip)} skip sites."
        )

    @staticmethod
    def _load_config_list(file_path: str) -> List[str]:
        """Load a simple list of domains/keywords from a .txt file."""
        if not os.path.exists(file_path):
            log.warning(
                f"Config file not found: {file_path}. List will be empty.")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            log.error(f"Failed to read config file {file_path}: {e}")
            return []

    @staticmethod
    def _load_recursive_config(file_path: str) -> Dict[str, Dict[str, int]]:
        """Load recursive site config (e.g., "https://example.com/ 2")."""
        config = {}
        if not os.path.exists(file_path):
            log.warning(
                f"Config file not found: {file_path}. Recursive crawl list will be empty.")
            return config

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            url_prefix = parts[0]
                            try:
                                depth = int(parts[1])
                                config[url_prefix] = {"max_depth": depth}
                            except ValueError:
                                log.error(
                                    f"Invalid depth '{parts[1]}' for site '{url_prefix}'. Skipping.")
                        elif len(parts) == 1:
                            config[parts[0]] = {"max_depth": 1}
            return config
        except Exception as e:
            log.error(f"Failed to read recursive config file {file_path}: {e}")
            return {}

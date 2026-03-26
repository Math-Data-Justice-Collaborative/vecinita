"""Markdown FAQ Loader for Vecinita.

Loads FAQs from markdown files and provides in-memory caching with auto-reload.
"""

import logging
import re
import string
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache settings
_faq_cache: dict[str, dict[str, str]] = {}
_cache_timestamps: dict[str, datetime] = {}
_cache_ttl = timedelta(minutes=5)  # Reload FAQs every 5 minutes

# FAQ directory path (relative from module, customizable via env var)
FAQ_DIR_ENV = "FAQ_DIR"
_FAQ_DIR_OVERRIDE = None  # Will be set by environment variable if provided


def _get_faq_dir() -> Path:
    """Get FAQ directory, checking for env override first."""
    # Check if env override is set
    import os

    if FAQ_DIR_ENV in os.environ:
        return Path(os.environ[FAQ_DIR_ENV])

    # Canonical path first (backend/src/services/agent/data/faqs)
    project_root = Path(__file__).parent.parent.parent
    canonical = project_root / "src" / "services" / "agent" / "data" / "faqs"
    if canonical.exists():
        return canonical

    # Legacy fallback (backend/services/agent/data/faqs)
    legacy = project_root / "services" / "agent" / "data" / "faqs"
    return legacy


def load_faqs_from_markdown(lang: str = "en") -> dict[str, str]:
    """Load FAQs from markdown file for the specified language.

    FAQs are cached in memory and reloaded every 5 minutes or when
    the file timestamp changes.

    Format:
        ## Question text here?

        Answer paragraph here.

        ## Another question?

        Another answer.

    Args:
        lang: Language code ('en', 'es', etc.)

    Returns:
        Dictionary mapping normalized questions to answers.
        Keys are lowercase, punctuation-removed for matching.
    """
    # Check if cache is still valid
    if lang in _faq_cache and lang in _cache_timestamps:
        age = datetime.now() - _cache_timestamps[lang]
        if age < _cache_ttl:
            logger.debug(f"Using cached FAQs for {lang} (age: {age.seconds}s)")
            return _faq_cache[lang]

    # Load from file
    faq_dir = _get_faq_dir()
    faq_file = faq_dir / f"{lang}.md"

    if not faq_file.exists():
        logger.warning(f"FAQ file not found: {faq_file}")
        # Return empty dict or fall back to English
        if lang != "en":
            logger.info(f"Falling back to English FAQs for {lang}")
            return load_faqs_from_markdown("en")
        return {}

    try:
        logger.info(f"Loading FAQs from {faq_file}")
        with open(faq_file, encoding="utf-8") as f:
            content = f.read()

        faqs = _parse_markdown_faqs(content)

        # Update cache
        _faq_cache[lang] = faqs
        _cache_timestamps[lang] = datetime.now()

        logger.info(f"Loaded {len(faqs)} FAQs for {lang}")
        return faqs

    except Exception as e:
        logger.error(f"Error loading FAQs from {faq_file}: {e}")
        # Return cached version if available, else empty dict
        return _faq_cache.get(lang, {})


def _parse_markdown_faqs(content: str) -> dict[str, str]:
    """Parse markdown content into FAQ dictionary.

    Extracts questions (## headings) and their corresponding answers
    (paragraphs following the heading).

    Args:
        content: Markdown file content

    Returns:
        Dictionary mapping normalized questions to answers
    """
    faqs = {}

    # Split by h2 headings (##)
    # Pattern: ## Question\n\nAnswer text
    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)

    # First section is usually just the title/header, skip it
    for section in sections[1:]:
        if not section.strip():
            continue

        # Split into question and answer at first blank line or double newline
        parts = re.split(r"\n\s*\n", section, maxsplit=1)

        if len(parts) < 2:
            # No answer found, skip
            continue

        question = parts[0].strip()
        answer = parts[1].strip()

        if not question or not answer:
            continue

        # Normalize question for matching
        normalized_question = _normalize_question(question)

        # Store with normalized key
        faqs[normalized_question] = answer

        logger.debug(f"Parsed FAQ: '{question[:50]}...' -> {len(answer)} chars")

    return faqs


def _normalize_question(question: str) -> str:
    """Normalize question for matching.

    Converts to lowercase and removes punctuation for more flexible matching.

    Args:
        question: Original question text

    Returns:
        Normalized question string
    """
    # Convert to lowercase
    normalized = question.lower().strip()

    # Remove punctuation (including Spanish punctuation)
    punctuation = string.punctuation + "¿¡"
    translation_table = str.maketrans("", "", punctuation)
    normalized = normalized.translate(translation_table)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def reload_faqs(lang: str | None = None) -> None:
    """Force reload FAQs from disk.

    Useful for manual refresh or testing.

    Args:
        lang: Language to reload, or None to reload all cached languages
    """
    if lang:
        if lang in _cache_timestamps:
            del _cache_timestamps[lang]
            if lang in _faq_cache:
                del _faq_cache[lang]
        load_faqs_from_markdown(lang)
    else:
        # Reload all cached languages
        languages = list(_cache_timestamps.keys())
        _cache_timestamps.clear()
        _faq_cache.clear()
        for lang in languages:
            load_faqs_from_markdown(lang)


def get_faq_stats() -> dict[str, int]:
    """Get statistics about loaded FAQs.

    Returns:
        Dictionary with counts per language
    """
    return {lang: len(faqs) for lang, faqs in _faq_cache.items()}


# Preload English FAQs on module import
try:
    load_faqs_from_markdown("en")
except Exception as e:
    logger.warning(f"Failed to preload English FAQs: {e}")

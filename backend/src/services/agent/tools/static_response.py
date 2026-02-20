"""Static response tool for Vecinita agent.

This tool provides predefined answers to frequently asked questions (FAQs).
FAQs are loaded from markdown files in backend/src/services/agent/data/faqs/.
"""

import logging
import string
from langchain_core.tools import tool
from src.utils import load_faqs_from_markdown, get_faq_stats

logger = logging.getLogger(__name__)

# Minimum query length for partial matching
MIN_QUERY_LENGTH = 10

DEFAULT_FAQ_DATABASE = {
    "en": {
        "what is vecinita": "Vecinita is a community-based Q&A assistant designed to help people find information about local services, community programs, and resources.",
        "how does this work": "Vecinita works by searching through a database of community documents and resources to provide accurate answers.",
        "who created vecinita": "Vecinita is an open-source project created to support community information access.",
    },
    "es": {
        "qué es vecinita": "Vecinita es un asistente comunitario de preguntas y respuestas diseñado para ayudar a las personas a encontrar información sobre servicios locales.",
        "cómo funciona esto": "Vecinita funciona buscando en una base de datos de documentos y recursos comunitarios.",
        "quién creó vecinita": "Vecinita es un proyecto de código abierto creado para apoyar el acceso a la información comunitaria.",
    },
}


def _bootstrap_faq_database() -> dict:
    """Load markdown FAQs into an in-memory, mutable database."""
    en_faqs = load_faqs_from_markdown("en")
    es_faqs = load_faqs_from_markdown("es")

    database = {
        "en": en_faqs if en_faqs else dict(DEFAULT_FAQ_DATABASE["en"]),
        "es": es_faqs if es_faqs else dict(DEFAULT_FAQ_DATABASE["es"]),
    }
    return database


# In-memory FAQ store kept for backward compatibility with tests and legacy code.
FAQ_DATABASE = _bootstrap_faq_database()


@tool
def static_response_tool(query: str, language: str = "en") -> str | None:
    """Check if the query matches a frequently asked question (FAQ).

    Returns the answer string if an FAQ match is found, None otherwise.
    The agent will try other tools (db_search, web_search) when None is returned.

    Args:
        query: The user's question.
        language: The language code ('en' or 'es').

    Returns:
        The FAQ answer string if found, None if no match.
    """
    try:
        logger.info(
            f"Static Response: Checking FAQ for: '{query}' ({language})")

        # Normalize query
        normalized_query = query.lower().strip()
        punctuation_table = str.maketrans('', '', string.punctuation + "¿¡")
        normalized_query_clean = normalized_query.translate(punctuation_table)

        # Read from mutable in-memory store first (test compatibility), then fallback.
        normalized_language = (language or "en").lower()

        faqs = FAQ_DATABASE.get(normalized_language)
        if faqs is None:
            faqs = FAQ_DATABASE.get("en", {})

        # 1. Exact match
        if normalized_query in faqs:
            return faqs[normalized_query]

        # 2. Cleaned match
        for faq_key, faq_answer in faqs.items():
            if faq_key.translate(punctuation_table) == normalized_query_clean:
                return faq_answer

        # 3. Partial match (only for longer queries)
        if len(normalized_query_clean) >= MIN_QUERY_LENGTH:
            for faq_key, faq_answer in faqs.items():
                faq_key_clean = faq_key.translate(punctuation_table)
                if faq_key_clean in normalized_query_clean or normalized_query_clean in faq_key_clean:
                    return faq_answer

        # 4. No match found - Return None so agent can try other tools
        logger.info(f"No FAQ match found for: '{query}'")
        return None

    except Exception as e:
        logger.error(f"Static Response Error: {e}")
        return None


def add_faq(question: str, answer: str, language: str = "en") -> None:
    """Add or update an FAQ entry in-memory.

    This preserves historical behavior expected by tests. Markdown remains the
    source of truth for persisted FAQs; this function does not write to disk.
    """
    normalized_language = (language or "en").lower()
    normalized_question = (question or "").strip().lower()

    if not normalized_question:
        return

    if normalized_language not in FAQ_DATABASE:
        FAQ_DATABASE[normalized_language] = {}

    FAQ_DATABASE[normalized_language][normalized_question] = answer


def list_faqs(language: str = "en") -> dict:
    """List all available FAQs for a language.

    Args:
        language: The language code ('en' or 'es')

    Returns:
        Dictionary of questions and answers loaded from markdown
    """
    normalized_language = (language or "en").lower()
    if normalized_language in FAQ_DATABASE:
        return FAQ_DATABASE[normalized_language]
    return {}


def get_faq_statistics() -> dict:
    """Get statistics about loaded FAQs.

    Returns:
        Dictionary with FAQ counts per language
    """
    stats = get_faq_stats()
    stats["in_memory"] = {lang: len(faqs) for lang, faqs in FAQ_DATABASE.items()}
    return stats

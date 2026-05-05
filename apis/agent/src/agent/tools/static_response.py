"""Static response tool for Vecinita agent.

This tool provides predefined answers to frequently asked questions (FAQs).
"""

import logging
import string

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Minimum query length for partial matching
MIN_QUERY_LENGTH = 10

# FAQ Database
FAQ_DATABASE = {
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


@tool
def static_response_tool(query: str, language: str = "en") -> str | None:
    """Check if the query matches a frequently asked question (FAQ).

    Returns the answer if found, or a 'not found' message.

    Args:
        query: The user's question.
        language: The language code ('en' or 'es').
    """
    try:
        logger.info(f"Static Response: Checking FAQ for: '{query}' ({language})")

        # Normalize query
        normalized_query = query.lower().strip()
        punctuation_table = str.maketrans("", "", string.punctuation + "¿¡")
        normalized_query_clean = normalized_query.translate(punctuation_table)

        # Get FAQs for language
        faqs = FAQ_DATABASE.get(language, FAQ_DATABASE.get("en", {}))

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
                if (
                    faq_key_clean in normalized_query_clean
                    or normalized_query_clean in faq_key_clean
                ):
                    return faq_answer

        # 4. No match found - Return None so other tools can be attempted
        return None

    except Exception as e:
        logger.error(f"Static Response Error: {e}")
        return None


def add_faq(question: str, answer: str, language: str = "en") -> None:
    """Add or update an FAQ entry in-memory.

    This helper is primarily used by tests and local development.
    """
    normalized_language = (language or "en").lower()
    normalized_question = (question or "").strip().lower()
    if not normalized_question:
        return

    if normalized_language not in FAQ_DATABASE:
        FAQ_DATABASE[normalized_language] = {}

    FAQ_DATABASE[normalized_language][normalized_question] = answer


def list_faqs(language: str = "en") -> dict:
    """Return FAQs for a language.

    Returns an empty dict for unknown languages.
    """
    normalized_language = (language or "en").lower()
    return FAQ_DATABASE.get(normalized_language, {})


def create_static_response_tool():
    """Create an instance of the static_response tool.

    The static response tool checks if a query matches a frequently asked question (FAQ)
    and returns the predefined answer if found.

    Returns:
        A configured tool function that can be used with LangGraph
    """
    return static_response_tool

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

        # Get FAQs for language from markdown files
        faqs = load_faqs_from_markdown(language)

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
    """DEPRECATED: Add a new FAQ to the markdown file.
    
    This function is no longer supported. FAQs are managed via markdown files.
    
    To add FAQs:
    1. Edit backend/src/services/agent/data/faqs/en.md (or es.md)
    2. Use markdown format:
       ## Question here?
       
       Answer paragraph here.
    3. The tool auto-reloads FAQs every 5 minutes
    
    Args:
        question: The FAQ question (deprecated - not used)
        answer: The answer to the question (deprecated - not used)
        language: The language code ('en' or 'es')
        
    Raises:
        RuntimeError: Always - use markdown file editing instead
    """
    logger.error(
        f"add_faq() deprecated. Edit backend/src/services/agent/data/faqs/{language}.md instead."
    )
    raise RuntimeError(
        f"FAQ management is file-based. Edit backend/src/services/agent/data/faqs/{language}.md directly. "
        "Changes are auto-loaded every 5 minutes."
    )


def list_faqs(language: str = "en") -> dict:
    """List all available FAQs for a language.

    Args:
        language: The language code ('en' or 'es')

    Returns:
        Dictionary of questions and answers loaded from markdown
    """
    return load_faqs_from_markdown(language)


def get_faq_statistics() -> dict:
    """Get statistics about loaded FAQs.

    Returns:
        Dictionary with FAQ counts per language
    """
    return get_faq_stats()

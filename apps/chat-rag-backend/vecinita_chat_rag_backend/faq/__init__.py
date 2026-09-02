"""FAQ fast-path package (F85)."""

from vecinita_chat_rag_backend.faq.match import (
    FaqEntry,
    FaqStore,
    default_faq_store_path,
    load_faq_store,
    match_faq,
    normalize_faq_question,
)

__all__ = [
    "FaqEntry",
    "FaqStore",
    "default_faq_store_path",
    "load_faq_store",
    "match_faq",
    "normalize_faq_question",
]

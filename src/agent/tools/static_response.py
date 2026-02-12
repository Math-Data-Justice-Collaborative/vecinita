import logging

logger = logging.getLogger(__name__)

def list_faqs(language: str = "en"):
    """Returns a dictionary of common FAQs for the given language."""
    faqs = {
        "en": {
            "what is vecinita": "Vecinita is a community assistant providing social services information.",
            "who are you": "I am Vecinita, your community AI assistant."
        },
        "es": {
            "que es vecinita": "Vecinita es un asistente comunitario que brinda información sobre servicios sociales.",
            "quien eres": "Soy Vecinita, tu asistente comunitario de inteligencia artificial."
        }
    }
    return faqs.get(language, faqs["en"])

def static_response_tool(query: str, language: str = "en") -> str:
    """Tool version of the FAQ matcher for the LangGraph agent."""
    q = query.lower().strip()
    faqs = list_faqs(language)
    return faqs.get(q, "")

"""RAG constants (config-spec, ADR-008)."""

from __future__ import annotations

EMBEDDING_DIMENSION = 384
DEFAULT_TOP_K = 8
MIN_TOP_K = 1
MAX_TOP_K = 50

NO_CONTEXT_MESSAGE_EN = "I don't have enough community corpus context to answer that question."
NO_CONTEXT_MESSAGE_ES = (
    "No tengo suficiente contexto del corpus comunitario para responder esa pregunta."
)
HEDGE_DISCLAIMER_EN = (
    "This answer may not be fully supported by the sources we found. "
    + "Please verify important details with the linked resources."
)
HEDGE_DISCLAIMER_ES = (
    "Esta respuesta puede no estar completamente respaldada por las fuentes encontradas. "
    + "Verifique los detalles importantes con los recursos enlazados."
)

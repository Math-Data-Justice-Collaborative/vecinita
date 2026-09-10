"""RAG constants (config-spec, ADR-008)."""

from __future__ import annotations

EMBEDDING_DIMENSION = 384
DEFAULT_TOP_K = 8
MIN_TOP_K = 1
MAX_TOP_K = 50

NO_CONTEXT_MESSAGE_EN = (
    "No matching sources were found in the community corpus for that question. "
    + "Try rephrasing, or browse topics for related resources."
)
NO_CONTEXT_MESSAGE_ES = (
    "No se encontraron fuentes coincidentes en el corpus comunitario para esa pregunta. "
    + "Intente reformularla o explore los temas para recursos relacionados."
)
HEDGE_DISCLAIMER_EN = (
    "This answer may not be fully supported by the sources we found. "
    + "Please verify important details with the linked resources."
)
HEDGE_DISCLAIMER_ES = (
    "Esta respuesta puede no estar completamente respaldada por las fuentes encontradas. "
    + "Verifique los detalles importantes con los recursos enlazados."
)

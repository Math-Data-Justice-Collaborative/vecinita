"""Rewrite question tool for Vecinita agent.

Uses the configured LLM provider to rewrite a question for better retrieval.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool


def create_rewrite_question_tool(get_llm_without_tools: Callable[[str | None, str | None], Any]):
    """Create rewrite tool bound to the current LLM factory."""

    @tool
    def rewrite_question_tool(
        question: str,
        provider: str | None = None,
        model: str | None = None,
    ) -> str:
        """Rewrite a question to improve retrieval relevance while preserving intent.

        Args:
            question: Original user question.
            provider: Optional provider override.
            model: Optional model override.

        Returns:
            Rewritten question text.
        """
        rewrite_prompt = (
            "Look at the input question and reason about its semantic intent.\n"
            "Rewrite it as a clearer, retrieval-friendly question while preserving meaning.\n"
            f"Original question: {question}"
        )

        try:
            llm = get_llm_without_tools(provider, model)
            rewritten = llm.invoke([HumanMessage(content=rewrite_prompt)])
            rewritten_text = rewritten.content if hasattr(rewritten, "content") else str(rewritten)
            cleaned = str(rewritten_text or "").strip()
            return cleaned or question
        except Exception:
            return question

    return rewrite_question_tool

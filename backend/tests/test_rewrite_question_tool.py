"""Unit tests for rewrite question tool."""

from unittest.mock import Mock

from src.agent.tools.rewrite_question import create_rewrite_question_tool


def test_rewrite_question_tool_uses_llm_output():
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(
        content="What housing assistance programs are available in Providence?"
    )

    tool = create_rewrite_question_tool(lambda _provider, _model: mock_llm)
    rewritten = tool.invoke({"question": "help me with housing", "provider": "deepseek"})

    assert isinstance(rewritten, str)
    assert "housing assistance" in rewritten.lower()


def test_rewrite_question_tool_falls_back_to_original_on_error():
    def _raise(_provider, _model):
        raise RuntimeError("llm down")

    tool = create_rewrite_question_tool(_raise)
    original = "need help"
    rewritten = tool.invoke({"question": original})

    assert rewritten == original

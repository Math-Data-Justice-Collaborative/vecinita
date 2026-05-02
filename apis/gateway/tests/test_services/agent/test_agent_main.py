"""Unit tests for the legacy services agent import path."""

from importlib import reload
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def _apply_env(env_vars, monkeypatch) -> None:
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)


def _import_server(env_vars, monkeypatch):
    _apply_env(env_vars, monkeypatch)
    with (
        patch("src.services.agent.server.ChatGroq") as mock_groq,
        patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings,
    ):
        mock_groq.return_value = MagicMock()
        mock_embeddings.return_value = MagicMock()
        from src.services.agent import server

        return reload(server)


def test_app_creation(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert server.app is not None


def test_location_context_configured(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert server.LOCATION_CONTEXT is not None
    assert "organization" in server.LOCATION_CONTEXT
    assert "location" in server.LOCATION_CONTEXT


def test_agent_thinking_messages_exist(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert "en" in server.AGENT_THINKING_MESSAGES
    assert "es" in server.AGENT_THINKING_MESSAGES


def test_get_agent_thinking_message_english(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert server.get_agent_thinking_message("plan", "en") == "Let me think about your question..."


def test_get_agent_thinking_message_spanish(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert (
        server.get_agent_thinking_message("db_search", "es")
        == "Revisando nuestros recursos locales..."
    )


def test_get_agent_thinking_message_fallback(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert server.get_agent_thinking_message("unknown_tool", "unknown_lang") == "Thinking..."


def test_get_agent_thinking_message_spanish_unknown_tool(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert server.get_agent_thinking_message("unknown_tool", "es") == "Pensando..."


def test_agent_state_creation(env_vars, monkeypatch):
    _import_server(env_vars, monkeypatch)
    from langchain_core.messages import HumanMessage

    from src.services.agent.server import AgentState

    state = AgentState(
        messages=[HumanMessage(content="test")],
        question="test question",
        language="en",
        provider="llama",
        model=None,
        plan=None,
    )
    assert state["question"] == "test question"
    assert state["language"] == "en"


def test_embedding_service_fallback_chain(env_vars, monkeypatch):
    _apply_env(env_vars, monkeypatch)
    with (
        patch("src.services.agent.server.ChatGroq") as mock_groq,
        patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings,
        patch(
            "src.services.agent.server.create_embedding_client",
            side_effect=Exception("Service unavailable"),
        ),
    ):
        mock_groq.return_value = MagicMock()
        mock_embeddings.return_value = MagicMock()
        from src.services.agent import server

        server = reload(server)
        assert server.embedding_model is not None


def test_llm_initialization_with_groq(env_vars, monkeypatch):
    env_vars["GROQ_API_KEY"] = "test-groq-key"
    server = _import_server(env_vars, monkeypatch)
    assert callable(server._get_llm_with_tools)


def test_tools_initialized(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert isinstance(server.tools, list)
    assert len(server.tools) > 0
    assert "static_response_tool" in [tool.name for tool in server.tools]


def test_none_tools_filtered(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    assert all(tool is not None for tool in server.tools)


def test_get_llm_with_tools_llama_ollama(env_vars, monkeypatch):
    env_vars["OLLAMA_BASE_URL"] = "http://localhost:11434"
    env_vars["OLLAMA_MODEL"] = "llama3.2"
    server = _import_server(env_vars, monkeypatch)
    server.ollama_base_url = "http://localhost:11434"
    server.CURRENT_SELECTION["provider"] = "ollama"

    mock_chatollama_cls = MagicMock()
    mock_chatollama_instance = MagicMock()
    mock_chatollama_instance.bind_tools.return_value = MagicMock()
    mock_chatollama_cls.return_value = mock_chatollama_instance

    with patch("src.services.agent.server._get_chatollama_class", return_value=mock_chatollama_cls):
        llm_with_tools = server._get_llm_with_tools("ollama", None)
    assert llm_with_tools is not None


def test_get_llm_with_tools_openai(env_vars, monkeypatch):
    env_vars["OPENAI_API_KEY"] = "test-openai-key"
    _apply_env(env_vars, monkeypatch)
    with (
        patch("src.services.agent.server.ChatGroq") as mock_groq,
        patch("src.services.agent.server.ChatOpenAI") as mock_openai,
        patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings,
    ):
        mock_llm = MagicMock()
        mock_groq.return_value = mock_llm
        mock_openai.return_value = mock_llm
        mock_embeddings.return_value = MagicMock()
        from src.services.agent import server

        server = reload(server)
        server.CURRENT_SELECTION["provider"] = "openai"
        llm_with_tools = server._get_llm_with_tools("openai", None)
        assert llm_with_tools is not None


def test_get_llm_with_tools_unsupported_provider(env_vars, monkeypatch):
    server = _import_server(env_vars, monkeypatch)
    llm_with_tools = server._get_llm_with_tools("unsupported", None)
    assert llm_with_tools is not None


def test_sanitize_human_message(env_vars, monkeypatch):
    _import_server(env_vars, monkeypatch)
    from langchain_core.messages import HumanMessage

    from src.services.agent.server import _sanitize_messages

    messages = [HumanMessage(content="test")]
    sanitized = _sanitize_messages(messages)
    assert len(sanitized) == 1
    assert isinstance(sanitized[0].content, str)


def test_sanitize_tool_message_with_list_content(env_vars, monkeypatch):
    _import_server(env_vars, monkeypatch)
    from langchain_core.messages import AIMessage, ToolMessage

    from src.services.agent.server import _sanitize_messages

    messages = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "123",
                    "name": "db_search",
                    "args": {"query": "test"},
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(content=["item1", "item2"], tool_call_id="123", name="db_search"),
    ]
    sanitized = _sanitize_messages(messages)
    tool_messages = [message for message in sanitized if isinstance(message, ToolMessage)]
    assert len(tool_messages) == 1
    assert isinstance(tool_messages[0].content, str)

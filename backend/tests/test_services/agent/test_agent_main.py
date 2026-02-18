"""
Unit tests for src/agent/server.py

Tests FastAPI app initialization, route handlers, and agent logic.
"""
import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

pytestmark = pytest.mark.unit


class TestAgentMainInitialization:
    """Test initialization of agent/server.py components."""

    def test_app_creation(self, env_vars, monkeypatch):
        """Test that FastAPI app is created successfully."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            # Import app after mocks
            from src.services.agent import server
            assert server.app is not None

    def test_location_context_configured(self, env_vars, monkeypatch):
        """Test that location context is properly configured."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client"), \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.HuggingFaceEmbeddings"):

            from src.services.agent import server
            assert server.LOCATION_CONTEXT is not None
            assert "organization" in server.LOCATION_CONTEXT
            assert "location" in server.LOCATION_CONTEXT


class TestAgentThinkingMessages:
    """Test human-readable thinking messages for agent."""

    def test_agent_thinking_messages_exist(self, env_vars, monkeypatch):
        """Test that thinking messages are defined for Spanish and English."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client"), \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.HuggingFaceEmbeddings"):

            from src.services.agent import server
            assert "en" in server.AGENT_THINKING_MESSAGES
            assert "es" in server.AGENT_THINKING_MESSAGES

    def test_get_agent_thinking_message_english(self, env_vars, monkeypatch):
        """Test getting English thinking message."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client"), \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.HuggingFaceEmbeddings"):

            from src.services.agent import server
            msg = server.get_agent_thinking_message("plan", "en")
            assert msg == "Let me think about your question..."

    def test_get_agent_thinking_message_spanish(self, env_vars, monkeypatch):
        """Test getting Spanish thinking message."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client"), \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.HuggingFaceEmbeddings"):

            from src.services.agent import server
            msg = server.get_agent_thinking_message("db_search", "es")
            assert msg == "Revisando nuestros recursos locales..."

    def test_get_agent_thinking_message_fallback(self, env_vars, monkeypatch):
        """Test fallback to English for unknown language."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client"), \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.HuggingFaceEmbeddings"):

            from src.services.agent import server
            msg = server.get_agent_thinking_message("unknown_tool", "unknown_lang")
            assert msg == "Thinking..."


class TestAgentState:
    """Test AgentState TypedDict."""

    def test_agent_state_creation(self, env_vars, monkeypatch):
        """Test that AgentState can be created."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client"), \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.HuggingFaceEmbeddings"):

            from src.services.agent.server import AgentState
            from langchain_core.messages import HumanMessage

            state = AgentState(
                messages=[HumanMessage(content="test")],
                question="test question",
                language="en",
                provider="llama",
                model=None,
                plan=None
            )
            assert state["question"] == "test question"
            assert state["language"] == "en"


class TestEmbeddingInitialization:
    """Test embedding model initialization."""

    def test_embedding_service_fallback_chain(self, env_vars, monkeypatch):
        """Test that embedding initialization has fallback chain."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Simulate embedding service unavailable
        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings, \
             patch("src.services.agent.server.create_embedding_client", side_effect=Exception("Service unavailable")):

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            # Should have initialized with fallback
            assert server.embedding_model is not None


class TestLLMInitialization:
    """Test LLM provider initialization."""

    def test_llm_initialization_with_groq(self, env_vars, monkeypatch):
        """Test LLM initialization with Groq API key."""
        env_vars["GROQ_API_KEY"] = "test-groq-key"
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            assert server.llm is not None


class TestToolsInitialization:
    """Test tool initialization."""

    def test_tools_initialized(self, env_vars, monkeypatch):
        """Test that tools are initialized."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            assert isinstance(server.tools, list)
            assert len(server.tools) > 0
            tool_names = [tool.name for tool in server.tools]
            assert "static_response_tool" in tool_names

    def test_none_tools_filtered(self, env_vars, monkeypatch):
        """Test that None tools are filtered out."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            # All tools should be non-None
            assert all(tool is not None for tool in server.tools)


class TestLLMWithTools:
    """Test _get_llm_with_tools function."""

    def test_get_llm_with_tools_llama_ollama(self, env_vars, monkeypatch):
        """Test getting Llama LLM with Ollama."""
        env_vars["OLLAMA_BASE_URL"] = "http://localhost:11434"
        env_vars["OLLAMA_MODEL"] = "llama3.2"
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.ChatOllama") as mock_ollama, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm
            mock_ollama.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            # Set CURRENT_SELECTION for llama
            server.CURRENT_SELECTION["provider"] = "llama"
            llm_with_tools = server._get_llm_with_tools("llama", None)
            assert llm_with_tools is not None

    def test_get_llm_with_tools_openai(self, env_vars, monkeypatch):
        """Test getting OpenAI LLM."""
        env_vars["OPENAI_API_KEY"] = "test-openai-key"
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.ChatOpenAI") as mock_openai, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm
            mock_openai.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            server.CURRENT_SELECTION["provider"] = "openai"
            llm_with_tools = server._get_llm_with_tools("openai", None)
            assert llm_with_tools is not None

    def test_get_llm_with_tools_unsupported_provider(self, env_vars, monkeypatch):
        """Test that unsupported provider gracefully falls back to available provider."""
        # Set up environment with Groq API key
        env_vars["GROQ_API_KEY"] = "test-groq-key"
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_llm_bound = MagicMock()
            mock_llm.bind_tools = MagicMock(return_value=mock_llm_bound)
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent import server
            # Unsupported provider should fall back to available provider (Groq in this case)
            llm_with_tools = server._get_llm_with_tools("unsupported", None)
            # Should not raise error, but return valid LLM
            assert llm_with_tools is not None


class TestMessageSanitization:
    """Test _sanitize_messages function."""

    def test_sanitize_human_message(self, env_vars, monkeypatch):
        """Test sanitizing human message."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent.server import _sanitize_messages
            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content="test")]
            sanitized = _sanitize_messages(messages)
            assert len(sanitized) == 1
            assert isinstance(sanitized[0].content, str)

    def test_sanitize_tool_message_with_list_content(self, env_vars, monkeypatch):
        """Test sanitizing tool message with list content."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with patch("src.services.agent.server.create_client") as mock_supabase, \
             patch("src.services.agent.server.ChatGroq") as mock_groq, \
             patch("src.services.agent.server.HuggingFaceEmbeddings") as mock_embeddings:

            mock_supabase_client = MagicMock()
            mock_supabase.return_value = mock_supabase_client

            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm

            mock_embedding_model = MagicMock()
            mock_embeddings.return_value = mock_embedding_model

            from src.services.agent.server import _sanitize_messages
            from langchain_core.messages import ToolMessage

            messages = [ToolMessage(content=["item1", "item2"], tool_call_id="123")]
            sanitized = _sanitize_messages(messages)
            assert len(sanitized) == 1
            assert isinstance(sanitized[0].content, str)


class TestEnvironmentVariableValidation:
    """Test environment variable handling."""

    @pytest.mark.skip(reason="Module-level initialization testing is unreliable with mocks/reloads")
    def test_missing_supabase_url_raises_error(self, monkeypatch):
        """Test that missing Supabase URL raises error."""
        # Set up environment with missing SUPABASE_URL
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        monkeypatch.setenv("SUPABASE_KEY", "test-key")
        monkeypatch.delenv("SUPABASE_URL", raising=False)

        # Mock all the imports to prevent actual initialization
        with patch("src.services.agent.server.create_client") as mock_client, \
             patch("src.services.agent.server.ChatGroq"), \
             patch("src.services.agent.server.create_embedding_client"):
            
            # Make create_client not be called (validation should fail first)
            mock_client.side_effect = Exception("Should not reach here")
            
            with pytest.raises(ValueError, match="Supabase URL and key must be set"):
                import importlib
                from src.services.agent import server as agent_main
                importlib.reload(agent_main)

    @pytest.mark.skip(reason="Module-level initialization testing is unreliable with mocks/reloads")
    def test_missing_llm_provider_raises_error(self, monkeypatch):
        """Test that missing LLM provider raises error."""
        # Clear all LLM provider keys
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPEN_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

        # Mock dependencies to allow reload
        with patch("src.services.agent.server.create_client") as mock_client, \
             patch("src.services.agent.server.create_embedding_client"):
            
            mock_client.return_value = MagicMock()
            
            with pytest.raises(RuntimeError, match="No LLM provider configured"):
                import importlib
                from src.services.agent import server as agent_main
                importlib.reload(agent_main)

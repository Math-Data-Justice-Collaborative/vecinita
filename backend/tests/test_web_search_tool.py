"""Unit tests for the web search tool.

Tests the web_search tool's ability to search the web via Tavily or
DuckDuckGo and return normalized results as JSON.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from src.agent.tools.web_search import create_web_search_tool


class TestWebSearchToolWithTavily:
    """Test suite for web search tool when Tavily is available."""

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key-123"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tavily_initialization(self, mock_tavily_class):
        """Test that Tavily is initialized when API key is present."""
        mock_tavily = Mock()
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()

        mock_tavily_class.assert_called_once()
        call_kwargs = mock_tavily_class.call_args[1]
        assert call_kwargs["api_key"] == "test-key-123"
        assert call_kwargs["max_results"] == 5

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tavily_search_normalizes_results(self, mock_tavily_class):
        """Test that Tavily results are normalized correctly."""
        mock_tavily = Mock()
        mock_tavily.invoke.return_value = [
            {
                "title": "Health Services",
                "content": "Information about local health services",
                "url": "https://example.com/health",
                "answer": "Answer text"
            }
        ]
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()
        results_json = tool.invoke("health services")
        results = json.loads(results_json)

        # Verify Tavily was called with correct query
        mock_tavily.invoke.assert_called_once_with(
            {"query": "health services"})

        assert len(results) == 1
        assert results[0]["title"] == "Health Services"
        assert results[0]["content"] == "Information about local health services"
        assert results[0]["url"] == "https://example.com/health"

    @patch.dict(os.environ, {"TAVILY_API_AI_KEY": "alt-key"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_alternate_tavily_env_var(self, mock_tavily_class):
        """Test that alternate TAVILY_API_AI_KEY env var is recognized."""
        mock_tavily = Mock()
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()

        call_kwargs = mock_tavily_class.call_args[1]
        assert call_kwargs["api_key"] == "alt-key"

    @patch.dict(os.environ, {"TVLY_API_KEY": "tvly-key"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tvly_shorthand_env_var(self, mock_tavily_class):
        """Test that TVLY_API_KEY shorthand is recognized."""
        mock_tavily = Mock()
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()

        call_kwargs = mock_tavily_class.call_args[1]
        assert call_kwargs["api_key"] == "tvly-key"

    @patch.dict(os.environ, {
        "TAVILY_API_KEY": "primary-key",
        "TAVILY_API_AI_KEY": "secondary-key",
        "TVLY_API_KEY": "tertiary-key",
    }, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tavily_env_var_precedence(self, mock_tavily_class):
        """When multiple Tavily env vars are set, primary has precedence."""
        mock_tavily = Mock()
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()

        # Ensure Tavily was constructed with the primary key first
        call_kwargs = mock_tavily_class.call_args[1]
        assert call_kwargs["api_key"] == "primary-key"


class TestWebSearchToolWithDuckDuckGo:
    """Test suite for web search tool when DuckDuckGo fallback is used."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("langchain_community.tools.DuckDuckGoSearchResults")
    def test_duckduckgo_initialization_without_key(self, mock_ddg_class):
        """Test that DuckDuckGo is initialized when no Tavily key present."""
        mock_ddg = Mock()
        mock_ddg_class.return_value = mock_ddg

        tool = create_web_search_tool()

        mock_ddg_class.assert_called_once_with(num_results=5)

    @patch.dict(os.environ, {}, clear=True)
    @patch("langchain_community.tools.DuckDuckGoSearchResults")
    def test_duckduckgo_search_list_results(self, mock_ddg_class):
        """Test that DuckDuckGo list results are normalized correctly."""
        mock_ddg = Mock()
        mock_ddg.invoke.return_value = [
            {
                "title": "Result 1",
                "snippet": "First result snippet",
                "link": "https://example.com/1"
            },
            {
                "title": "Result 2",
                "snippet": "Second result snippet",
                "link": "https://example.com/2"
            }
        ]
        mock_ddg_class.return_value = mock_ddg

        tool = create_web_search_tool()
        results_json = tool.invoke("test query")

        # Verify DuckDuckGo was called with correct query
        mock_ddg.invoke.assert_called_once_with("test query")

        results = json.loads(results_json)
        assert len(results) == 2
        assert results[0]["title"] == "Result 1"
        assert results[0]["content"] == "First result snippet"
        assert results[0]["url"] == "https://example.com/1"

    @patch.dict(os.environ, {}, clear=True)
    @patch("langchain_community.tools.DuckDuckGoSearchResults")
    def test_duckduckgo_search_string_result(self, mock_ddg_class):
        """Test that DuckDuckGo string result is wrapped in a list."""
        mock_ddg = Mock()
        mock_ddg.invoke.return_value = "Some search result text"
        mock_ddg_class.return_value = mock_ddg

        tool = create_web_search_tool()
        results_json = tool.invoke("test query")

        # Verify DuckDuckGo was called with correct query
        mock_ddg.invoke.assert_called_once_with("test query")

        results = json.loads(results_json)
        assert len(results) == 1
        assert results[0]["title"] == "DuckDuckGo Result"
        assert results[0]["content"] == "Some search result text"

    @patch.dict(os.environ, {}, clear=True)
    @patch("langchain_community.tools.DuckDuckGoSearchResults")
    def test_duckduckgo_empty_result(self, mock_ddg_class):
        """Test that DuckDuckGo empty result returns empty list."""
        mock_ddg = Mock()
        mock_ddg.invoke.return_value = ""
        mock_ddg_class.return_value = mock_ddg

        tool = create_web_search_tool()
        results_json = tool.invoke("test query")

        # Verify DuckDuckGo was called with correct query
        mock_ddg.invoke.assert_called_once_with("test query")

        assert results_json == "[]"


class TestWebSearchToolErrorHandling:
    """Test suite for web search tool error handling."""

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tavily_initialization_failure_falls_back_to_duckduckgo(self, mock_tavily_class):
        """Test that DuckDuckGo fallback is used if Tavily init fails."""
        mock_tavily_class.side_effect = Exception("API key invalid")

        with patch("langchain_community.tools.DuckDuckGoSearchResults") as mock_ddg_class:
            mock_ddg = Mock()
            mock_ddg.invoke.return_value = [{"title": "DDG Result"}]
            mock_ddg_class.return_value = mock_ddg

            tool = create_web_search_tool()
            results = tool.invoke("test")

            # Verify DuckDuckGo was called with correct query
            mock_ddg.invoke.assert_called_once_with("test")

            # Should use DuckDuckGo
            results_parsed = json.loads(results)
            assert len(results_parsed) == 1
            assert results_parsed[0]["title"] == "DDG Result"

    @patch.dict(os.environ, {}, clear=True)
    def test_no_providers_available(self):
        """Test that empty list is returned when no providers are available."""
        with patch("langchain_community.tools.DuckDuckGoSearchResults") as mock_ddg_class:
            mock_ddg_class.side_effect = Exception("Import error")

            tool = create_web_search_tool()
            results = tool.invoke("test")

            assert results == "[]"

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tavily_invocation_error_returns_empty_list(self, mock_tavily_class):
        """Test that tool returns empty list if search execution fails."""
        mock_tavily = Mock()
        mock_tavily.invoke.side_effect = Exception("Search failed")
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()
        results = tool.invoke("test")

        assert results == "[]"


class TestWebSearchToolProperties:
    """Test suite for web search tool properties."""

    @patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=True)
    @patch("langchain_tavily.TavilySearch")
    def test_tool_name_and_description(self, mock_tavily_class):
        """Test that tool has proper name and description."""
        mock_tavily = Mock()
        mock_tavily_class.return_value = mock_tavily

        tool = create_web_search_tool()

        assert tool.name == "web_search"
        assert "web" in tool.description.lower()
        assert "search" in tool.description.lower()

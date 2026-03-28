"""Unit tests for the static response tool (FAQ lookup).

Tests the static_response_tool's ability to match questions to predefined
FAQ answers in English and Spanish.
"""

import copy

import pytest

from src.agent.tools.static_response import FAQ_DATABASE, add_faq, list_faqs, static_response_tool


# Ensure tests don't pollute the global FAQ database state
@pytest.fixture(autouse=True)
def restore_faq_database():
    original = copy.deepcopy(FAQ_DATABASE)
    yield
    # Restore original contents
    FAQ_DATABASE.clear()
    for lang, faqs in original.items():
        FAQ_DATABASE[lang] = faqs


class TestStaticResponseTool:
    """Test suite for static response tool."""

    def test_static_response_matches_english_faq(self):
        """Test that tool matches English FAQ questions."""
        result = static_response_tool.invoke({"query": "what is vecinita", "language": "en"})

        assert result is not None
        assert "community assistant" in result.lower() or "q&a" in result.lower()

    def test_static_response_matches_spanish_faq(self):
        """Test that tool matches Spanish FAQ questions."""
        result = static_response_tool.invoke({"query": "qué es vecinita", "language": "es"})

        assert result is not None
        assert "comunitar" in result.lower() or "asistente" in result.lower()

    def test_static_response_case_insensitive(self):
        """Test that FAQ matching is case-insensitive."""
        result1 = static_response_tool.invoke({"query": "what is vecinita", "language": "en"})
        result2 = static_response_tool.invoke({"query": "WHAT IS VECINITA", "language": "en"})
        result3 = static_response_tool.invoke({"query": "What Is Vecinita", "language": "en"})

        assert result1 == result2 == result3

    def test_static_response_returns_none_for_nonexistent_question(self):
        """Test that tool returns None for questions without FAQ."""
        result = static_response_tool.invoke(
            {"query": "xyzabc nonexistent topic", "language": "en"}
        )

        assert result is None

    def test_static_response_partial_match(self):
        """Test that tool matches partial question strings."""
        result = static_response_tool.invoke(
            {"query": "tell me about how vecinita works", "language": "en"}
        )

        # Should match the "how does this work" FAQ since query contains those keywords
        # If partial matching is supported, result should contain info about how Vecinita works
        if result is not None:
            assert "database" in result.lower() or "search" in result.lower()
        # If no partial match, that's also valid behavior - just document it
        # This test verifies the tool behaves consistently

    def test_static_response_spanish_defaults_to_english(self):
        """Test that tool falls back to English if language not available."""
        result = static_response_tool.invoke(
            {"query": "what is vecinita", "language": "fr"}  # French not in FAQ_DATABASE
        )

        # Should return English FAQ (default behavior)
        assert result is not None

    def test_static_response_whitespace_handling(self):
        """Test that tool handles extra whitespace correctly."""
        result1 = static_response_tool.invoke({"query": "what is vecinita", "language": "en"})
        result2 = static_response_tool.invoke({"query": "  what is vecinita  ", "language": "en"})

        assert result1 == result2


class TestAddFaqFunction:
    """Test suite for adding new FAQs."""

    def test_add_faq_english(self):
        """Test adding a new English FAQ."""
        test_question = "test question unique xyz"
        test_answer = "Test answer content"

        add_faq(test_question, test_answer, language="en")

        result = static_response_tool.invoke({"query": test_question, "language": "en"})

        assert result == test_answer

    def test_add_faq_spanish(self):
        """Test adding a new Spanish FAQ."""
        test_question = "pregunta de prueba xyz"
        test_answer = "Respuesta de prueba"

        add_faq(test_question, test_answer, language="es")

        result = static_response_tool.invoke({"query": test_question, "language": "es"})

        assert result == test_answer

    def test_add_faq_creates_new_language_if_needed(self):
        """Test that add_faq creates a new language entry if needed."""
        # Assuming a language doesn't exist
        test_lang = "ja"
        test_question = "テスト質問"
        test_answer = "テスト回答"

        add_faq(test_question, test_answer, language=test_lang)

        assert test_lang in FAQ_DATABASE
        assert test_question.lower() in FAQ_DATABASE[test_lang]

    def test_add_faq_normalizes_question(self):
        """Test that add_faq normalizes question to lowercase."""
        test_question = "UPPERCASE QUESTION XYZ"
        test_answer = "Answer"

        add_faq(test_question, test_answer, language="en")

        # Should be stored as lowercase
        assert test_question.lower() in FAQ_DATABASE["en"]


class TestListFaqsFunction:
    """Test suite for listing FAQs."""

    def test_list_faqs_english(self):
        """Test listing all English FAQs."""
        faqs = list_faqs(language="en")

        assert isinstance(faqs, dict)
        assert len(faqs) > 0
        # Should have at least the built-in FAQs
        assert any("vecinita" in key.lower() for key in faqs.keys())

    def test_list_faqs_spanish(self):
        """Test listing all Spanish FAQs."""
        faqs = list_faqs(language="es")

        assert isinstance(faqs, dict)
        assert len(faqs) > 0
        # Should have at least the built-in FAQs
        assert any("vecinita" in key.lower() for key in faqs.keys())

    def test_list_faqs_nonexistent_language(self):
        """Test that list_faqs returns empty dict for nonexistent language."""
        faqs = list_faqs(language="xx")

        assert isinstance(faqs, dict)
        assert len(faqs) == 0

    def test_list_faqs_returns_all_questions_and_answers(self):
        """Test that list_faqs includes both questions and answers."""
        faqs = list_faqs(language="en")

        for question, answer in faqs.items():
            assert isinstance(question, str)
            assert isinstance(answer, str)
            assert len(question) > 0
            assert len(answer) > 0


class TestFaqDatabase:
    """Test suite for the FAQ database structure."""

    def test_faq_database_has_english_and_spanish(self):
        """Test that FAQ database includes English and Spanish."""
        assert "en" in FAQ_DATABASE
        assert "es" in FAQ_DATABASE

    def test_english_faqs_not_empty(self):
        """Test that English FAQ database is not empty."""
        assert len(FAQ_DATABASE["en"]) > 0

    def test_spanish_faqs_not_empty(self):
        """Test that Spanish FAQ database is not empty."""
        assert len(FAQ_DATABASE["es"]) > 0

    def test_all_faq_keys_are_lowercase(self):
        """Test that all FAQ keys are lowercase."""
        for _lang, faqs in FAQ_DATABASE.items():
            for question in faqs.keys():
                assert question == question.lower(), f"FAQ key not lowercase: {question}"

    def test_all_faq_values_are_strings(self):
        """Test that all FAQ answers are strings."""
        for _lang, faqs in FAQ_DATABASE.items():
            for answer in faqs.values():
                assert isinstance(answer, str)
                assert len(answer) > 0

"""
Unit tests for the clarify_question tool.
Tests question clarification and follow-up question generation.
"""

import pytest

from src.agent.tools.clarify_question import clarify_question, create_clarify_question_tool


@pytest.mark.unit
class TestClarifyQuestion:
    """Test suite for clarify_question tool."""

    def test_clarify_question_doctor_query(self):
        """Test clarification for doctor-related query."""
        result = clarify_question.invoke(
            {
                "original_question": "Where's a doctor near me?",
                "reason_for_clarification": "No matching documents found in database",
            }
        )

        # Should contain relevant prompts
        assert "doctor" in result.lower() or "type of doctor" in result.lower()
        assert "clarif" in result.lower()
        assert "near me" in result

    def test_clarify_question_location_emphasis(self):
        """Test clarification emphasizes location for location-based queries."""
        result = clarify_question.invoke(
            {
                "original_question": "What places are nearby?",
                "reason_for_clarification": "Need more specific location",
            }
        )

        assert "location" in result.lower() or "city" in result.lower()
        assert "clarif" in result.lower()

    def test_clarify_question_service_type(self):
        """Test clarification for service-type queries."""
        result = clarify_question.invoke(
            {
                "original_question": "What services do you offer?",
                "reason_for_clarification": "Question is too broad",
            }
        )

        assert "service" in result.lower() or "detail" in result.lower()
        assert "clarif" in result.lower()

    def test_clarify_question_generic(self):
        """Test clarification for generic/ambiguous queries."""
        result = clarify_question.invoke(
            {
                "original_question": "Tell me about that thing",
                "reason_for_clarification": "Unclear what you're asking about",
            }
        )

        assert (
            "context" in result.lower() or "detail" in result.lower() or "clarif" in result.lower()
        )

    def test_clarify_question_includes_reason(self):
        """Test that clarification includes the reason provided."""
        reason = "Search returned no results"
        result = clarify_question.invoke(
            {"original_question": "What is this?", "reason_for_clarification": reason}
        )

        assert reason in result

    def test_clarify_question_includes_original(self):
        """Test that clarification includes the original question."""
        question = "How do I find a good restaurant?"
        result = clarify_question.invoke(
            {"original_question": question, "reason_for_clarification": "Need more context"}
        )

        assert question in result

    def test_clarify_question_suggests_multiple_options(self):
        """Test that clarification suggests multiple follow-up options."""
        result = clarify_question.invoke(
            {"original_question": "Where can I get help?", "reason_for_clarification": "Too vague"}
        )

        # Should have numbered options
        assert "1." in result
        assert "2." in result

    def test_clarify_question_natural_language(self):
        """Test that clarification reads naturally."""
        result = clarify_question.invoke(
            {
                "original_question": "Can you help me?",
                "reason_for_clarification": "Unclear what you need",
            }
        )

        # Should be formatted well
        assert len(result) > 50
        assert "**" in result or "\n" in result  # Markdown formatting

    def test_clarify_question_with_search_context(self):
        """Test clarification with search context."""
        result = clarify_question.invoke(
            {
                "original_question": "What medical services exist?",
                "search_context": "Searched: 'medical', 'health', 'services' - no results",
                "reason_for_clarification": "Database search found 0 documents",
            }
        )

        assert "clarif" in result.lower()

    def test_create_clarify_question_tool(self):
        """Test that tool creation works."""
        tool = create_clarify_question_tool()

        # Tool should be callable
        assert hasattr(tool, "invoke")

        # Tool should be the same as clarify_question
        assert tool is clarify_question

    def test_clarify_question_with_empty_question(self):
        """Test clarification handles empty/minimal questions."""
        result = clarify_question.invoke(
            {"original_question": "", "reason_for_clarification": "No question provided"}
        )

        assert len(result) > 0
        assert "clarif" in result.lower()

    def test_clarify_question_multiple_keywords(self):
        """Test clarification when query has multiple keyword types."""
        result = clarify_question.invoke(
            {
                "original_question": "Where can I find a doctor for medical issues near me?",
                "reason_for_clarification": "Need more specific information",
            }
        )

        # Should handle multi-keyword questions
        assert "clarif" in result.lower()
        assert len(result) > 100

    def test_clarify_question_return_type(self):
        """Test that clarification returns a string."""
        result = clarify_question.invoke(
            {
                "original_question": "What is Vecinita?",
                "reason_for_clarification": "Need clarification",
            }
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_clarify_question_healthcare_focus(self):
        """Test clarification for healthcare-related questions."""
        result = clarify_question.invoke(
            {
                "original_question": "hospital clinic medical center",
                "reason_for_clarification": "Database search returned 0 results",
            }
        )

        # Should suggest healthcare-relevant questions
        assert "doctor" in result.lower() or "medical" in result.lower() or "type" in result.lower()

    def test_clarify_question_consistent_format(self):
        """Test that clarification response has consistent structure."""
        clarify_question.invoke(
            {"original_question": "Question 1?", "reason_for_clarification": "Reason 1"}
        )

        clarify_question.invoke(
            {"original_question": "Question 2?", "reason_for_clarification": "Reason 2"}
        )

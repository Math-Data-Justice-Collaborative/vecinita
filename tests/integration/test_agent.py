"""Integration tests for the LangGraph refactored agent.

These tests verify that the agent properly uses tools and responds correctly.

**IMPORTANT:** These are integration tests that require:
- Valid SUPABASE_URL and SUPABASE_KEY environment variables
- Valid GROQ_API_KEY environment variable
- Active Supabase database with search_similar_documents RPC function
- Network connectivity for API calls

To run these tests:
    pytest tests/test_agent_langgraph.py -m integration

To skip these tests (e.g., in CI without credentials):
    pytest tests/test_agent_langgraph.py -m "not integration"

For unit tests with mocked dependencies, see:
    - test_db_search_tool.py
    - test_web_search_tool.py
    - test_static_response_tool.py
"""

import os
import pytest
from fastapi.testclient import TestClient

# Skip all integration tests if required environment variables are not set
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY"),
        os.getenv("GROQ_API_KEY")
    ]),
    reason="Integration tests require SUPABASE_URL, SUPABASE_KEY, and GROQ_API_KEY environment variables"
)

# Import app at module level with error handling
try:
    from src.agent.main import app
    APP_IMPORT_ERROR = None
except Exception as e:
    app = None
    APP_IMPORT_ERROR = str(e)


@pytest.mark.integration
def test_agent_basic_question(test_client):
    """Test that the agent can handle a basic question."""
    response = test_client.get(
        "/ask", params={"question": "What is Vecinita?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "thread_id" in data
    assert len(data["answer"]) > 0


@pytest.mark.integration
def test_agent_static_response(test_client):
    """Test that the agent uses the static_response_tool for FAQs."""
    response = test_client.get("/ask", params={"question": "what is vecinita"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # Should mention it's a community assistant or Q&A system
    assert any(keyword in data["answer"].lower() for keyword in [
               "community", "assistant", "q&a", "vecinita"])


@pytest.mark.integration
def test_agent_spanish_question(test_client):
    """Test that the agent responds in Spanish to Spanish questions."""
    response = test_client.get(
        "/ask", params={"question": "¿Qué es Vecinita?"})

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # Should contain Spanish keywords
    assert any(keyword in data["answer"].lower()
               for keyword in ["comunitar", "asistente", "proyecto"])


@pytest.mark.integration
def test_agent_conversation_history(test_client):
    """Test that the agent maintains conversation history with thread_id."""
    thread_id = "test-thread-123"

    # First question
    response1 = test_client.get("/ask", params={
        "question": "What is Vecinita?",
        "thread_id": thread_id
    })
    assert response1.status_code == 200

    # Second question in same thread
    response2 = test_client.get("/ask", params={
        "question": "Tell me more about it.",
        "thread_id": thread_id
    })
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["thread_id"] == thread_id


@pytest.mark.integration
def test_agent_empty_question(test_client):
    """Test that the agent rejects empty questions."""
    response = test_client.get("/ask", params={"question": ""})

    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"].lower()


@pytest.mark.integration
def test_health_endpoint(test_client):
    """Test that the health endpoint works."""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


# Fixtures
@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from src.agent.main import app
    return TestClient(app)

"""
Integration tests for token streaming endpoint (/ask-stream)

Tests the real-time token generation and SSE event format.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.integration


@pytest.mark.streaming
def test_streaming_endpoint_returns_sse_format(fastapi_client, parse_sse_events):
    """Test /ask-stream endpoint returns proper Server-Sent Events format"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        # Setup mock
        mock_supabase.rpc.return_value.data = [
            {
                "content": "Python is a language",
                "source_url": "https://python.org",
                "similarity": 0.95,
            }
        ]
        
        # Make request
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "What is Python?"}
        )
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        # Parse events
        events = parse_sse_events(response.text)
        
        # Should have multiple events
        assert len(events) > 0, "No SSE events received"
        
        # Check event types
        event_types = {e.get("type") for e in events}
        assert "token" in event_types, f"Missing token events. Got: {event_types}"
        assert "complete" in event_types, f"Missing complete event. Got: {event_types}"


@pytest.mark.streaming
def test_streaming_events_have_correct_structure(fastapi_client, parse_sse_events):
    """Test each streaming event has required fields"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        mock_supabase.rpc.return_value.data = []
        
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "Test?"}
        )
        
        events = parse_sse_events(response.text)
        
        for event in events:
            # All events must have a type
            assert "type" in event, f"Event missing 'type': {event}"
            assert event["type"] in [
                "thinking", "token", "source", "complete", "error"
            ], f"Invalid event type: {event['type']}"
            
            # Token events must have content
            if event["type"] == "token":
                assert "content" in event, f"Token event missing 'content': {event}"
                assert "cumulative" in event, f"Token event missing 'cumulative': {event}"
            
            # Complete event must have metadata
            if event["type"] == "complete":
                assert "answer" in event, f"Complete event missing 'answer': {event}"
                assert "metadata" in event, f"Complete event missing 'metadata': {event}"
                assert "model_used" in event["metadata"]
                assert "tokens" in event["metadata"]


@pytest.mark.streaming
def test_token_accumulation_in_streaming(fastapi_client, parse_sse_events):
    """Test tokens accumulate correctly in cumulative field"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        mock_supabase.rpc.return_value.data = []
        
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "What?"}
        )
        
        events = parse_sse_events(response.text)
        token_events = [e for e in events if e.get("type") == "token"]
        
        if len(token_events) > 1:
            # Later cumulative should be longer than earlier
            prev_length = 0
            for event in token_events:
                cumulative = event.get("cumulative", "")
                assert len(cumulative) >= prev_length, \
                    f"Token cumulative not accumulating: {cumulative}"
                prev_length = len(cumulative)


@pytest.mark.streaming
def test_streaming_with_sources(fastapi_client, parse_sse_events):
    """Test streaming includes source discovery events"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        # Mock document retrieval
        mock_supabase.rpc.return_value.data = [
            {
                "content": "Python info",
                "source_url": "https://example.com/python",
                "similarity": 0.95,
            }
        ]
        
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "What is Python?"}
        )
        
        events = parse_sse_events(response.text)
        complete_event = next(
            (e for e in events if e.get("type") == "complete"), None
        )
        
        if complete_event:
            assert "sources" in complete_event, \
                f"Complete event should have sources: {complete_event}"


@pytest.mark.streaming
def test_streaming_error_handling(fastapi_client, parse_sse_events):
    """Test streaming handles errors gracefully"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        # Simulate database error
        mock_supabase.rpc.side_effect = Exception("Database error")
        
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "Will fail?"}
        )
        
        # Should still return 200 with error event
        assert response.status_code in [200, 500]  # Either streaming or error response
        
        if response.status_code == 200:
            events = parse_sse_events(response.text)
            # Should have error event
            has_error = any(e.get("type") == "error" for e in events)
            # Or at least complete with no answer
            assert has_error or len(events) > 0


@pytest.mark.streaming
def test_streaming_metadata_tracking(fastapi_client, parse_sse_events):
    """Test that streaming response includes model and token metadata"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase, \
         patch("src.services.agent.server._get_llm_with_tools") as mock_get_llm:
        
        # Setup mocks
        mock_supabase.rpc.return_value.data = []
        
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(return_value=MagicMock(
            content="Test answer",
            response_metadata={"usage_metadata": {"output_tokens": 25}}
        ))
        mock_llm.model_name = "deepseek-chat"
        mock_get_llm.return_value = mock_llm
        
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "Test?"}
        )
        
        events = parse_sse_events(response.text)
        complete_event = next(
            (e for e in events if e.get("type") == "complete"), None
        )
        
        if complete_event and "metadata" in complete_event:
            metadata = complete_event["metadata"]
            assert "model_used" in metadata, "Missing model_used in metadata"
            assert "tokens" in metadata, "Missing tokens in metadata"
            # Model should indicate a provider and model name
            assert ":" in metadata.get("model_used", ""), \
                f"model_used should be 'provider:model' format, got: {metadata['model_used']}"


@pytest.mark.streaming
def test_streaming_empty_response(fastapi_client, parse_sse_events):
    """Test streaming handles empty or minimal responses"""
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        # Empty search results
        mock_supabase.rpc.return_value.data = []
        
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "Obscure question with no results?"}
        )
        
        assert response.status_code == 200
        events = parse_sse_events(response.text)
        
        # Should still have at least a complete event
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) > 0, "No complete event. Events: " + str(events)


@pytest.mark.streaming
@pytest.mark.slow
def test_streaming_response_time(fastapi_client):
    """Test streaming response completes in reasonable time"""
    import time
    
    with patch("src.services.agent.server.supabase") as mock_supabase:
        mock_supabase.rpc.return_value.data = [
            {"content": "Test", "source_url": "https://example.com", "similarity": 0.9}
        ]
        
        start = time.time()
        response = fastapi_client.get(
            "/ask-stream",
            params={"question": "Fast test?"}
        )
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 10, f"Streaming took too long: {elapsed}s"
        assert response.status_code == 200

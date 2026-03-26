"""Tests for intent-gated deterministic RAG behavior in src.agent.main endpoints."""

import asyncio
import json
from unittest.mock import Mock


def _module():
    import src.agent.main as agent_main

    return agent_main


async def _collect_streaming_body(streaming_response) -> str:
    parts: list[str] = []
    async for chunk in streaming_response.generator:
        if isinstance(chunk, bytes):
            parts.append(chunk.decode("utf-8", errors="ignore"))
        else:
            parts.append(str(chunk))
    return "".join(parts)


class _CapturedStreamingResponse:
    def __init__(self, generator, media_type=None):
        self.generator = generator
        self.media_type = media_type
        self.status_code = 200


def test_ask_answer_seeking_runs_db_search_once_and_returns_sources(fastapi_client, monkeypatch):
    agent_main = _module()

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent_main, "static_response_tool", Mock(invoke=Mock(return_value=None)))

    db_search_mock = Mock(
        return_value=json.dumps(
            [
                {
                    "content": "Housing help is available in Providence.",
                    "source_url": "https://example.org/housing",
                    "similarity": 0.91,
                    "chunk_index": 0,
                }
            ]
        )
    )
    monkeypatch.setattr(agent_main, "db_search_tool", Mock(invoke=db_search_mock))

    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(
        content="Grounded response. (Source: https://example.org/housing)"
    )
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    response = fastapi_client.get(
        "/ask", params={"question": "What housing programs are available?"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload and payload["answer"]
    assert "sources" in payload and len(payload["sources"]) == 1
    assert payload["sources"][0]["url"] == "https://example.org/housing"
    assert db_search_mock.call_count == 1


def test_ask_non_answer_intent_skips_db_search(fastapi_client, monkeypatch):
    agent_main = _module()

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent_main, "static_response_tool", Mock(invoke=Mock(return_value=None)))

    db_search_mock = Mock(return_value="[]")
    monkeypatch.setattr(agent_main, "db_search_tool", Mock(invoke=db_search_mock))

    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(content="Hello! How can I help?")
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    response = fastapi_client.get("/ask", params={"question": "hello"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["sources"] == []
    assert db_search_mock.call_count == 0


def test_ask_weak_retrieval_adds_warning_banner(fastapi_client, monkeypatch):
    agent_main = _module()

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agent_main, "static_response_tool", Mock(invoke=Mock(return_value=None)))

    monkeypatch.setattr(
        agent_main,
        "db_search_tool",
        Mock(
            invoke=Mock(
                return_value=json.dumps(
                    [
                        {
                            "content": "Partial and weakly matched content.",
                            "source_url": "https://example.org/weak",
                            "similarity": 0.12,
                        }
                    ]
                )
            )
        ),
    )

    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(content="Best-effort answer.")
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    response = fastapi_client.get(
        "/ask", params={"question": "How can I improve local water quality?"}
    )

    assert response.status_code == 200
    payload = response.json()
    assert "⚠️" in payload["answer"]


def test_stream_answer_seeking_runs_db_search_once(fastapi_client, parse_sse_events, monkeypatch):
    agent_main = _module()

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)

    db_search_mock = Mock(
        return_value=json.dumps(
            [
                {
                    "content": "Food pantry resources in Providence.",
                    "source_url": "https://example.org/food",
                    "similarity": 0.88,
                }
            ]
        )
    )
    monkeypatch.setattr(agent_main, "db_search_tool", Mock(invoke=db_search_mock))

    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(
        content="Use local pantry resources. (Source: https://example.org/food)"
    )
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    response = fastapi_client.get(
        "/ask-stream", params={"question": "Where can I find food assistance?"}
    )

    assert response.status_code == 200
    assert db_search_mock.call_count == 1

    events = parse_sse_events(response.text)
    if events:
        complete = next((event for event in events if event.get("type") == "complete"), None)
        assert complete is not None
        assert len(complete.get("sources", [])) == 1


def test_stream_non_answer_intent_skips_db_search(fastapi_client, parse_sse_events, monkeypatch):
    agent_main = _module()

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)

    db_search_mock = Mock(return_value="[]")
    monkeypatch.setattr(agent_main, "db_search_tool", Mock(invoke=db_search_mock))

    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(content="Hi there!")
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    response = fastapi_client.get("/ask-stream", params={"question": "hello"})

    assert response.status_code == 200
    assert db_search_mock.call_count == 0

    events = parse_sse_events(response.text)
    if events:
        complete = next((event for event in events if event.get("type") == "complete"), None)
        assert complete is not None
        assert complete.get("sources", []) == []


def test_stream_spanish_thinking_messages_are_localized(parse_sse_events, monkeypatch):
    agent_main = _module()
    monkeypatch.setattr(agent_main, "StreamingResponse", _CapturedStreamingResponse)

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        agent_main,
        "db_search_tool",
        Mock(
            invoke=Mock(
                return_value=json.dumps(
                    [
                        {
                            "content": "Hay recursos de alimentos en Providence.",
                            "source_url": "https://example.org/es-food",
                            "similarity": 0.9,
                        }
                    ]
                )
            )
        ),
    )

    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(
        content="Puedes usar recursos locales. (Fuente: https://example.org/es-food)"
    )
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    streaming_response = asyncio.run(
        agent_main.ask_question_stream(
            question="¿Dónde puedo encontrar ayuda con alimentos?",
            query=None,
            thread_id="default",
            lang="es",
            provider=None,
            model=None,
            clarification_response=None,
            tags=None,
            tag_match_mode="any",
            include_untagged_fallback=True,
            rerank=False,
            rerank_top_k=10,
        )
    )
    body_text = asyncio.run(_collect_streaming_body(streaming_response))
    body_text = body_text.replace("\\n\\n", "\n\n")

    events = parse_sse_events(body_text)
    assert "data:" in body_text, "Expected SSE payload lines in response body"
    assert events, "Expected non-empty SSE event stream"

    thinking_messages = [
        event.get("message", "") for event in events if event.get("type") == "thinking"
    ]
    assert thinking_messages, "Expected at least one 'thinking' SSE event"

    assert any("Verificando si ya conozco esto..." in message for message in thinking_messages)
    assert any("Entendiendo tu pregunta..." in message for message in thinking_messages)
    assert any("Revisando nuestros recursos locales..." in message for message in thinking_messages)
    assert any("Finalizando respuesta..." in message for message in thinking_messages)
    assert all("Finalizing answer..." not in message for message in thinking_messages)


def test_stream_spanish_rate_limit_error_is_localized(parse_sse_events, monkeypatch):
    agent_main = _module()
    monkeypatch.setattr(agent_main, "StreamingResponse", _CapturedStreamingResponse)

    monkeypatch.setattr(agent_main, "_find_static_faq_answer", lambda *_args, **_kwargs: None)

    SpanishRateLimitError = type("RateLimitError", (Exception,), {})
    monkeypatch.setattr(
        agent_main,
        "db_search_tool",
        Mock(invoke=Mock(side_effect=SpanishRateLimitError("rate limited"))),
    )

    streaming_response = asyncio.run(
        agent_main.ask_question_stream(
            question="¿Qué apoyo hay para vivienda?",
            query=None,
            thread_id="default",
            lang="es",
            provider=None,
            model=None,
            clarification_response=None,
            tags=None,
            tag_match_mode="any",
            include_untagged_fallback=True,
            rerank=False,
            rerank_top_k=10,
        )
    )
    body_text = asyncio.run(_collect_streaming_body(streaming_response))
    body_text = body_text.replace("\\n\\n", "\n\n")

    events = parse_sse_events(body_text)
    assert "data:" in body_text, "Expected SSE payload lines in response body"
    assert events, "Expected non-empty SSE event stream"
    error_event = next((event for event in events if event.get("type") == "error"), None)
    assert error_event is not None, "Expected an 'error' SSE event"
    assert "Servicio temporalmente no disponible" in error_event.get("message", "")

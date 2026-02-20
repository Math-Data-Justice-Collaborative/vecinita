"""Unit tests for LangGraph RAG routing helpers in src.agent.main."""

import importlib
from unittest.mock import Mock

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def _agent_main_module():
    return importlib.import_module("src.agent.main")


def test_route_after_tools_grades_when_db_docs_present():
    agent_main = _agent_main_module()
    state = {
        "messages": [
            HumanMessage(content="What housing programs exist?"),
            ToolMessage(
                content='[{"content": "Housing support details", "source_url": "https://example.com"}]',
                tool_call_id="tool-1",
                name="db_search",
            ),
        ],
        "question": "What housing programs exist?",
        "language": "en",
        "provider": "deepseek",
        "model": None,
        "plan": None,
        "fast_mode": False,
        "grade_result": None,
    }

    route = agent_main.route_after_tools(state)
    assert route == "rank_retrieval"


def test_rank_retrieval_node_emits_ranked_tool_message():
    agent_main = _agent_main_module()
    state = {
        "messages": [
            HumanMessage(content="What housing programs exist?"),
            ToolMessage(
                content='[{"content": "Housing support details", "source_url": "https://example.com", "similarity": 0.9}]',
                tool_call_id="tool-1",
                name="db_search",
            ),
        ],
        "question": "What housing programs exist?",
        "language": "en",
        "provider": "deepseek",
        "model": None,
        "plan": None,
        "fast_mode": False,
        "grade_result": None,
    }

    ranked_state = agent_main.rank_retrieval_node(state)
    assert "messages" in ranked_state
    ranked_msg = ranked_state["messages"][0]
    assert isinstance(ranked_msg, ToolMessage)
    assert ranked_msg.name == "rank_retrieval_results"


def test_grade_documents_routes_to_rewrite_when_irrelevant(monkeypatch):
    agent_main = _agent_main_module()
    fake_scored = Mock()
    fake_scored.binary_score = "no"

    fake_llm = Mock()
    fake_llm.with_structured_output.return_value.invoke.return_value = fake_scored

    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    state = {
        "messages": [
            HumanMessage(content="What housing programs exist?"),
            ToolMessage(
                content='[{"content": "Unrelated topic text"}]',
                tool_call_id="tool-1",
                name="db_search",
            ),
            ToolMessage(
                content='[{"content": "Unrelated topic text"}]',
                tool_call_id="tool-2",
                name="rank_retrieval_results",
            ),
        ],
        "question": "What housing programs exist?",
        "language": "en",
        "provider": "deepseek",
        "model": None,
        "plan": None,
        "fast_mode": False,
        "grade_result": None,
    }

    grade_state = agent_main.grade_documents_node(state)
    assert grade_state["grade_result"] == "no"

    merged_state = {**state, **grade_state}
    assert agent_main.route_after_grading(merged_state) == "rewrite_question"


def test_rewrite_question_node_emits_human_message(monkeypatch):
    agent_main = _agent_main_module()
    fake_llm = Mock()
    fake_llm.invoke.return_value = Mock(content="What housing assistance programs are available in Providence?")
    monkeypatch.setattr(agent_main, "_get_llm_without_tools", lambda *_args, **_kwargs: fake_llm)

    state = {
        "messages": [HumanMessage(content="test")],
        "question": "test",
        "language": "en",
        "provider": "deepseek",
        "model": None,
        "plan": None,
        "grade_result": "no",
    }

    rewritten = agent_main.rewrite_question_node(state)
    assert "messages" in rewritten
    assert isinstance(rewritten["messages"][0], HumanMessage)
    assert "housing assistance" in rewritten["messages"][0].content.lower()


def test_sanitize_messages_drops_orphan_tool_messages():
    agent_main = _agent_main_module()
    messages = [
        HumanMessage(content="Find local housing support"),
        ToolMessage(
            content='[{"content": "ranked docs"}]',
            tool_call_id="rank-retrieval-node",
            name="rank_retrieval_results",
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call-db-1",
                    "name": "db_search",
                    "args": {"query": "housing"},
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(
            content='[{"content": "db docs"}]',
            tool_call_id="call-db-1",
            name="db_search",
        ),
    ]

    sanitized = agent_main._sanitize_messages(messages)
    tool_messages = [msg for msg in sanitized if isinstance(msg, ToolMessage)]

    assert len(tool_messages) == 1
    assert tool_messages[0].tool_call_id == "call-db-1"
    assert tool_messages[0].name == "db_search"


def test_sanitize_messages_keeps_tool_messages_with_matching_tool_calls():
    agent_main = _agent_main_module()
    messages = [
        HumanMessage(content="Find utility assistance"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": "call-1",
                    "name": "db_search",
                    "args": {"query": "utility assistance"},
                    "type": "tool_call",
                },
                {
                    "id": "call-2",
                    "name": "web_search",
                    "args": {"query": "Rhode Island utility help"},
                    "type": "tool_call",
                },
            ],
        ),
        ToolMessage(content='[{"content": "local docs"}]', tool_call_id="call-1", name="db_search"),
        ToolMessage(content='[{"content": "web docs"}]', tool_call_id="call-2", name="web_search"),
    ]

    sanitized = agent_main._sanitize_messages(messages)
    tool_messages = [msg for msg in sanitized if isinstance(msg, ToolMessage)]

    assert len(tool_messages) == 2
    assert {msg.tool_call_id for msg in tool_messages} == {"call-1", "call-2"}


def test_agent_node_invokes_llm_without_orphan_tool_messages(monkeypatch):
    agent_main = _agent_main_module()

    class FakeLLM:
        def __init__(self):
            self.seen_messages = None

        def invoke(self, messages):
            self.seen_messages = messages
            return AIMessage(content="ok")

    fake_llm = FakeLLM()

    monkeypatch.setattr(
        agent_main,
        "_provider_candidates_for_request",
        lambda *_args, **_kwargs: [("deepseek", "deepseek-chat")],
    )
    monkeypatch.setattr(
        agent_main,
        "_get_llm_with_tools",
        lambda *_args, **_kwargs: fake_llm,
    )

    state = {
        "messages": [
            HumanMessage(content="What housing programs are available?"),
            ToolMessage(
                content='[{"content": "ranked docs"}]',
                tool_call_id="rank-retrieval-node",
                name="rank_retrieval_results",
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call-db-1",
                        "name": "db_search",
                        "args": {"query": "housing programs"},
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content='[{"content": "db docs"}]',
                tool_call_id="call-db-1",
                name="db_search",
            ),
        ],
        "question": "What housing programs are available?",
        "language": "en",
        "provider": "deepseek",
        "model": None,
        "plan": None,
        "fast_mode": False,
        "grade_result": None,
    }

    output = agent_main.agent_node(state)

    assert "messages" in output
    assert isinstance(output["messages"][0], AIMessage)
    seen_tools = [m for m in fake_llm.seen_messages if isinstance(m, ToolMessage)]
    assert len(seen_tools) == 1
    assert seen_tools[0].tool_call_id == "call-db-1"

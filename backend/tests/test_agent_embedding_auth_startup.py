"""Regression tests for agent embedding auth startup wiring."""

import importlib
import sys
import types
from unittest.mock import Mock


def _install_fastembed_stub(monkeypatch):
    fake_fastembed_module = types.ModuleType("langchain_community.embeddings.fastembed")

    class _FakeFastEmbedEmbeddings:
        def __init__(self, *args, **kwargs):
            pass

        def embed_query(self, _text):
            return [0.1] * 384

    fake_fastembed_module.FastEmbedEmbeddings = _FakeFastEmbedEmbeddings

    fake_embeddings_module = types.ModuleType("langchain_community.embeddings")
    fake_embeddings_module.fastembed = fake_fastembed_module

    fake_langchain_community = types.ModuleType("langchain_community")
    fake_langchain_community.embeddings = fake_embeddings_module

    monkeypatch.setitem(sys.modules, "langchain_community", fake_langchain_community)
    monkeypatch.setitem(sys.modules, "langchain_community.embeddings", fake_embeddings_module)
    monkeypatch.setitem(
        sys.modules, "langchain_community.embeddings.fastembed", fake_fastembed_module
    )


def _install_langdetect_stub(monkeypatch):
    fake_langdetect_module = types.ModuleType("langdetect")

    class _FakeLangDetectException(Exception):
        pass

    fake_langdetect_module.detect = lambda _text: "en"
    fake_langdetect_module.LangDetectException = _FakeLangDetectException
    monkeypatch.setitem(sys.modules, "langdetect", fake_langdetect_module)


def _reload_agent_main(monkeypatch, create_embedding_client):
    _install_fastembed_stub(monkeypatch)
    _install_langdetect_stub(monkeypatch)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)

    fake_embedding_module = types.ModuleType("src.embedding_service.client")
    fake_chroma_store_module = types.ModuleType("src.services.chroma_store")

    class _FakeChromaStore:
        def heartbeat(self):
            return True

    fake_embedding_module.create_embedding_client = create_embedding_client
    fake_chroma_store_module.ChromaStore = _FakeChromaStore
    fake_chroma_store_module.get_chroma_store = lambda *_args, **_kwargs: Mock(
        heartbeat=Mock(return_value=True)
    )

    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setenv("DEFAULT_PROVIDER", "ollama")
    monkeypatch.setenv("AGENT_ENFORCE_ROUTE", "false")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("MODEL_SELECTION_PATH", "/tmp/vecinita-test-model-selection.json")
    monkeypatch.setenv("SKIP_AGENT_MAIN_IMPORT", "true")
    monkeypatch.setitem(sys.modules, "src.embedding_service.client", fake_embedding_module)
    monkeypatch.setitem(sys.modules, "src.services.chroma_store", fake_chroma_store_module)

    import src.config as config

    importlib.reload(config)

    import src.agent.main as agent_main

    monkeypatch.setattr(agent_main, "create_client", Mock(return_value=Mock()))
    monkeypatch.setattr(
        agent_main, "get_chroma_store", Mock(return_value=Mock(heartbeat=Mock(return_value=True)))
    )
    monkeypatch.setattr(
        agent_main, "create_db_search_tool", Mock(return_value=Mock(name="db_search"))
    )
    monkeypatch.setattr(
        agent_main,
        "create_static_response_tool",
        Mock(return_value=Mock(name="static_response_tool")),
    )
    monkeypatch.setattr(
        agent_main, "create_web_search_tool", Mock(return_value=Mock(name="web_search"))
    )
    monkeypatch.setattr(
        agent_main, "create_clarify_question_tool", Mock(return_value=Mock(name="clarify_question"))
    )
    monkeypatch.setattr(
        agent_main,
        "create_rank_retrieval_tool",
        Mock(return_value=Mock(name="rank_retrieval_results")),
    )
    monkeypatch.setattr(
        agent_main,
        "create_rewrite_question_tool",
        Mock(return_value=Mock(name="rewrite_question_tool")),
    )

    return importlib.reload(agent_main)


def test_agent_startup_passes_explicit_embedding_auth_token(monkeypatch):
    create_embedding_client = Mock(return_value=Mock(embed_query=Mock(return_value=[0.1] * 384)))
    monkeypatch.setenv("EMBEDDING_SERVICE_AUTH_TOKEN", "explicit-auth-token")

    _reload_agent_main(monkeypatch, create_embedding_client)

    create_embedding_client.assert_called()
    _, kwargs = create_embedding_client.call_args
    assert kwargs["auth_token"] == "explicit-auth-token"


def test_agent_startup_uses_modal_secret_as_embedding_auth_fallback(monkeypatch):
    create_embedding_client = Mock(return_value=Mock(embed_query=Mock(return_value=[0.1] * 384)))
    monkeypatch.delenv("EMBEDDING_SERVICE_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "modal-secret-token")

    _reload_agent_main(monkeypatch, create_embedding_client)

    create_embedding_client.assert_called()
    _, kwargs = create_embedding_client.call_args
    assert kwargs["auth_token"] == "modal-secret-token"


def test_agent_forces_local_modal_llm_provider_candidates(monkeypatch):
    create_embedding_client = Mock(return_value=Mock(embed_query=Mock(return_value=[0.1] * 384)))
    monkeypatch.setenv("MODAL_OLLAMA_ENDPOINT", "https://vecinita--vecinita-model-api.modal.run")
    monkeypatch.setenv("FORCE_LOCAL_MODAL_LLM", "true")

    agent_main = _reload_agent_main(monkeypatch, create_embedding_client)

    candidates = agent_main._provider_candidates_for_request("deepseek", "deepseek-chat")
    assert candidates[0][0] == "ollama"


def test_modal_native_chat_api_detection(monkeypatch):
    create_embedding_client = Mock(return_value=Mock(embed_query=Mock(return_value=[0.1] * 384)))
    monkeypatch.setenv("MODAL_OLLAMA_ENDPOINT", "https://vecinita--vecinita-model-api.modal.run")
    monkeypatch.setenv("MODAL_OLLAMA_USE_NATIVE_API", "true")

    agent_main = _reload_agent_main(monkeypatch, create_embedding_client)

    assert agent_main._use_modal_native_chat_api("https://vecinita--vecinita-model-api.modal.run")
    assert not agent_main._use_modal_native_chat_api("http://localhost:11434")


def test_modal_native_chat_client_invoke(monkeypatch):
    create_embedding_client = Mock(return_value=Mock(embed_query=Mock(return_value=[0.1] * 384)))
    monkeypatch.setenv("MODAL_OLLAMA_ENDPOINT", "https://vecinita--vecinita-model-api.modal.run")
    monkeypatch.setenv("MODAL_OLLAMA_USE_NATIVE_API", "true")

    agent_main = _reload_agent_main(monkeypatch, create_embedding_client)

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"model": "llama3.2:latest", "message": {"role": "assistant", "content": "ok"}}

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json=None, headers=None):
            assert url.endswith("/chat")
            assert isinstance(json, dict)
            assert "messages" in json
            return _Resp()

    from src.services.llm import client_manager as llm_client_manager

    assert agent_main.llm_client_manager.uses_modal_native_chat_api()
    monkeypatch.setattr(llm_client_manager.httpx, "Client", _Client)

    llm = agent_main._get_llm_without_tools("ollama", "llama3.2")
    response = llm.invoke([agent_main.HumanMessage(content="hello")])
    assert response.content == "ok"

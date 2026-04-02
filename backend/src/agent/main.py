"""Vecinita Agent — FastAPI RAG Q&A Service.

This module is the primary entry point for the Vecinita LangGraph-powered
RAG (Retrieval-Augmented Generation) agent.  It exposes three main endpoints:

- ``GET /ask``        — synchronous question answering with source attribution
- ``GET /ask-stream`` — streaming (SSE) question answering with live agent
                        activity updates (thinking / clarification / complete)
- ``GET /config``     — LLM provider/model discovery for the frontend

Deployment routing (Render)
---------------------------
On Render, all model and embedding traffic is routed through the internal
modal-proxy private service (``vecinita-modal-proxy-v1:10000``) using path
prefixes recognised by the proxy:

- ``/model/...``     → Ollama-compatible model backend  (strips ``/model``)
- ``/embedding/...`` → Embedding backend                (strips ``/embedding``)

This is enforced at startup by ``_normalize_internal_service_url``.  Any
env vars pointing at ``localhost``, Docker-internal hostnames, or direct
Modal endpoints are silently replaced with the proxy URL on Render.

Environment variables (minimum required)
-----------------------------------------
- ``SUPABASE_URL`` / ``SUPABASE_KEY`` — vector-store access
- ``OLLAMA_BASE_URL``                 — Ollama server (local/Docker dev only;
                                        overridden by proxy on Render)
- ``GROQ_API_KEY``                    — optional Groq provider
- ``OPENAI_API_KEY``                  — optional OpenAI provider
- ``EMBEDDING_SERVICE_URL``           — embedding microservice (local/Docker;
                                        overridden by proxy on Render)
"""

# ruff: noqa: E402, I001

import json
import inspect
import logging
import os
import re
import time
import traceback
import warnings
from datetime import datetime, timezone
from pathlib import Path

# Avoid hard torch dependency during transformers import on CPU-only/broken torch envs.
os.environ.setdefault("USE_TORCH", "0")
os.environ.setdefault("TRANSFORMERS_NO_TORCH", "1")
# Suppress advisory warning about missing torch/tensorflow/flax in local CPU paths.
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

# Suppress non-blocking transformers advisory on CPU-only environments.
# This warning appears when PyTorch/TensorFlow/Flax are not installed but
# doesn't prevent embedding service (HTTP-based) from functioning.
warnings.filterwarnings(
    "ignore",
    message=".*None of PyTorch.*TensorFlow.*Flax have been found.*",
    category=UserWarning,
)

from typing import Annotated, Any, Literal, TypedDict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from supabase import Client, create_client

# Optional fallback embedding class; imported lazily only when needed.
FastEmbedEmbeddings = None

try:
    from langdetect import LangDetectException, detect  # type: ignore[import-not-found]
except Exception:

    class LangDetectException(Exception):
        pass

    def detect(_text: str) -> str:
        return "en"


try:
    import psycopg2
except Exception:  # pragma: no cover - optional dependency in some test/runtime profiles
    psycopg2 = None  # type: ignore[assignment]


from src.services.chroma_store import get_chroma_store
from src.services.llm import LocalLLMClientManager
from src.utils.tags import parse_tags_input

from .tools.clarify_question import create_clarify_question_tool

# Import tools
from .tools.db_search import create_db_search_tool, get_last_search_metrics, get_last_search_status
from .tools.db_search import reset_search_options as reset_db_search_options
from .tools.db_search import set_search_options as set_db_search_options
from .tools.rank_retrieval import create_rank_retrieval_tool
from .tools.rewrite_question import create_rewrite_question_tool
from .tools.static_response import FAQ_DATABASE, create_static_response_tool
from .tools.web_search import create_web_search_tool

# Load environment variables with deterministic precedence:
# runtime shell env > root .env > backend/.env defaults.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env", override=False)
load_dotenv(_BACKEND_ROOT / ".env", override=False)

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Providers that failed with transport/connect errors in current process.
_RUNTIME_PROVIDER_BLOCKLIST: set[str] = set()

# Lazy-loaded optional classes (avoid importing heavy/fragile deps at startup)
ChatOllama = None
_CHATOLLAMA_IMPORT_ERROR = None
HuggingFaceEmbeddings = None
_HF_EMBEDDINGS_IMPORT_ERROR = None


def _get_chatollama_class():
    """Load ChatOllama lazily so startup doesn't fail on optional deps."""
    global ChatOllama, _CHATOLLAMA_IMPORT_ERROR
    if ChatOllama is not None:
        return ChatOllama
    if _CHATOLLAMA_IMPORT_ERROR is not None:
        return None
    try:
        from langchain_ollama import ChatOllama as _ChatOllama  # type: ignore[import-not-found]

        ChatOllama = _ChatOllama
        return ChatOllama
    except Exception as exc:
        _CHATOLLAMA_IMPORT_ERROR = exc
        logger.warning(
            "langchain_ollama unavailable at startup (%s). Ollama provider will be disabled.",
            exc,
        )
        return None


def _get_hf_embeddings_class():
    """Load HuggingFaceEmbeddings lazily for last-resort embedding fallback only."""
    global HuggingFaceEmbeddings, _HF_EMBEDDINGS_IMPORT_ERROR
    if HuggingFaceEmbeddings is not None:
        return HuggingFaceEmbeddings
    if _HF_EMBEDDINGS_IMPORT_ERROR is not None:
        return None
    try:
        from langchain_huggingface import HuggingFaceEmbeddings as _HuggingFaceEmbeddings

        HuggingFaceEmbeddings = _HuggingFaceEmbeddings
        return HuggingFaceEmbeddings
    except Exception as exc:
        _HF_EMBEDDINGS_IMPORT_ERROR = exc
        logger.warning(
            "langchain_huggingface unavailable (%s). "
            "HuggingFace embedding fallback will be disabled.",
            exc,
        )
        return None


# --- Initialize FastAPI App ---
app = FastAPI()

# --- Add CORS Middleware ---
# Allow callers to restrict origins via env var.  Defaults to wildcard so
# existing local-dev and gateway-proxied deployments are unaffected.
# On Render the gateway enforces CORS; the agent ALLOWED_ORIGINS env var
# provides an extra defense-in-depth layer (set to gateway hostname).
_AGENT_ALLOWED_ORIGINS_RAW = os.environ.get("ALLOWED_ORIGINS", "*")
_AGENT_ALLOWED_ORIGINS: list[str] = (
    ["*"]
    if _AGENT_ALLOWED_ORIGINS_RAW.strip() == "*"
    else [o.strip() for o in _AGENT_ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
)
_AGENT_ALLOWED_ORIGIN_REGEX: str | None = os.environ.get("ALLOWED_ORIGIN_REGEX", "").strip() or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=_AGENT_ALLOWED_ORIGINS,
    allow_origin_regex=_AGENT_ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static files mount removed - using separate React frontend ---


# --- Load Environment Variables & Validate ---
# Import normalized endpoints from central config (ensures consistency across services).
from src.config import (
    EMBEDDING_SERVICE_URL,
    OLLAMA_BASE_URL,
    _normalize_internal_service_url,
    _running_on_render,
)

# Keep these helpers bound on this module for legacy imports and tests.
_RENDER_URL_HELPERS = (_normalize_internal_service_url, _running_on_render)


supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = (
    os.environ.get("SUPABASE_SECRET_KEY")
    or os.environ.get("SUPABASE_KEY")
    or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
)
# Use normalized OLLAMA_BASE_URL from config (handles Render vs local-dev)
ollama_base_url = OLLAMA_BASE_URL
ollama_api_key = (
    os.environ.get("OLLAMA_API_KEY")
    or os.environ.get("MODAL_API_PROXY_SECRET")
    or os.environ.get("MODAL_API_PROXY_KEY")
    or os.environ.get("MODAL_API_KEY")
    or os.environ.get("MODAL_TOKEN_SECRET")
    or os.environ.get("MODAL_API_TOKEN_SECRET")
)
modal_proxy_key = (
    os.environ.get("MODAL_API_PROXY_KEY")
    or os.environ.get("MODAL_API_KEY")
    or os.environ.get("MODAL_API_TOKEN_ID")
    or os.environ.get("MODAL_TOKEN_ID")
)
modal_proxy_secret = os.environ.get("MODAL_API_PROXY_SECRET") or os.environ.get(
    "MODAL_TOKEN_SECRET"
)
proxy_auth_token = (
    os.environ.get("PROXY_AUTH_TOKEN")
    or os.environ.get("MODAL_PROXY_AUTH_TOKEN")
    or os.environ.get("X_PROXY_TOKEN")
)
ollama_model = os.environ.get("OLLAMA_MODEL") or "llama3.1:8b"
default_provider = "ollama"
default_model = os.environ.get("DEFAULT_MODEL") or None
force_local_modal_llm = (os.environ.get("FORCE_LOCAL_MODAL_LLM") or "true").lower() in [
    "1",
    "true",
    "yes",
]
lock_model_selection_env = (os.environ.get("LOCK_MODEL_SELECTION") or "false").lower() in [
    "1",
    "true",
    "yes",
]
enforce_proxy_llm = (os.environ.get("AGENT_ENFORCE_PROXY") or "true").lower() in [
    "1",
    "true",
    "yes",
]
selection_file_path = os.environ.get("MODEL_SELECTION_PATH") or str(
    Path(__file__).parent / "data" / "model_selection.json"
)
agent_fast_mode = (os.environ.get("AGENT_FAST_MODE") or "true").lower() in ["1", "true", "yes"]
agent_max_response_sentences = max(1, int(os.environ.get("AGENT_MAX_RESPONSE_SENTENCES") or "4"))
agent_max_response_chars = max(120, int(os.environ.get("AGENT_MAX_RESPONSE_CHARS") or "700"))
llm_manager_kwargs: dict[str, Any] = {
    "base_url": ollama_base_url,
    "default_model": ollama_model,
    "api_key": ollama_api_key,
    "modal_proxy_key": modal_proxy_key,
    "modal_proxy_secret": modal_proxy_secret,
    "proxy_auth_token": proxy_auth_token,
    "selection_file_path": selection_file_path,
    "locked": lock_model_selection_env,
    "use_native_api": force_local_modal_llm,
    "enforce_proxy": enforce_proxy_llm,
}
if "enforce_proxy" not in inspect.signature(LocalLLMClientManager.__init__).parameters:
    logger.warning(
        "LocalLLMClientManager does not accept enforce_proxy; falling back to legacy constructor"
    )
    llm_manager_kwargs.pop("enforce_proxy", None)
llm_client_manager = LocalLLMClientManager(**llm_manager_kwargs)
# --- Initialize Clients ---
try:
    supabase: Client | None = None
    if supabase_url and supabase_key:
        logger.info("Initializing optional Supabase client (auth/diagnostics only)...")
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    else:
        logger.info(
            "Supabase client not configured for agent runtime; continuing with Chroma-backed retrieval"
        )

    chroma_store = get_chroma_store()
    if chroma_store.heartbeat():
        logger.info("Chroma store connectivity check passed")
    else:
        logger.warning(
            "Chroma store heartbeat failed at startup; retrieval will retry during requests"
        )

    class Selection(TypedDict):
        provider: str
        model: str | None
        locked: bool

    CURRENT_SELECTION: Selection = llm_client_manager.get_selection()

    def _save_model_selection_to_file(provider: str, model: str | None, locked: bool | None = None):
        llm_client_manager.save_selection(provider, model, locked)

    def _available_providers() -> list[str]:
        return ["ollama"] if ollama_base_url else []

    def _normalize_provider_name(provider_name: str | None) -> str:
        return llm_client_manager.normalize_provider(provider_name)

    def _default_model_for_provider(_provider_name: str) -> str | None:
        return llm_client_manager.current_model()

    def _use_modal_native_chat_api(base_url: str | None = None) -> bool:
        candidate_url = (base_url or llm_client_manager.base_url or "").strip()
        return bool(force_local_modal_llm and candidate_url and "modal.run" in candidate_url)

    def _validate_or_resolve_selection() -> None:
        llm_client_manager.validate_selection()

    _validate_or_resolve_selection()
    llm_client_manager.validate_runtime()

    # Use dedicated embedding service and optionally fail fast if unavailable
    logger.info("Initializing embedding model (Embedding Service, fail-fast)...")
    # Use normalized EMBEDDING_SERVICE_URL from config (handles Render vs local-dev)
    embedding_service_url = EMBEDDING_SERVICE_URL
    embedding_service_auth_token = (
        os.environ.get("EMBEDDING_SERVICE_AUTH_TOKEN")
        or os.environ.get("MODAL_API_PROXY_SECRET")
        or os.environ.get("MODAL_API_KEY")
        or os.environ.get("MODAL_TOKEN_SECRET")
        or os.environ.get("MODAL_API_TOKEN_SECRET")
    )
    embedding_strict_startup = os.environ.get("EMBEDDING_STRICT_STARTUP", "false").lower() in [
        "1",
        "true",
        "yes",
    ]

    try:
        from src.embedding_service.client import create_embedding_client

        embedding_model = create_embedding_client(
            embedding_service_url,
            validate_on_init=True,
            auth_token=embedding_service_auth_token,
        )
        active_embedding_url = getattr(embedding_model, "base_url", embedding_service_url)
        logger.info(
            "✅ Embedding model initialized via Embedding Service (%s)",
            active_embedding_url,
        )
    except Exception as service_exc:
        if embedding_strict_startup:
            raise RuntimeError(
                "Embedding service validation failed. "
                "Set EMBEDDING_SERVICE_URL to a reachable service and ensure /health is up. "
                "For local dev: `uv run uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001`. "
                "For Cloud Run deploy via gcloud CLI: `backend/scripts/deploy_embedding_gcloud.sh` "
                "with PROJECT_ID and REGION configured. "
                f"Original error: {service_exc}"
            ) from service_exc

        logger.warning(
            "Embedding service unavailable at startup; falling back to local FastEmbedEmbeddings. "
            "Set EMBEDDING_STRICT_STARTUP=true to fail fast. Original error: %s",
            service_exc,
        )
        try:
            if FastEmbedEmbeddings is None:
                try:
                    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings as _FBE

                    FastEmbedEmbeddings = _FBE
                except Exception:
                    FastEmbedEmbeddings = None

            if FastEmbedEmbeddings is None:
                raise ImportError("langchain_community is not installed")
            embedding_model = FastEmbedEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        except Exception as fastembed_exc:
            logger.warning(
                "FastEmbedEmbeddings fallback unavailable: %s. Trying HuggingFaceEmbeddings fallback.",
                fastembed_exc,
            )
            HuggingFaceEmbeddingsClass = _get_hf_embeddings_class()
            if HuggingFaceEmbeddingsClass is not None:
                try:
                    embedding_model = HuggingFaceEmbeddingsClass(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                except Exception as hf_exc:
                    logger.warning(
                        "HuggingFaceEmbeddings initialization failed: %s. Using zero-vector fallback embeddings.",
                        hf_exc,
                    )

                    class _ZeroVectorEmbeddings:
                        def embed_query(self, _text: str) -> list[float]:
                            return [0.0] * 384

                        def embed_documents(self, texts: list[str]) -> list[list[float]]:
                            return [[0.0] * 384 for _ in texts]

                    embedding_model = _ZeroVectorEmbeddings()  # type: ignore[assignment]
            else:
                logger.warning(
                    "HuggingFaceEmbeddings fallback unavailable: %s. Using zero-vector fallback embeddings.",
                    _HF_EMBEDDINGS_IMPORT_ERROR,
                )

                embedding_model = _ZeroVectorEmbeddings()  # type: ignore[assignment]
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    logger.error(traceback.format_exc())
    raise RuntimeError(f"Failed to initialize clients: {e}") from e


def _is_truthy_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _probe_guardrails_loaded() -> tuple[bool, str]:
    """Eager-load guardrails so first user request does not pay setup latency."""
    try:
        from src.agent.guardrails_config import _get_hub_guards  # type: ignore[attr-defined]

        require_hub_validator = _is_truthy_env("GUARDRAILS_REQUIRE_HUB_VALIDATOR", False)
        input_guard, _ = _get_hub_guards()
        if input_guard is None:
            if require_hub_validator:
                return False, "hub_validator_required_but_unavailable"
            return True, "local_fallback"
        return True, "hub_validator_ready"
    except Exception as exc:
        logger.warning("Guardrails preload failed: %s", exc)
        return False, f"error: {exc}"


def _probe_chroma_connectivity() -> tuple[bool, str]:
    try:
        healthy = bool(chroma_store.heartbeat())
        return (healthy, "ok" if healthy else "heartbeat_failed")
    except Exception as exc:
        return False, f"error: {exc}"


def _probe_supabase_connectivity() -> tuple[bool, str]:
    if supabase is None:
        return False, "supabase_not_configured"
    try:
        # Lightweight connectivity probe for configured data backend.
        supabase.table("document_chunks").select("id").limit(1).execute()
        return True, "ok"
    except Exception as exc:
        return False, f"error: {exc}"


def _probe_postgres_connectivity() -> tuple[bool, str]:
    if psycopg2 is None:
        return False, "psycopg2_not_available"

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        return False, "database_url_not_configured"

    try:
        conn = psycopg2.connect(database_url, connect_timeout=3)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        finally:
            conn.close()
        return True, "ok"
    except Exception as exc:
        return False, f"error: {exc}"


def _run_startup_preflight() -> dict[str, Any]:
    from src.config import resolve_data_db_mode

    data_mode = resolve_data_db_mode()

    checks: dict[str, dict[str, Any]] = {}

    require_guardrails_hub = _is_truthy_env("GUARDRAILS_REQUIRE_HUB_VALIDATOR", False)
    require_chroma = _is_truthy_env("CHROMA_REQUIRED", False)

    guardrails_ok, guardrails_detail = _probe_guardrails_loaded()
    checks["guardrails"] = {
        "ok": guardrails_ok,
        "detail": guardrails_detail,
        "required": require_guardrails_hub,
    }

    chroma_ok, chroma_detail = _probe_chroma_connectivity()
    checks["chroma"] = {
        "ok": chroma_ok,
        "detail": chroma_detail,
        "required": require_chroma,
    }

    if data_mode == "postgres":
        data_ok, data_detail = _probe_postgres_connectivity()
        checks["data_backend"] = {
            "ok": data_ok,
            "backend": "postgres",
            "detail": data_detail,
            "required": True,
        }
    else:
        data_ok, data_detail = _probe_supabase_connectivity()
        checks["data_backend"] = {
            "ok": data_ok,
            "backend": "supabase",
            "detail": data_detail,
            "required": True,
        }

    overall_ok = all(
        bool(item.get("ok")) for item in checks.values() if bool(item.get("required", False))
    )
    return {
        "status": "ok" if overall_ok else "degraded",
        "data_mode": data_mode,
        "checks": checks,
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }


@app.on_event("startup")
async def startup_preflight() -> None:
    if not _is_truthy_env("BACKEND_PREFLIGHT_ENABLED", True):
        app.state.preflight = {
            "status": "skipped",
            "reason": "disabled_by_env",
            "ran_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Startup preflight skipped (BACKEND_PREFLIGHT_ENABLED=false)")
        return

    preflight = _run_startup_preflight()
    app.state.preflight = preflight

    logger.info(
        "Startup preflight completed status=%s data_mode=%s checks=%s",
        preflight.get("status"),
        preflight.get("data_mode"),
        preflight.get("checks"),
    )

    if preflight.get("status") != "ok" and _is_truthy_env("BACKEND_PREFLIGHT_STRICT", False):
        raise RuntimeError("Startup preflight failed in strict mode")


# --- Location Context Configuration ---
# This can be customized per deployment or organization
LOCATION_CONTEXT = {
    "organization": "Woonasquatucket River Watershed Council",
    "location": "Providence, Rhode Island",
    "address": "45 Eagle Street, Suite 202, Providence, RI 02909",
    "region": "Rhode Island",
    "service_area": "Woonasquatucket River Watershed",
    "focus_areas": [
        "Water quality and watershed protection",
        "Community environmental education",
        "Habitat restoration",
        "Community health and wellbeing in Rhode Island",
    ],
}

# --- Define LangGraph State ---


class AgentState(TypedDict, total=False):
    """State for the Vecinita agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    question: str
    language: str
    provider: str | None
    model: str | None
    fast_mode: bool | None
    plan: str | None  # Stores planning results
    grade_result: str | None


# --- Human-readable agent thinking messages ---
AGENT_THINKING_MESSAGES = {
    "es": {
        "static_response": "Verificando si ya conozco esto...",
        "db_search": "Revisando nuestros recursos locales...",
        "clarify_question": "Necesito un poco más de información...",
        "web_search": "Buscando información adicional...",
        "plan": "Déjame pensar en tu pregunta...",
        "analyzing": "Entendiendo tu pregunta...",
        "searching": "Encontrando información relevante...",
    },
    "en": {
        "static_response": "Checking if I already know this...",
        "db_search": "Looking through our local resources...",
        "clarify_question": "I need a bit more information...",
        "web_search": "Searching for additional information...",
        "plan": "Let me think about your question...",
        "analyzing": "Understanding your question...",
        "searching": "Finding relevant information...",
    },
}


def get_agent_thinking_message(tool_name: str, language: str) -> str:
    """Get human-readable conversational message for agent activity."""
    msgs = AGENT_THINKING_MESSAGES.get(language, AGENT_THINKING_MESSAGES["en"])
    return msgs.get(tool_name, "Pensando..." if language == "es" else "Thinking...")


def _summarize_tool_result(tool_name: str, content: str, language: str) -> str:
    """Return compact user-visible summary for tool results."""
    safe_content = content if isinstance(content, str) else str(content)
    lang = "es" if language == "es" else "en"

    if tool_name == "db_search":
        try:
            docs = json.loads(safe_content)
            if isinstance(docs, list):
                if lang == "es":
                    return f"db_search devolvió {len(docs)} fragmentos relevantes."
                return f"db_search returned {len(docs)} relevant chunks."
        except Exception:
            pass
    if tool_name == "web_search":
        try:
            links = json.loads(safe_content)
            if isinstance(links, list):
                if lang == "es":
                    return f"web_search devolvió {len(links)} resultados web."
                return f"web_search returned {len(links)} web results."
        except Exception:
            pass
    if tool_name == "clarify_question":
        return (
            "Se requieren aclaraciones del usuario."
            if lang == "es"
            else "User clarification is required."
        )

    return "Herramienta completada." if lang == "es" else "Tool call completed."


def _db_unavailable_message(language: str) -> str:
    if language == "es":
        return (
            "No puedo acceder temporalmente a la base de datos de documentos de Vecinita. "
            "Inténtalo nuevamente en unos minutos mientras restablecemos la conexión."
        )
    return (
        "I can’t access the Vecinita document database right now. "
        "Please try again in a few minutes while the connection is restored."
    )


def _weak_retrieval_warning(language: str) -> str:
    if language == "es":
        return (
            "⚠️ No encontré suficientes coincidencias sólidas en la base local. "
            "La siguiente respuesta es de mejor esfuerzo y puede ser incompleta."
        )
    return (
        "⚠️ I did not find strong matches in the local knowledge base. "
        "The following answer is best-effort and may be incomplete."
    )


def _normalize_suggested_questions(
    candidates: list[str] | tuple[str, ...] | None,
    *,
    max_items: int = 3,
) -> list[str]:
    if not candidates:
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        if not isinstance(candidate, str):
            continue

        cleaned = " ".join(candidate.strip().split())
        if not cleaned:
            continue

        if len(cleaned) > 140:
            cleaned = cleaned[:139].rstrip()

        if not cleaned.endswith("?"):
            cleaned = f"{cleaned}?"

        key = cleaned.casefold()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(cleaned)
        if len(normalized) >= max_items:
            break

    return normalized


def _build_follow_up_suggestions(
    *,
    question: str,
    answer: str,
    language: str,
    sources: list[dict] | None = None,
) -> list[str]:
    del answer

    first_source_title = ""
    if sources:
        for source in sources:
            if isinstance(source, dict):
                title = str(source.get("title") or "").strip()
                if title:
                    first_source_title = title
                    break

    if language == "es":
        candidates = [
            "¿Puedes resumir esto en 3 puntos clave",
            "¿Qué debería hacer primero",
            "¿Qué recursos locales están más relacionados con esta respuesta",
        ]
        if first_source_title:
            candidates.insert(0, f"¿Qué dice la fuente '{first_source_title}'")
        if question.strip():
            candidates.append("¿Cómo cambia esto según mi situación")
    else:
        candidates = [
            "Can you summarize this in 3 key points",
            "What should I do first",
            "Which local resources are most relevant to this answer",
        ]
        if first_source_title:
            candidates.insert(0, f"What does the source '{first_source_title}' say")
        if question.strip():
            candidates.append("How does this change for my specific situation")

    return _normalize_suggested_questions(candidates)


def _is_contextual_follow_up(question: str, language: str) -> bool:
    text = " ".join((question or "").strip().lower().split())
    if not text:
        return False

    if language == "es":
        patterns = (
            "resume esto",
            "resumir esto",
            "3 puntos clave",
            "que deberia hacer primero",
            "que debería hacer primero",
            "esta respuesta",
        )
    else:
        patterns = (
            "summarize this",
            "summarise this",
            "3 key points",
            "what should i do first",
            "this answer",
            "this in 3",
        )

    return any(pattern in text for pattern in patterns)


def _build_contextual_follow_up_answer(
    *,
    question: str,
    prior_answer: str,
    language: str,
    provider: str | None,
    model: str | None,
) -> str:
    context_text = (prior_answer or "").strip()
    if not context_text:
        if language == "es":
            return "No tengo suficiente contexto previo para resumir."
        return "I do not have enough prior context to summarize yet."

    if language == "es":
        prompt = (
            "Responde SOLO usando el contexto provisto de la respuesta previa. "
            "No agregues hechos nuevos ni enlaces nuevos. "
            "Si piden resumen, devuelve 3 puntos clave breves en viñetas. "
            "Si piden primeros pasos, da pasos concretos basados en ese contexto.\n\n"
            f"Solicitud del usuario: {question}\n\n"
            f"Contexto previo:\n{context_text}"
        )
    else:
        prompt = (
            "Answer ONLY from the provided prior-answer context. "
            "Do not add new facts or links. "
            "If asked to summarize, return 3 concise key bullet points. "
            "If asked what to do first, provide practical first steps based on that context.\n\n"
            f"User request: {question}\n\n"
            f"Prior context:\n{context_text}"
        )

    try:
        llm = _get_llm_without_tools(provider, model)
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content if hasattr(response, "content") else str(response)
        cleaned = str(answer or "").strip()
        if cleaned:
            return cleaned
    except Exception as exc:
        logger.warning("Contextual follow-up generation failed: %s", exc)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", context_text) if s.strip()]
    top = sentences[:3] if sentences else [context_text]
    if language == "es":
        return "\n".join(f"- {item}" for item in top)
    return "\n".join(f"- {item}" for item in top)


def _is_answer_seeking_query(question: str, language: str) -> bool:
    text = (question or "").strip().lower()
    if not text:
        return False

    non_answer_intents_en = {
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "cool",
        "bye",
        "goodbye",
    }
    non_answer_intents_es = {
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "gracias",
        "ok",
        "vale",
        "adios",
        "chao",
        "chau",
    }

    compact = " ".join(text.split())
    if language == "es":
        if compact in non_answer_intents_es:
            return False
    else:
        if compact in non_answer_intents_en:
            return False

    question_markers = (
        "?",
        "¿",
        "what",
        "how",
        "when",
        "where",
        "why",
        "which",
        "who",
        "can you",
        "help",
    )
    if any(marker in compact for marker in question_markers):
        return True

    return len(compact.split()) > 4


def _parse_db_search_docs(raw_content: str) -> list[dict]:
    content = raw_content if isinstance(raw_content, str) else str(raw_content)
    content = content.strip()
    if not content or not content.startswith("["):
        return []
    try:
        parsed = json.loads(content)
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _is_weak_retrieval(docs: list[dict]) -> bool:
    if not docs:
        return True
    similarities = [float(doc.get("similarity", 0.0) or 0.0) for doc in docs]
    if not similarities:
        return True
    return max(similarities) < 0.2


def _build_sources_from_docs(docs: list[dict]) -> list[dict]:
    sources: list[dict] = []
    seen_urls = set()

    for d in docs[:5]:
        url = d.get("source_url") or ""
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        content_text = d.get("content", "")
        clean_title = None

        if content_text.startswith("DOCUMENTS_LOADED:"):
            lines = content_text.split("\n", 2)
            if len(lines) >= 2:
                for line in lines[1:]:
                    stripped = line.strip()
                    if stripped and len(stripped) > 3:
                        clean_title = stripped[:100] + ("..." if len(stripped) > 100 else "")
                        break

        if not clean_title and content_text:
            first_line = content_text.split("\n")[0].strip()
            if first_line and len(first_line) > 3:
                clean_title = first_line[:100] + ("..." if len(first_line) > 100 else "")

        if not clean_title:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                path_parts = parsed.path.rstrip("/").split("/")
                if path_parts and path_parts[-1]:
                    clean_title = path_parts[-1]
                else:
                    clean_title = parsed.netloc or url.split("/")[-1] or "Internal Document"
            except Exception:
                clean_title = url.split("/")[-1] or "Internal Document"

        entry = {
            "title": clean_title,
            "url": url,
            "type": "document",
        }
        lower = url.lower()
        entry["isDownload"] = any(
            lower.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"]
        )
        if "chunk_index" in d:
            entry["chunkIndex"] = d["chunk_index"]
        if "char_start" in d:
            entry["charStart"] = d["char_start"]
        if "char_end" in d:
            entry["charEnd"] = d["char_end"]
        if "doc_index" in d:
            entry["docIndex"] = d["doc_index"]
        if "total_chunks" in d:
            entry["totalChunks"] = d["total_chunks"]
        if "metadata" in d and d["metadata"]:
            entry["metadata"] = d["metadata"]
        sources.append(entry)

    return sources


def _allowed_source_urls_from_docs(docs: list[dict]) -> set[str]:
    allowed: set[str] = set()
    for doc in docs:
        source_url = str(doc.get("source_url") or "").strip()
        if source_url.startswith("http://") or source_url.startswith("https://"):
            allowed.add(source_url)
    return allowed


def _sanitize_answer_links(answer: str, allowed_urls: set[str], language: str) -> str:
    if not answer:
        return answer

    url_pattern = re.compile(r"https?://[^\s)\]\[\"'<>]+")
    replacement = (
        "[enlace no verificado eliminado]" if language == "es" else "[unverified link removed]"
    )

    def _replace(match: re.Match[str]) -> str:
        raw_url = match.group(0)
        normalized = raw_url.rstrip('.,;:!?)"]')
        return raw_url if normalized in allowed_urls else replacement

    return url_pattern.sub(_replace, answer)


def _build_deterministic_rag_answer(
    *,
    question: str,
    language: str,
    provider: str | None,
    model: str | None,
    retrieved_docs: list[dict],
    weak_retrieval: bool,
) -> str:
    context_blocks = []
    for index, doc in enumerate(retrieved_docs[:5], start=1):
        source = doc.get("source_url") or "Internal Document"
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        context_blocks.append(f"[{index}] Source: {source}\n{content}")
    context_text = "\n\n".join(context_blocks) if context_blocks else ""

    if language == "es":
        if context_text:
            prompt = (
                "Responde usando principalmente el contexto recuperado de la base vectorial local. "
                "Si el contexto no alcanza para una parte, dilo claramente. "
                "Nunca inventes enlaces. Solo usa URLs que aparecen textualmente en el contexto recuperado. "
                "Incluye citas en formato (Fuente: URL) cuando uses el contexto.\n\n"
                f"Pregunta: {question}\n\n"
                f"Contexto recuperado:\n{context_text}"
            )
        else:
            prompt = (
                "No se recuperó contexto útil de la base local. "
                "Da una respuesta cautelosa y explícitamente limitada. "
                "No afirmes certeza cuando no la tengas.\n\n"
                f"Pregunta: {question}"
            )
    else:
        if context_text:
            prompt = (
                "Answer primarily using the retrieved local vector database context. "
                "If context is insufficient for any part, state that explicitly. "
                "Never invent links. Only use URLs that appear verbatim in the retrieved context. "
                "Include citations in the format (Source: URL) when using context.\n\n"
                f"Question: {question}\n\n"
                f"Retrieved context:\n{context_text}"
            )
        else:
            prompt = (
                "No useful context was retrieved from the local knowledge base. "
                "Provide a cautious, explicitly limited best-effort response. "
                "Do not imply certainty where none exists.\n\n"
                f"Question: {question}"
            )

    try:
        llm = _get_llm_without_tools(provider, model)
        response = llm.invoke([HumanMessage(content=prompt)])
        answer = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.warning(
            "Deterministic generation fallback activated due to model error: %s | provider=%s model=%s base_url=%s via_proxy=%s uses_native_api=%s",
            exc,
            provider,
            model,
            llm_client_manager.base_url,
            llm_client_manager._via_proxy(),
            llm_client_manager.uses_modal_native_chat_api(),
        )
        if language == "es":
            if retrieved_docs:
                source = retrieved_docs[0].get("source_url") or "Documento interno"
                snippet = (retrieved_docs[0].get("content") or "").strip()[:260]
                answer = (
                    "No pude consultar el modelo de lenguaje en este momento. "
                    "Comparto un resumen de mejor esfuerzo basado en el contenido recuperado:\n\n"
                    f"{snippet}\n\n(Fuente: {source})"
                )
            else:
                answer = (
                    "No pude consultar el modelo de lenguaje y no se recuperó contexto suficiente. "
                    "Intenta reformular la pregunta o vuelve a intentar en unos minutos."
                )
        else:
            if retrieved_docs:
                source = retrieved_docs[0].get("source_url") or "Internal Document"
                snippet = (retrieved_docs[0].get("content") or "").strip()[:260]
                answer = (
                    "I could not reach the language model right now. "
                    "Here is a best-effort summary from retrieved context:\n\n"
                    f"{snippet}\n\n(Source: {source})"
                )
            else:
                answer = (
                    "I could not reach the language model and insufficient context was retrieved. "
                    "Please rephrase your question or try again in a few minutes."
                )

    if weak_retrieval:
        return f"{_weak_retrieval_warning(language)}\n\n{answer}"
    return answer


def _build_clarification_payload(content: str, language: str) -> dict:
    """Parse clarify_question tool content into a structured clarification event payload."""
    safe_content = content if isinstance(content, str) else str(content)
    lines = [line.strip() for line in safe_content.splitlines() if line.strip()]

    questions: list[str] = []
    for line in lines:
        normalized = line
        for prefix in ("1.", "2.", "3.", "4.", "5.", "-", "•"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :].strip()
        if normalized.endswith("?") and len(normalized) > 8:
            questions.append(normalized)

    if not questions:
        if language == "es":
            questions = ["¿Podrías compartir más detalles para que pueda ayudarte mejor?"]
        else:
            questions = ["Could you share more details so I can help you better?"]

    if language == "es":
        message = "Necesito más información para continuar."
        context = "Se requiere intervención del usuario."
    else:
        message = "I need more details to continue."
        context = "User intervention is required."

    return {
        "type": "clarification",
        "message": message,
        "questions": questions[:3],
        "context": context,
        "waiting": True,
        "stage": "clarification",
        "progress": 85,
        "status": "waiting",
    }


# --- Initialize Tools ---
logger.info("Initializing agent tools...")
# Use lower threshold (0.1) for better recall - can be tuned based on results
db_search_tool = create_db_search_tool(
    chroma_store, embedding_model, match_threshold=0.1, match_count=5
)
web_search_tool = create_web_search_tool()
clarify_question_tool = create_clarify_question_tool()
static_response_tool = create_static_response_tool()
rank_retrieval_results_tool = create_rank_retrieval_tool()
rewrite_question_tool = create_rewrite_question_tool(
    lambda provider, model: _get_llm_without_tools(provider, model)
)
tools = [
    db_search_tool,
    static_response_tool,
    clarify_question_tool,
    web_search_tool,
    rank_retrieval_results_tool,
    rewrite_question_tool,
]
# Filter out None values if any tool failed to initialize
tools = [t for t in tools if t is not None]
logger.info(f"Initialized {len(tools)} tools: {[tool.name for tool in tools]}")


def _resolve_effective_provider_model(
    provider: str | None,
    model: str | None,
) -> tuple[str | None, str | None]:
    """Resolve provider/model against the local-only selection manager."""
    resolved_provider, resolved_model = llm_client_manager.resolve_request(provider, model)
    return resolved_provider, resolved_model


def _get_llm_with_tools(provider: str | None, model: str | None):
    return llm_client_manager.build_client(
        provider=provider,
        model=model,
        temperature=0,
        tools=tools,
    )


def _get_llm_without_tools(provider: str | None, model: str | None):
    return llm_client_manager.build_client(
        provider=provider,
        model=model,
        temperature=0,
    )


def _normalize_provider_name_runtime(provider_name: str | None) -> str:
    return llm_client_manager.normalize_provider(provider_name)


def _is_transport_connection_error(exc: Exception) -> bool:
    err_name = exc.__class__.__name__.lower()
    text = str(exc).lower()
    return (
        "connecterror" in err_name
        or "connectionerror" in err_name
        or "apiconnectionerror" in err_name
        or "connection refused" in text
        or "failed to establish" in text
        or "temporary failure in name resolution" in text
        or "network is unreachable" in text
    )


def _provider_candidates_for_request(
    provider: str | None, model: str | None
) -> list[tuple[str | None, str | None]]:
    resolved_provider, resolved_model = llm_client_manager.resolve_request(provider, model)
    return [(resolved_provider, resolved_model)]


def _sanitize_messages(messages: list[BaseMessage]) -> list[BaseMessage]:  # noqa: C901
    """Sanitize messages to ensure all content fields are strings.

    Some chat APIs require message content to be strings,
    but LangChain's ToolNode can produce messages with list content.
    This function converts any non-string content to a string.
    """
    sanitized: list[BaseMessage] = []
    valid_tool_call_ids: set[str] = set()
    for msg in messages:
        # Make a copy of the message to avoid modifying the original
        if isinstance(msg, AIMessage):
            tool_calls = getattr(msg, "tool_calls", None) or []
            for call in tool_calls:
                if isinstance(call, dict):
                    call_id = call.get("id")
                else:
                    call_id = getattr(call, "id", None)
                if call_id:
                    valid_tool_call_ids.add(str(call_id))

        if isinstance(msg, ToolMessage):
            tool_call_id = str(msg.tool_call_id) if msg.tool_call_id is not None else ""
            if not tool_call_id or tool_call_id not in valid_tool_call_ids:
                logger.debug(
                    "Dropping orphan ToolMessage with tool_call_id=%s name=%s",
                    tool_call_id,
                    getattr(msg, "name", None),
                )
                continue

            # ToolMessage content can be a list; convert to string
            content = msg.content
            if isinstance(content, list):
                # Convert list to JSON string
                content = json.dumps(content, ensure_ascii=False)
            # Create new ToolMessage with string content
            sanitized.append(
                ToolMessage(
                    content=content,
                    tool_call_id=msg.tool_call_id,
                    name=msg.name if hasattr(msg, "name") else None,
                )
            )
        else:
            # For other message types, ensure content is string
            content = msg.content
            if not isinstance(content, str):
                if isinstance(content, list):
                    content = json.dumps(content, ensure_ascii=False)
                else:
                    content = str(content)
            # Create a new message with the same type but sanitized content
            msg_dict = msg.dict()
            msg_dict["content"] = content
            sanitized.append(msg.__class__(**msg_dict))
    return sanitized


# --- Define Agent Node ---


def agent_node(state: AgentState) -> AgentState:
    """Agent node that calls the LLM with tool binding."""
    logger.info("Agent node: Processing messages...")

    # Log the current conversation state for debugging
    last_message = state["messages"][-1]
    if hasattr(last_message, "content"):
        logger.debug(
            f"Last message content: {last_message.content[:200] if isinstance(last_message.content, str) else last_message.content}"
        )

    # Sanitize messages to ensure all content is strings for chat-client compatibility
    sanitized_messages = _sanitize_messages(state["messages"])

    # Retry on transient rate-limit / 429 errors and fail over provider on transport errors.
    import re as _re

    last_exc: Exception | None = None
    provider_candidates = _provider_candidates_for_request(
        state.get("provider"), state.get("model")
    )

    for provider_candidate, model_candidate in provider_candidates:
        logger.info(
            "Agent node: Attempting provider='%s' model='%s'",
            provider_candidate,
            model_candidate,
        )

        llm_with_tools = _get_llm_with_tools(provider_candidate, model_candidate)

        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                response = llm_with_tools.invoke(sanitized_messages)
                return {"messages": [response]}
            except Exception as e:
                last_exc = e
                err_name = e.__class__.__name__
                is_rate_limit = err_name in (
                    "RateLimitError",
                    "TooManyRequests",
                    "RateLimitException",
                )
                if is_rate_limit:
                    wait_seconds = 5.0
                    m = _re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", str(e))
                    if m:
                        try:
                            wait_seconds = float(m.group(1))
                        except Exception:
                            pass
                    logger.warning(
                        "Rate limit hit (%s). Waiting %.2fs before retry (%s/%s).",
                        err_name,
                        wait_seconds,
                        attempts + 1,
                        max_attempts,
                    )
                    time.sleep(wait_seconds)
                    attempts += 1
                    continue

                if _is_transport_connection_error(e):
                    normalized_provider = _normalize_provider_name_runtime(provider_candidate)
                    if normalized_provider:
                        _RUNTIME_PROVIDER_BLOCKLIST.add(normalized_provider)
                    logger.warning(
                        "Provider '%s' failed with transport error: %s. Trying next provider if available.",
                        provider_candidate,
                        e,
                    )
                    break

                raise

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("All LLM provider candidates exhausted without result")


def classify_query_complexity(state: AgentState) -> str:
    """Classify if query needs planning or can go straight to agent using LLM.

    Uses the LLM to intelligently determine query complexity.

    Returns:
        - "simple" for straightforward questions that don't need planning
        - "complex" for questions requiring planning and multi-step reasoning
    """
    question = state["question"]
    language = state["language"]

    if state.get("fast_mode", agent_fast_mode):
        logger.info("Fast mode enabled: skipping complexity classification and routing as SIMPLE")
        return "simple"

    # Create classification prompt
    if language == "es":
        classification_prompt = f"""Analiza esta pregunta y clasifícala como SIMPLE o COMPLEJA.

SIMPLE: Preguntas directas, saludos, definiciones básicas, preguntas de una sola respuesta.
Ejemplos: "Hola", "¿Qué es SNAP?", "¿Quién eres?", "Gracias"

COMPLEJA: Comparaciones, instrucciones paso a paso, múltiples partes, análisis profundo, listas exhaustivas.
Ejemplos: "Compara programas de vivienda", "Explica cómo aplicar paso a paso", "Lista todos los recursos"

Pregunta: "{question}"

Responde SOLO con: SIMPLE o COMPLEJA"""
    else:
        classification_prompt = f"""Analyze this question and classify it as SIMPLE or COMPLEX.

SIMPLE: Direct questions, greetings, basic definitions, single-answer questions.
Examples: "Hello", "What is SNAP?", "Who are you?", "Thanks"

COMPLEX: Comparisons, step-by-step instructions, multi-part questions, deep analysis, exhaustive lists.
Examples: "Compare housing programs", "Explain how to apply step by step", "List all resources"

Question: "{question}"

Respond with ONLY: SIMPLE or COMPLEX"""

    try:
        # Use LLM without tools for classification
        llm = _get_llm_without_tools(state.get("provider"), state.get("model"))

        # Get classification from LLM (without tools)
        response = llm.invoke([HumanMessage(content=classification_prompt)])
        classification = response.content.strip().upper()

        # Parse response
        if "SIMPLE" in classification:
            logger.info(f"Query classified as SIMPLE by LLM: '{question}'")
            return "simple"
        elif "COMPLEX" in classification or "COMPLEJA" in classification:
            logger.info(f"Query classified as COMPLEX by LLM: '{question}'")
            return "complex"
        else:
            # If LLM response unclear, use word count heuristic
            word_count = len(question.split())
            result = "simple" if word_count < 10 else "complex"
            logger.info(
                f"Query classified as {result.upper()} by fallback heuristic ({word_count} words)"
            )
            return result

    except Exception as e:
        logger.warning(f"LLM classification failed ({e}), using fallback heuristic")
        # Fallback: word count heuristic
        word_count = len(question.split())
        result = "simple" if word_count < 10 else "complex"
        logger.info(f"Query classified as {result.upper()} by fallback ({word_count} words)")
        return result


def planning_node(state: AgentState) -> AgentState:
    """Planning node that analyzes the question and creates a search strategy.

    This node runs before tool execution to:
    1. Analyze the user's question
    2. Identify key concepts and search terms
    3. Plan which tools to use and in what order
    4. Store the plan for reference
    """
    logger.info("Planning node: Analyzing question and creating search strategy...")

    if state.get("fast_mode", agent_fast_mode):
        logger.info("Fast mode enabled: skipping planning node")
        return {"plan": ""}

    llm_without_tools = _get_llm_without_tools(state.get("provider"), state.get("model"))

    question = state["question"]
    language = state["language"]

    # Create planning prompt with location context
    if language == "es":
        planning_prompt = f"""Analiza esta pregunta del usuario y crea un plan de búsqueda específico para {LOCATION_CONTEXT["location"]}.

CONTEXTO: Eres un asistente para {LOCATION_CONTEXT["organization"]} en {LOCATION_CONTEXT["location"]}.
Las áreas de enfoque incluyen: {", ".join(LOCATION_CONTEXT["focus_areas"])}

PREGUNTA: "{question}"

Tu tarea es:
1. Identificar los conceptos clave en la pregunta
2. Determinar si la pregunta es relevante para {LOCATION_CONTEXT["location"]} (Rhode Island)
3. Identificar qué tipo de información se necesita (servicios locales, ubicación específica, etc.)
4. Sugerir qué herramientas usar en qué orden

Responde en este formato:
CONCEPTOS CLAVE: [lista los conceptos principales]
RELEVANCIA LOCAL: [es aplicable a {LOCATION_CONTEXT["location"]}? Sí/No/Parcialmente]
TIPO DE INFORMACIÓN: [qué tipo de información busca el usuario]
PLAN DE BÚSQUEDA: [describe el orden de búsqueda recomendado]
BÚSQUEDA NECESITA CLARIFICACIÓN: [sí/no - ¿necesitamos más detalles del usuario?]
CONTEXTO UBICACIÓN: [si aplica, notas sobre la ubicación específica requerida]
"""
    else:
        planning_prompt = f"""Analyze this user question and create a search plan specific to {LOCATION_CONTEXT["location"]}.

CONTEXT: You are an assistant for {LOCATION_CONTEXT["organization"]} in {LOCATION_CONTEXT["location"]}.
Focus areas include: {", ".join(LOCATION_CONTEXT["focus_areas"])}

QUESTION: "{question}"

Your task is:
1. Identify key concepts in the question
2. Determine if the question is relevant to {LOCATION_CONTEXT["location"]} (Rhode Island)
3. Identify what type of information is needed (local services, specific location, etc.)
4. Suggest which tools to use and in what order

Respond in this format:
KEY CONCEPTS: [list the main concepts]
LOCAL RELEVANCE: [is it applicable to {LOCATION_CONTEXT["location"]}? Yes/No/Partially]
INFORMATION TYPE: [what type of information the user is searching for]
SEARCH PLAN: [describe the recommended search order]
SEARCH NEEDS CLARIFICATION: [yes/no - do we need more details from the user?]
LOCATION CONTEXT: [if applicable, notes about the specific location required]
"""

    # Get planning from LLM
    try:
        planning_response = llm_without_tools.invoke(
            [
                SystemMessage(
                    content=(
                        "You are a search strategy analyst. Analyze questions and create search plans."
                        if language == "en"
                        else "Eres un analista de estrategia de búsqueda. Analiza preguntas y crea planes de búsqueda."
                    )
                ),
                HumanMessage(content=planning_prompt),
            ]
        )

        plan = (
            planning_response.content
            if hasattr(planning_response, "content")
            else str(planning_response)
        )
        logger.info(f"Search plan created: {plan[:200]}...")

        # Add plan to state
        return {"messages": state["messages"], "plan": plan}
    except Exception as e:
        logger.warning(f"Planning failed, continuing without plan: {e}")
        return {"plan": ""}


def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue or end."""
    last_message = state["messages"][-1]

    # Log whether this message has tool calls
    has_tool_calls = hasattr(last_message, "tool_calls") and last_message.tool_calls

    if not has_tool_calls:
        logger.info(
            f"Agent ended: No tool calls found. Final response type: {type(last_message).__name__}"
        )
        if hasattr(last_message, "content") and isinstance(last_message.content, str):
            logger.debug(f"Final response preview: {last_message.content[:150]}...")
        return END

    # Log tool calls that will be executed
    tool_names = [
        call.get("name") if isinstance(call, dict) else getattr(call, "name", "unknown")
        for call in getattr(last_message, "tool_calls", [])
    ]
    logger.info(f"Agent continuing with tool calls: {tool_names}")
    return "tools"


def check_for_empty_db_search(state: AgentState) -> bool:
    """Check if the most recent db_search tool call returned 0 documents.

    This helps detect when we should suggest clarification instead of
    immediately falling back to web search.
    """
    for msg in reversed(state["messages"]):
        if hasattr(msg, "name") and msg.name == "db_search":
            # Check if the content indicates 0 documents
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            normalized = content.lower().strip()
            if normalized == "[]" or "found 0" in normalized or "no documents" in normalized:
                return True
    return False


class GradeDocuments(BaseModel):
    """Binary relevance decision for retrieved context."""

    binary_score: Literal["yes", "no"]


def _latest_user_question(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage) and isinstance(message.content, str):
            return message.content
    return ""


def _extract_latest_db_search_docs(messages: list[BaseMessage]) -> list[dict]:
    for message in reversed(messages):
        if hasattr(message, "name") and getattr(message, "name", None) == "db_search":
            content = message.content if isinstance(message.content, str) else str(message.content)
            try:
                docs = json.loads(content)
                if isinstance(docs, list):
                    return [doc for doc in docs if isinstance(doc, dict)]
            except Exception:
                return []
    return []


def _extract_latest_ranked_docs(messages: list[BaseMessage]) -> list[dict]:
    for message in reversed(messages):
        if hasattr(message, "name") and getattr(message, "name", None) == "rank_retrieval_results":
            content = message.content if isinstance(message.content, str) else str(message.content)
            try:
                docs = json.loads(content)
                if isinstance(docs, list):
                    return [doc for doc in docs if isinstance(doc, dict)]
            except Exception:
                return []
    return []


def route_after_tools(
    state: AgentState,
) -> Literal["rank_retrieval", "grade_documents", "db_unavailable", "agent"]:
    """Route after ToolNode execution.

    - If db_search returned docs, grade relevance.
    - Otherwise continue regular agent loop.
    """
    docs = _extract_latest_db_search_docs(state["messages"])
    if docs:
        return "rank_retrieval"

    status = get_last_search_status()
    if status in ("infra_error", "schema_error", "error"):
        logger.warning(
            "DB retrieval backend unavailable (status=%s); returning db_unavailable response.",
            status,
        )
        return "db_unavailable"
    return "agent"


def db_unavailable_node(state: AgentState) -> AgentState:
    """Return clear fallback when retrieval backend is unavailable."""
    language = state.get("language") or "en"
    if language == "es":
        message = (
            "No puedo acceder temporalmente a la base de datos de documentos de Vecinita. "
            "Inténtalo nuevamente en unos minutos mientras restablecemos la conexión."
        )
    else:
        message = (
            "I can’t access the Vecinita document database right now. "
            "Please try again in a few minutes while the connection is restored."
        )
    return {"messages": [AIMessage(content=message)]}


def rank_retrieval_node(state: AgentState) -> AgentState:
    """Rerank latest db_search results before grading/answering."""
    docs = _extract_latest_db_search_docs(state["messages"])
    question = _latest_user_question(state["messages"]) or state.get("question", "")

    if not docs:
        return {}

    try:
        ranked_json = rank_retrieval_results_tool.invoke(
            {
                "query": question,
                "results_json": json.dumps(docs, ensure_ascii=False),
                "top_k": min(10, len(docs)),
            }
        )
        ranked_text = ranked_json if isinstance(ranked_json, str) else str(ranked_json)
        return {
            "messages": [
                ToolMessage(
                    content=ranked_text,
                    tool_call_id="rank-retrieval-node",
                    name="rank_retrieval_results",
                )
            ]
        }
    except Exception as exc:
        logger.warning("Ranking node failed (%s); proceeding with unranked results.", exc)
        return {}


def grade_documents_node(state: AgentState) -> AgentState:
    """Grade whether latest retrieved docs are relevant to the user question."""
    docs = _extract_latest_ranked_docs(state["messages"]) or _extract_latest_db_search_docs(
        state["messages"]
    )
    question = _latest_user_question(state["messages"]) or state.get("question", "")

    if not docs:
        return {"grade_result": "no"}

    context = "\n\n".join((doc.get("content") or "") for doc in docs[:5])
    grading_prompt = (
        "You are grading retrieval relevance for a RAG agent.\n"
        "Return yes if the retrieved context is relevant to the user question, otherwise no.\n"
        f"Question: {question}\n"
        f"Retrieved Context:\n{context}"
    )

    try:
        grader = _get_llm_without_tools(state.get("provider"), state.get("model"))
        graded = grader.with_structured_output(GradeDocuments).invoke(
            [HumanMessage(content=grading_prompt)]
        )
        score = "yes" if str(graded.binary_score).lower() == "yes" else "no"
        logger.info("Retrieved document relevance grade: %s", score)
        return {"grade_result": score}
    except Exception as exc:
        logger.warning(
            "Document grading failed (%s). Defaulting to relevant to avoid dead-end.", exc
        )
        return {"grade_result": "yes"}


def route_after_grading(state: AgentState) -> Literal["agent", "rewrite_question"]:
    """Route based on grade decision."""
    if state.get("fast_mode", agent_fast_mode):
        return "agent"
    return "agent" if state.get("grade_result") == "yes" else "rewrite_question"


def rewrite_question_node(state: AgentState) -> AgentState:
    """Rewrite the latest user question when retrieved docs are not relevant."""
    question = _latest_user_question(state["messages"]) or state.get("question", "")
    try:
        rewritten_text = rewrite_question_tool.invoke(
            {
                "question": question,
                "provider": state.get("provider"),
                "model": state.get("model"),
            }
        )
        logger.info("Question rewritten for retrieval retry.")
        final_text = rewritten_text if isinstance(rewritten_text, str) else str(rewritten_text)
        return {"messages": [HumanMessage(content=final_text)]}
    except Exception as exc:
        logger.warning("Question rewrite failed (%s); continuing with original question.", exc)
        return {"messages": [HumanMessage(content=question)]}


# --- Build LangGraph ---
logger.info("Building LangGraph workflow...")
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planning", planning_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("rank_retrieval", rank_retrieval_node)
workflow.add_node("grade_documents", grade_documents_node)
workflow.add_node("rewrite_question", rewrite_question_node)
workflow.add_node("db_unavailable", db_unavailable_node)

# Add conditional routing from START based on query complexity
# Simple queries skip planning and go straight to agent
workflow.add_conditional_edges(
    START,
    classify_query_complexity,
    {
        "simple": "agent",  # Simple queries: direct to agent
        "complex": "planning",  # Complex queries: plan first
    },
)

# Planning always goes to agent
workflow.add_edge("planning", "agent")

# Agent decides: continue with tools or end
workflow.add_conditional_edges("agent", should_continue, ["tools", END])

# Route after tools execution: grade retrieved docs when available
workflow.add_conditional_edges(
    "tools",
    route_after_tools,
    {
        "rank_retrieval": "rank_retrieval",
        "grade_documents": "grade_documents",
        "db_unavailable": "db_unavailable",
        "agent": "agent",
    },
)

workflow.add_edge("rank_retrieval", "grade_documents")

# Route after grading: answer path or rewrite/retry retrieval
workflow.add_conditional_edges(
    "grade_documents",
    route_after_grading,
    {
        "agent": "agent",
        "rewrite_question": "rewrite_question",
    },
)

workflow.add_edge("rewrite_question", "agent")
workflow.add_edge("db_unavailable", END)

# Compile with memory
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
logger.info("LangGraph workflow compiled successfully")

# --- API Endpoints ---

# --- Helper: Deterministic static FAQ matcher ---


def _find_static_faq_answer(question: str, language: str) -> str | None:
    try:
        import string
        import unicodedata

        q = question.lower().strip()
        table = str.maketrans("", "", string.punctuation + "¿¡")
        q_clean = q.translate(table)
        # Remove accents for robust matching

        def _unaccent(s: str) -> str:
            return "".join(
                c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
            )

        q_unaccent = _unaccent(q_clean)
        faqs = FAQ_DATABASE.get(language, FAQ_DATABASE.get("en", {}))
        # Exact match against original
        if q in faqs:
            return faqs[q]
        # Exact match against cleaned
        for k, v in faqs.items():
            if k.translate(table) == q_clean:
                return v
        # Partial match using cleaned strings
        if len(q_clean) >= 10:
            for k, v in faqs.items():
                k_clean = k.translate(table)
                k_unaccent = _unaccent(k_clean)
                if (
                    k_clean in q_clean
                    or q_clean in k_clean
                    or k_unaccent in q_unaccent
                    or q_unaccent in k_unaccent
                ):
                    return v
        return None
    except Exception:
        return None


# --- THIS IS THE NEW ROOT ENDPOINT ---


@app.get("/")
async def get_root():
    """Returns API information and available endpoints."""
    return {
        "service": "Vecinita Backend API",
        "status": "running",
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask?question=<your_question>",
            "docs": "/docs",
            "config": "/config",
        },
        "message": "Use the React frontend at http://localhost:3000 or call /ask endpoint directly",
    }


# --- Favicon endpoint removed - using separate React frontend ---


@app.get("/health")
async def health():
    """Simple healthcheck endpoint used by Docker Compose."""
    preflight = getattr(app.state, "preflight", None)
    readiness = (
        preflight.get("status")
        if isinstance(preflight, dict) and preflight.get("status")
        else "unknown"
    )
    return {
        "status": "ok",
        "readiness": readiness,
        "preflight": preflight,
    }


@app.get("/test-db-search")
def test_db_search(query: str = "community resources"):
    """Test database search functionality and return diagnostic info.

    Args:
        query: Test query string (default: "community resources")

    Returns:
        Diagnostic information about the search operation
    """
    diagnostics: dict[str, Any] = {}

    try:
        logger.info(f"Test DB Search: Query = '{query}'")

        if supabase is None:
            return {"error": "Supabase client not initialized"}

        # Step 1: Check if table exists and has data
        try:
            table_result = supabase.table("document_chunks").select("*").limit(1).execute()
            total_rows = (
                table_result.count
                if hasattr(table_result, "count")
                else len(table_result.data) if table_result.data else 0
            )
            diagnostics["table_exists"] = True
            diagnostics["total_rows"] = total_rows
            logger.info(f"Test DB Search: Table has {total_rows} rows")
        except Exception as e:
            diagnostics["table_exists"] = False
            diagnostics["table_error"] = str(e)
            logger.error(f"Test DB Search: Table check failed: {e}")

        # Step 2: Check if embeddings exist and are non-null
        try:
            embedding_check = (
                supabase.table("document_chunks").select("id,embedding").limit(5).execute()
            )
            if embedding_check.data:
                embedding_rows: list[dict[str, Any]] = embedding_check.data  # type: ignore[assignment]
                non_null_embeddings = sum(
                    1 for row in embedding_rows if row.get("embedding") is not None
                )
                diagnostics["embeddings_exist"] = non_null_embeddings > 0
                diagnostics["sample_embedding_count"] = non_null_embeddings
                diagnostics["sample_size"] = len(embedding_rows)

                # Check embedding dimension if we have one
                if non_null_embeddings > 0:
                    sample_embedding = next(
                        (row["embedding"] for row in embedding_rows if row.get("embedding")), None
                    )
                    if sample_embedding:
                        if isinstance(sample_embedding, list):
                            diagnostics["stored_embedding_dimension"] = len(sample_embedding)
                        elif isinstance(sample_embedding, str):
                            # Might be stored as string, try to parse
                            try:
                                import json

                                parsed = json.loads(sample_embedding)
                                diagnostics["stored_embedding_dimension"] = len(parsed)
                            except Exception:
                                diagnostics["stored_embedding_dimension"] = (
                                    "unknown (string format)"
                                )
                        else:
                            diagnostics["stored_embedding_dimension"] = (
                                f"unknown (type: {type(sample_embedding).__name__})"
                            )

                logger.info(
                    f"Test DB Search: {non_null_embeddings}/{len(embedding_rows)} sample rows have embeddings"
                )
            else:
                diagnostics["embeddings_exist"] = False
                diagnostics["embedding_check_error"] = "No data returned"
        except Exception as e:
            diagnostics["embeddings_exist"] = False
            diagnostics["embedding_check_error"] = str(e)
            logger.error(f"Test DB Search: Embedding check failed: {e}")

        # Step 3: Check if RPC function exists
        try:
            # Try calling RPC with a simple test embedding (all zeros)
            test_embedding = [0.0] * 384
            rpc_test = supabase.rpc(
                "search_similar_documents",
                {"query_embedding": test_embedding, "match_threshold": 0.0, "match_count": 1},
            ).execute()
            diagnostics["rpc_function_exists"] = True
            rpc_test_data: list[dict[str, Any]] = rpc_test.data or []  # type: ignore[assignment]
            diagnostics["rpc_test_results"] = len(rpc_test_data)
            logger.info(
                f"Test DB Search: RPC function exists and returned {diagnostics['rpc_test_results']} results with test embedding"
            )
        except Exception as e:
            diagnostics["rpc_function_exists"] = False
            diagnostics["rpc_error"] = str(e)
            logger.error(f"Test DB Search: RPC function test failed: {e}")

        # Step 4: Generate embedding from query
        question_embedding = embedding_model.embed_query(query)
        diagnostics["query_embedding_dimension"] = len(question_embedding)
        logger.info(f"Test DB Search: Generated embedding dimension = {len(question_embedding)}")
        logger.info(f"Test DB Search: First 5 values = {question_embedding[:5]}")

        # Step 5: Try actual search with threshold=0.0
        test_threshold = 0.0
        logger.info(f"Test DB Search: Searching with threshold = {test_threshold}")

        result = supabase.rpc(
            "search_similar_documents",
            {
                "query_embedding": question_embedding,
                "match_threshold": test_threshold,
                "match_count": 10,
            },
        ).execute()
        result_data: list[dict[str, Any]] = result.data or []  # type: ignore[assignment]

        logger.info(f"Test DB Search: Found {len(result_data)} results")
        diagnostics["search_results_found"] = len(result_data)

        if result_data:
            # Show similarity scores
            similarities = [doc.get("similarity", 0) for doc in result_data]
            logger.info(f"Test DB Search: Similarity scores = {similarities}")

            return {
                "status": "success",
                "query": query,
                "diagnostics": diagnostics,
                "results_found": len(result_data),
                "similarity_range": {
                    "min": min(similarities),
                    "max": max(similarities),
                    "avg": sum(similarities) / len(similarities),
                },
                "sample_result": {
                    "content_preview": result_data[0].get("content", "")[:200],
                    "source_url": result_data[0].get("source_url", "N/A"),
                    "similarity": result_data[0].get("similarity", 0),
                },
                "all_similarities": similarities,
            }
        else:
            return {
                "status": "no_results",
                "query": query,
                "diagnostics": diagnostics,
                "message": "No results found. See diagnostics for details.",
                "recommendations": _get_recommendations(diagnostics),
            }

    except Exception as e:
        logger.error(f"Test DB Search Error: {e}")
        return {
            "status": "error",
            "query": query,
            "diagnostics": diagnostics,
            "error": str(e),
            "error_type": type(e).__name__,
        }


def _get_recommendations(diagnostics: dict) -> list:
    """Generate recommendations based on diagnostic results."""
    recommendations = []

    if not diagnostics.get("table_exists"):
        recommendations.append(
            "❌ Table 'document_chunks' not found or not accessible. Check database connection and permissions."
        )

    if diagnostics.get("total_rows", 0) == 0:
        recommendations.append(
            "❌ Table is empty. Run the scraper to populate data: cd backend && uv run python src/utils/vector_loader.py"
        )

    if not diagnostics.get("embeddings_exist"):
        recommendations.append(
            "❌ Embeddings are NULL in database. Re-run vector loader to generate embeddings."
        )

    if not diagnostics.get("rpc_function_exists"):
        recommendations.append(
            "❌ RPC function 'search_similar_documents' not found. Run: psql $DATABASE_URL -f backend/scripts/schema_install.sql"
        )
    elif diagnostics.get("rpc_test_results", 0) == 0 and diagnostics.get("total_rows", 0) > 0:
        recommendations.append(
            "⚠️ RPC function exists but returns no results with test embedding. Check function implementation."
        )

    stored_dim = diagnostics.get("stored_embedding_dimension")
    query_dim = diagnostics.get("query_embedding_dimension")
    if stored_dim and query_dim and stored_dim != query_dim:
        recommendations.append(
            f"❌ DIMENSION MISMATCH: Stored embeddings are {stored_dim}D but query is {query_dim}D. Re-generate embeddings with correct model."
        )

    if (
        diagnostics.get("search_results_found", 0) == 0
        and diagnostics.get("rpc_test_results", 0) > 0
    ):
        recommendations.append(
            "⚠️ RPC works with test embedding but not with query embedding. Check if embeddings were generated with the same model."
        )

    if not recommendations:
        recommendations.append(
            "✅ All diagnostics passed. Issue may be with query content or similarity calculation."
        )

    return recommendations


def _response_payload(
    answer_text: str,
    *,
    thread_id: str,
    started_at: float,
    sources: list[dict] | None = None,
    latency_breakdown: dict | None = None,
) -> dict:
    payload = {
        "answer": answer_text,
        "thread_id": thread_id,
        "response_time_ms": int((time.perf_counter() - started_at) * 1000),
    }
    if sources is not None:
        payload["sources"] = sources
    if latency_breakdown:
        payload["latency_breakdown"] = latency_breakdown
    return payload


@app.get("/db-info")
def get_db_info():
    """Get basic database information for debugging.

    Returns:
        Database statistics and sample data
    """
    if supabase is None:
        return {"status": "error", "error": "Supabase client not initialized"}
    _supa = supabase
    try:
        info: dict[str, Any] = {}

        # Get row count
        try:
            count_result = _supa.table("document_chunks").select("id").limit(1).execute()
            info["total_rows"] = (
                count_result.count
                if hasattr(count_result, "count")
                else len(_supa.table("document_chunks").select("id").execute().data or [])
            )
        except Exception as e:
            info["total_rows"] = f"error: {e}"

        # Get sample rows with embeddings
        try:
            sample_result = (
                _supa.table("document_chunks")
                .select("id,source_url,chunk_index,embedding,content")
                .limit(3)
                .execute()
            )
            if sample_result.data:
                sample_rows: list[dict[str, Any]] = sample_result.data  # type: ignore[assignment]
                samples = []
                for row in sample_rows:
                    sample: dict[str, Any] = {
                        "id": row.get("id"),
                        "source_url": row.get("source_url"),
                        "chunk_index": row.get("chunk_index"),
                        "content_preview": (
                            row.get("content", "")[:100] + "..." if row.get("content") else None
                        ),
                        "has_embedding": row.get("embedding") is not None,
                    }

                    # Try to get embedding dimension
                    if row.get("embedding"):
                        emb = row["embedding"]
                        if isinstance(emb, list):
                            sample["embedding_dimension"] = len(emb)
                            sample["embedding_type"] = "list"
                        elif isinstance(emb, str):
                            sample["embedding_type"] = "string"
                            try:
                                import json

                                parsed = json.loads(emb)
                                sample["embedding_dimension"] = len(parsed)
                            except Exception:
                                sample["embedding_dimension"] = "parse_failed"
                        else:
                            sample["embedding_type"] = type(emb).__name__

                    samples.append(sample)

                info["sample_rows"] = samples
        except Exception as e:
            info["sample_error"] = str(e)

        # Check RPC function
        try:
            test_embedding = [0.0] * 384
            rpc_result = _supa.rpc(
                "search_similar_documents",
                {"query_embedding": test_embedding, "match_threshold": 0.0, "match_count": 1},
            ).execute()
            info["rpc_function_works"] = True
            rpc_data: list[dict[str, Any]] = rpc_result.data or []  # type: ignore[assignment]
            info["rpc_test_returned"] = len(rpc_data)
        except Exception as e:
            info["rpc_function_works"] = False
            info["rpc_error"] = str(e)

        return {
            "status": "success",
            "database_info": info,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "expected_dimension": 384,
        }

    except Exception as e:
        return {"status": "error", "error": str(e), "error_type": type(e).__name__}


@app.get("/ask")
async def ask_question(
    question: str | None = Query(default=None),
    query: str | None = Query(default=None),
    thread_id: str = "default",
    lang: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
    context_answer: str | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma-separated metadata tags"),
    tag_match_mode: str = Query(default="any", description="Tag match mode: any|all"),
    include_untagged_fallback: bool = Query(default=True),
    rerank: bool = Query(default=False),
    rerank_top_k: int = Query(default=10, ge=1, le=50),
):
    """Handles Q&A requests from the UI or API using LangGraph agent"""
    started_at = time.perf_counter()

    # Accept both 'question' and legacy 'query' parameter names
    if question is None and query is not None:
        question = query
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question parameter cannot be empty. Use 'question' or 'query'.",
        )

    try:
        provider, model = _resolve_effective_provider_model(provider, model)

        # Detect language unless explicitly provided
        if not lang:
            try:
                lang = detect(question)
            except LangDetectException:
                lang = "en"
                logger.warning(
                    "Language detection failed for question: '%s'. Defaulting to English.", question
                )
            # Heuristic override: treat as Spanish if question contains Spanish punctuation or accents
            if lang != "es":
                if any(ch in question for ch in ["¿", "¡", "á", "é", "í", "ó", "ú", "ñ"]):
                    lang = "es"

        # Try static response first for deterministic FAQ handling in both languages
        # --- GuardrailsAI: validate input before invoking agent ---
        from src.agent.guardrails_config import validate_input

        contextual_follow_up = bool(context_answer) and _is_contextual_follow_up(question, lang)
        guard_result = validate_input(
            question,
            lang=lang,
            allow_contextual_follow_up=contextual_follow_up,
        )
        if not guard_result.passed:
            return _response_payload(
                guard_result.reason, thread_id=thread_id, started_at=started_at, sources=[]
            )
        # If PII was detected and redacted, use redacted version
        effective_question = guard_result.redacted if guard_result.redacted else question

        if contextual_follow_up:
            llm_started_at = time.perf_counter()
            answer = _build_contextual_follow_up_answer(
                question=effective_question,
                prior_answer=context_answer or "",
                language=lang,
                provider=provider,
                model=model,
            )
            llm_ms = int((time.perf_counter() - llm_started_at) * 1000)

            from src.agent.guardrails_config import validate_output

            out_guard = validate_output(answer)
            if not out_guard.passed:
                answer = out_guard.reason
            elif out_guard.redacted:
                answer = out_guard.redacted

            return _response_payload(
                answer,
                thread_id=thread_id,
                started_at=started_at,
                sources=[],
                latency_breakdown={"retrieval_invoke_ms": 0, "llm_ms": llm_ms, "db_search": {}},
            )

        logger.info(
            f"\n--- New request received: '{effective_question}' (Detected Language: {lang}, Thread: {thread_id}) ---"
        )

        answer_seeking = _is_answer_seeking_query(effective_question, lang)
        if not answer_seeking:
            local_static = _find_static_faq_answer(effective_question, lang)
            if local_static:
                logger.info("Returning static FAQ answer (local matcher, non-answer intent).")
                return _response_payload(local_static, thread_id=thread_id, started_at=started_at)
            try:
                static_answer = static_response_tool.invoke(
                    {"query": effective_question, "language": lang}
                )
                if static_answer:
                    logger.info(
                        "Returning static FAQ answer without retrieval (non-answer intent)."
                    )
                    return _response_payload(
                        static_answer, thread_id=thread_id, started_at=started_at
                    )
            except Exception as static_exc:
                logger.warning(f"Static response check failed: {static_exc}")

        # Deterministic, intent-gated RAG is handled below.

        request_tags = parse_tags_input(tags)
        search_token = set_db_search_options(
            tags=request_tags,
            tag_match_mode=tag_match_mode,
            include_untagged_fallback=include_untagged_fallback,
            rerank=rerank,
            rerank_top_k=rerank_top_k,
        )
        try:
            logger.info("Intent gate: answer_seeking=%s", answer_seeking)
            retrieval_ms = 0
            llm_ms = 0

            if not answer_seeking:
                static_faq_answer = _find_static_faq_answer(effective_question, lang)
                if static_faq_answer:
                    answer = static_faq_answer
                else:
                    fallback_llm = _get_llm_without_tools(provider, model)
                    quick_prompt = f"Respond briefly and naturally in {'Spanish' if lang == 'es' else 'English'}: {effective_question}"
                    llm_started_at = time.perf_counter()
                    raw = fallback_llm.invoke([HumanMessage(content=quick_prompt)])
                    llm_ms = int((time.perf_counter() - llm_started_at) * 1000)
                    answer = raw.content if hasattr(raw, "content") else str(raw)
                sources: list[dict] = []
            else:
                logger.info("Running mandatory one-shot db_search for answer-seeking query")
                retrieval_started_at = time.perf_counter()
                raw_search = db_search_tool.invoke(effective_question)
                retrieval_ms = int((time.perf_counter() - retrieval_started_at) * 1000)
                retrieved_docs = _parse_db_search_docs(
                    raw_search if isinstance(raw_search, str) else str(raw_search)
                )
                weak_retrieval = _is_weak_retrieval(retrieved_docs)

                llm_started_at = time.perf_counter()
                answer = _build_deterministic_rag_answer(
                    question=effective_question,
                    language=lang,
                    provider=provider,
                    model=model,
                    retrieved_docs=retrieved_docs,
                    weak_retrieval=weak_retrieval,
                )
                llm_ms = int((time.perf_counter() - llm_started_at) * 1000)
                sources = _build_sources_from_docs(retrieved_docs)
                answer = _sanitize_answer_links(
                    answer,
                    _allowed_source_urls_from_docs(retrieved_docs),
                    lang,
                )
                logger.info(
                    "Deterministic RAG complete: docs=%s, weak=%s, sources=%s",
                    len(retrieved_docs),
                    weak_retrieval,
                    len(sources),
                )

            db_metrics = get_last_search_metrics() if answer_seeking else {}
            latency_breakdown = {
                "retrieval_invoke_ms": retrieval_ms,
                "llm_ms": llm_ms,
                "db_search": db_metrics,
            }
        finally:
            reset_db_search_options(search_token)

        db_status = get_last_search_status()
        if answer_seeking and not sources and db_status in {"schema_error", "infra_error", "error"}:
            logger.warning(
                "Retrieval backend failure detected during deterministic path (status=%s).",
                db_status,
            )

        # --- GuardrailsAI: validate output before returning ---
        from src.agent.guardrails_config import validate_output

        out_guard = validate_output(answer)
        if not out_guard.passed:
            answer = out_guard.reason
        elif out_guard.redacted:
            answer = out_guard.redacted

        return _response_payload(
            answer,
            thread_id=thread_id,
            started_at=started_at,
            sources=sources,
            latency_breakdown=latency_breakdown,
        )

    except Exception as e:
        logger.error("Error processing question '%s': %s", question, str(e))
        logger.error("Full traceback:\n%s", traceback.format_exc())
        import re as _re

        is_rate_limit = e.__class__.__name__ in (
            "RateLimitError",
            "TooManyRequests",
            "RateLimitException",
        )
        if is_rate_limit:
            wait_seconds = 10.0
            m = _re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", str(e))
            if m:
                try:
                    wait_seconds = float(m.group(1))
                except Exception:
                    pass
            if "lang" in locals() and lang == "es":
                fallback = f"El asistente está limitado por tasa temporalmente. Intenta nuevamente en {wait_seconds:.0f} segundos."
            else:
                fallback = f"The assistant is temporarily unavailable. Please try again in {wait_seconds:.0f} seconds."
            return _response_payload(fallback, thread_id=thread_id, started_at=started_at)
        # Non-rate-limit errors: propagate as HTTP 500
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/ask-stream")
async def ask_question_stream(
    question: str | None = Query(default=None),
    query: str | None = Query(default=None),
    thread_id: str = "default",
    lang: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
    clarification_response: str | None = Query(default=None),
    context_answer: str | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma-separated metadata tags"),
    tag_match_mode: str = Query(default="any", description="Tag match mode: any|all"),
    include_untagged_fallback: bool = Query(default=True),
    rerank: bool = Query(default=False),
    rerank_top_k: int = Query(default=10, ge=1, le=50),
):
    """Enhanced streaming endpoint with conversational agent activity updates.

    Sends JSON objects showing agent's thinking process:
    - {"type": "thinking", "message": "Let me think about your question..."}
    - {"type": "thinking", "message": "Looking through our local resources..."}
    - {"type": "clarification", "questions": [...], "context": "..."} ← User must respond
    - {"type": "complete", "answer": "...", "sources": [...]}
    """
    # Accept both 'question' and legacy 'query' parameter names
    if question is None and query is not None:
        question = query
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question parameter cannot be empty. Use 'question' or 'query'.",
        )

    async def generate_stream():
        try:
            effective_provider, effective_model = _resolve_effective_provider_model(provider, model)

            def _sse(payload: dict) -> str:
                payload.setdefault(
                    "timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                )
                return f"data: {json.dumps(payload)}\\n\\n"

            # Detect language unless explicitly provided
            if not lang:
                try:
                    detected_lang = detect(question)
                    lang_local = detected_lang if detected_lang in ["es", "en"] else "en"
                except LangDetectException:
                    lang_local = "en"
                # Heuristic override: treat as Spanish if question contains Spanish punctuation or accents
                if lang_local != "es":
                    if any(c in question for c in "¿¡áéíóúñü"):
                        lang_local = "es"
            else:
                lang_local = lang

            logger.info(
                f"\n--- Streaming request received: '{question}' (Language: {lang_local}, Thread: {thread_id}) ---"
            )

            # Yield thinking message for FAQ check
            msg = get_agent_thinking_message("static_response", lang_local)
            yield _sse(
                {
                    "type": "thinking",
                    "message": msg,
                    "stage": "precheck",
                    "progress": 10,
                    "status": "working",
                    "waiting": False,
                }
            )

            # Yield thinking message for analysis
            msg = get_agent_thinking_message("analyzing", lang_local)
            yield _sse(
                {
                    "type": "thinking",
                    "message": msg,
                    "stage": "analysis",
                    "progress": 25,
                    "status": "working",
                    "waiting": False,
                }
            )
            answer_seeking = _is_answer_seeking_query(question, lang_local)
            contextual_follow_up = bool(context_answer) and _is_contextual_follow_up(
                question, lang_local
            )
            logger.info("Streaming intent gate: answer_seeking=%s", answer_seeking)

            if contextual_follow_up:
                answer = _build_contextual_follow_up_answer(
                    question=question,
                    prior_answer=context_answer or "",
                    language=lang_local,
                    provider=effective_provider,
                    model=effective_model,
                )
                yield _sse(
                    {
                        "type": "complete",
                        "answer": answer,
                        "sources": [],
                        "suggested_questions": _build_follow_up_suggestions(
                            question=question,
                            answer=answer,
                            language=lang_local,
                            sources=[],
                        ),
                        "thread_id": thread_id,
                        "plan": "",
                        "metadata": {
                            "progress": 100,
                            "stage": "complete",
                        },
                    }
                )
                return

            if not answer_seeking:
                local_static = _find_static_faq_answer(question, lang_local)
                if local_static:
                    logger.info("Returning static FAQ answer (streaming, non-answer intent).")
                    yield _sse(
                        {
                            "type": "complete",
                            "answer": local_static,
                            "sources": [],
                            "suggested_questions": _build_follow_up_suggestions(
                                question=question,
                                answer=local_static,
                                language=lang_local,
                                sources=[],
                            ),
                            "thread_id": thread_id,
                            "plan": "",
                            "metadata": {
                                "progress": 100,
                                "stage": "complete",
                            },
                        }
                    )
                    return

            sources: list[dict] = []
            plan = ""

            if not answer_seeking:
                local_non_answer = _find_static_faq_answer(question, lang_local)
                if local_non_answer:
                    answer = local_non_answer
                else:
                    llm_plain = _get_llm_without_tools(effective_provider, effective_model)
                    quick_prompt = f"Respond briefly and naturally in {'Spanish' if lang_local == 'es' else 'English'}: {question}"
                    plain = llm_plain.invoke([HumanMessage(content=quick_prompt)])
                    answer = plain.content if hasattr(plain, "content") else str(plain)
            else:
                tool_msg = get_agent_thinking_message("db_search", lang_local)
                yield _sse(
                    {
                        "type": "thinking",
                        "message": tool_msg,
                        "stage": "tooling",
                        "progress": 40,
                        "status": "working",
                        "waiting": False,
                        "tool": "db_search",
                    }
                )
                yield _sse(
                    {
                        "type": "tool_event",
                        "phase": "start",
                        "tool": "db_search",
                        "message": tool_msg,
                        "stage": "tooling",
                        "progress": 42,
                        "status": "working",
                        "transient": True,
                        "waiting": True,
                    }
                )

                request_tags = parse_tags_input(tags)
                search_token = set_db_search_options(
                    tags=request_tags,
                    tag_match_mode=tag_match_mode,
                    include_untagged_fallback=include_untagged_fallback,
                    rerank=rerank,
                    rerank_top_k=rerank_top_k,
                )
                try:
                    raw_search = db_search_tool.invoke({"query": question})
                finally:
                    reset_db_search_options(search_token)

                raw_search_text = raw_search if isinstance(raw_search, str) else str(raw_search)
                retrieved_docs = _parse_db_search_docs(raw_search_text)
                weak_retrieval = _is_weak_retrieval(retrieved_docs)

                yield _sse(
                    {
                        "type": "tool_event",
                        "phase": "result",
                        "tool": "db_search",
                        "message": _summarize_tool_result("db_search", raw_search_text, lang_local),
                        "stage": "tooling",
                        "progress": 62,
                        "status": "working",
                        "transient": True,
                        "waiting": False,
                    }
                )

                answer = _build_deterministic_rag_answer(
                    question=question,
                    language=lang_local,
                    provider=effective_provider,
                    model=effective_model,
                    retrieved_docs=retrieved_docs,
                    weak_retrieval=weak_retrieval,
                )
                sources = _build_sources_from_docs(retrieved_docs)
                answer = _sanitize_answer_links(
                    answer,
                    _allowed_source_urls_from_docs(retrieved_docs),
                    lang_local,
                )
                logger.info(
                    "Streaming deterministic RAG complete: docs=%s, weak=%s, sources=%s",
                    len(retrieved_docs),
                    weak_retrieval,
                    len(sources),
                )

            yield _sse(
                {
                    "type": "thinking",
                    "message": (
                        "Finalizing answer..." if lang_local != "es" else "Finalizando respuesta..."
                    ),
                    "stage": "finalizing",
                    "progress": 95,
                    "status": "working",
                    "waiting": False,
                }
            )

            # Yield complete response
            yield _sse(
                {
                    "type": "complete",
                    "answer": answer,
                    "sources": sources,
                    "suggested_questions": _build_follow_up_suggestions(
                        question=question,
                        answer=answer,
                        language=lang_local,
                        sources=sources,
                    ),
                    "thread_id": thread_id,
                    "plan": plan,
                    "metadata": {
                        "progress": 100,
                        "stage": "complete",
                    },
                }
            )

        except Exception as e:
            logger.error("Error in streaming endpoint '%s': %s", question, str(e))
            logger.error("Full traceback:\n%s", traceback.format_exc())

            # Handle rate limits gracefully
            is_rate_limit = e.__class__.__name__ in (
                "RateLimitError",
                "TooManyRequests",
                "RateLimitException",
            )
            if is_rate_limit:
                fallback = (
                    "Servicio temporalmente no disponible. Inténtalo de nuevo en un momento."
                    if lang_local == "es"
                    else "Service temporarily unavailable. Please try again in a moment."
                )
            else:
                fallback = (
                    f"Error procesando la pregunta: {str(e)}"
                    if lang_local == "es"
                    else f"Error processing question: {str(e)}"
                )

            yield _sse(
                {
                    "type": "error",
                    "message": fallback,
                    "stage": "error",
                    "progress": 100,
                    "status": "error",
                }
            )

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


class ModelSelection(BaseModel):
    provider: str
    model: str | None = None
    lock: bool | None = None


@app.get("/model-selection")
def get_model_selection():
    """Return current model selection and availability map for frontend."""
    # Reuse config() enumerations for available providers/models
    available = config()
    return {
        "current": {
            "provider": CURRENT_SELECTION.get("provider"),
            "model": CURRENT_SELECTION.get("model"),
            "locked": CURRENT_SELECTION.get("locked"),
        },
        "available": available,
    }


@app.post("/model-selection")
def set_model_selection(selection: ModelSelection):
    """Set the local model selection if not locked."""
    if CURRENT_SELECTION.get("locked"):
        raise HTTPException(status_code=403, detail="Model selection is locked")

    normalized_provider = llm_client_manager.normalize_provider(selection.provider)
    if normalized_provider != "ollama":
        raise HTTPException(
            status_code=400,
            detail="Only the local Ollama provider is supported",
        )

    # Validate model if provided
    if selection.model:
        available = config()
        avail_models = available["models"].get("ollama", [])
        if selection.model not in avail_models:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported local model: {selection.model}",
            )

    # Save selection (file + in-memory)
    _save_model_selection_to_file("ollama", selection.model, selection.lock)
    return {"status": "ok", "current": CURRENT_SELECTION}


@app.get("/config")
def config():
    """Expose the local-only LLM configuration for frontend discovery."""
    payload = llm_client_manager.config_payload()
    payload["runtime"] = {
        "fast_mode": agent_fast_mode,
        "max_response_sentences": agent_max_response_sentences,
        "max_response_chars": agent_max_response_chars,
        "reachable": llm_client_manager.is_reachable(),
    }
    return payload


@app.get("/privacy")
def privacy():
    """Return Privacy Policy markdown content for display."""
    policy_path = Path(__file__).parent.parent.parent / "docs" / "PRIVACY_POLICY.md"
    # Fallback to repo docs if local not found
    if not policy_path.exists():
        policy_path = Path(__file__).parents[3] / "docs" / "PRIVACY_POLICY.md"
    if not policy_path.exists():
        raise HTTPException(status_code=404, detail="Privacy policy not found")
    return JSONResponse({"markdown": policy_path.read_text(encoding="utf-8")})


# --end-of-file--

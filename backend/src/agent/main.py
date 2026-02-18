# main.py
# FastAPI application for the Vecinita RAG Q&A system.
# This version includes an explicit rule for response language.
# Serves the index.html UI at the root "/" endpoint.

import os
import json
import time
import logging
import traceback
from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import TypedDict, Optional
from supabase import create_client, Client
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_community.chat_models import ChatOpenAI as ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langdetect import detect, LangDetectException
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Import tools
from .tools.db_search import create_db_search_tool
from .tools.static_response import create_static_response_tool, FAQ_DATABASE
from .tools.web_search import create_web_search_tool
from .tools.clarify_question import create_clarify_question_tool

# Load environment variables from .env file
load_dotenv()

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Initialize FastAPI App ---
app = FastAPI()

# --- Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Static files mount removed - using separate React frontend ---

# --- Load Environment Variables & Validate ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")
openai_api_key = os.environ.get(
    "OPENAI_API_KEY") or os.environ.get("OPEN_API_KEY")
deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
ollama_model = os.environ.get("OLLAMA_MODEL") or "llama3.2"
default_provider = (os.environ.get("DEFAULT_PROVIDER") or "llama").lower()
default_model = os.environ.get("DEFAULT_MODEL") or None
lock_model_selection_env = (os.environ.get("LOCK_MODEL_SELECTION") or "false").lower() in ["1", "true", "yes"]
selection_file_path = os.environ.get("MODEL_SELECTION_PATH") or str(Path(__file__).parent / "data" / "model_selection.json")
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and key must be set.")

# --- Initialize Clients ---
try:
    logger.info("Initializing Supabase client...")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")

    # Persisted model selection (optional JSON file)
    class Selection(TypedDict):
        provider: str
        model: Optional[str]
        locked: bool

    CURRENT_SELECTION: Selection = {
        "provider": str(default_provider),
        "model": default_model if default_model else None,
        "locked": bool(lock_model_selection_env),
    }

    def _load_model_selection_from_file():
        try:
            p = Path(selection_file_path)
            if p.exists():
                data = json.loads(p.read_text())
                # Minimal validation
                prov = (data.get("provider") or CURRENT_SELECTION["provider"]).lower()
                mod = data.get("model") or CURRENT_SELECTION["model"]
                locked = bool(data.get("locked", CURRENT_SELECTION["locked"]))
                CURRENT_SELECTION.update({"provider": prov, "model": mod, "locked": locked})
                logger.info(f"Model selection loaded: {CURRENT_SELECTION}")
        except Exception as e:
            logger.warning(f"Failed to load model selection file: {e}")

    def _save_model_selection_to_file(provider: str, model: str | None, locked: bool | None = None):
        try:
            payload = {
                "provider": provider,
                "model": model,
                "locked": CURRENT_SELECTION["locked"] if locked is None else bool(locked),
            }
            Path(selection_file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(selection_file_path).write_text(json.dumps(payload, indent=2))
            CURRENT_SELECTION.update(payload)
            logger.info(f"Model selection saved: {payload}")
        except Exception as e:
            logger.error(f"Failed to save model selection file: {e}")

    _load_model_selection_from_file()

    # Initialize default LLM: prefer DeepSeek, then Groq, then OpenAI, finally Ollama Llama
    if deepseek_api_key:
        logger.info("Initializing ChatOpenAI with DeepSeek (default)...")
        deepseek_base_url = os.environ.get(
            "DEEPSEEK_BASE_URL") or "https://api.deepseek.com/v1"
        llm = ChatOpenAI(
            temperature=0,
            api_key=deepseek_api_key,
            model="deepseek-chat",
            base_url=deepseek_base_url
        )
        logger.info("DeepSeek LLM initialized successfully")
    elif groq_api_key:
        logger.info("Initializing ChatGroq LLM (Llama fallback)...")
        llm = ChatGroq(temperature=0, groq_api_key=groq_api_key,
                       model_name="llama-3.1-8b-instant")
        logger.info("ChatGroq LLM initialized successfully")
    elif openai_api_key:
        logger.info("Initializing ChatOpenAI LLM (GPT fallback)...")
        llm = ChatOpenAI(temperature=0, api_key=openai_api_key,
                         model="gpt-4o-mini")
        logger.info("ChatOpenAI LLM initialized successfully")
    elif ollama_base_url:
        logger.info("Initializing ChatOllama (Llama fallback)...")
        llm = ChatOllama(temperature=0, model=ollama_model,
                         base_url=ollama_base_url)
        logger.info(
            f"ChatOllama initialized successfully (model={ollama_model})")
    else:
        raise RuntimeError(
            "No LLM provider configured. Set DEEPSEEK_API_KEY or GROQ_API_KEY or OPENAI_API_KEY/OPEN_API_KEY or OLLAMA_BASE_URL.")

    # Use dedicated Embedding Service for embeddings (lightweight agent!)
    # Embedding service runs as a separate Render free-tier service
    # Fallback to local FastEmbed if service unavailable
    logger.info("Initializing embedding model (Embedding Service)...")
    embedding_service_url = os.environ.get(
        "EMBEDDING_SERVICE_URL", "http://embedding-service:8001")

    try:
        from src.embedding_service.client import create_embedding_client
        embedding_model = create_embedding_client(embedding_service_url)
        logger.info(
            f"✅ Embedding model initialized via Embedding Service ({embedding_service_url})")
    except Exception as service_exc:
        logger.warning(
            f"Embedding service failed ({service_exc}); falling back to FastEmbed")
        try:
            embedding_model = FastEmbedEmbeddings(
                model_name="fast-bge-small-en-v1.5")
            logger.info(
                "Embedding model initialized successfully (FastEmbed fallback)")
        except Exception as emb_exc:
            logger.warning(
                f"FastEmbedEmbeddings failed ({emb_exc}); falling back to HuggingFace.")
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            embedding_model = HuggingFaceEmbeddings(model_name=model_name)
            logger.info(
                "Embedding model initialized successfully (HuggingFace fallback)")
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    logger.error(traceback.format_exc())
    raise RuntimeError(f"Failed to initialize clients: {e}")

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
        "Community health and wellbeing in Rhode Island"
    ]
}

# --- Define LangGraph State ---


class AgentState(TypedDict):
    """State for the Vecinita agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    language: str
    provider: str | None
    model: str | None
    plan: str | None  # Stores planning results


# --- Human-readable agent thinking messages ---
AGENT_THINKING_MESSAGES = {
    'es': {
        'static_response': 'Verificando si ya conozco esto...',
        'db_search': 'Revisando nuestros recursos locales...',
        'clarify_question': 'Necesito un poco más de información...',
        'web_search': 'Buscando información adicional...',
        'plan': 'Déjame pensar en tu pregunta...',
        'analyzing': 'Entendiendo tu pregunta...',
        'searching': 'Encontrando información relevante...',
    },
    'en': {
        'static_response': 'Checking if I already know this...',
        'db_search': 'Looking through our local resources...',
        'clarify_question': 'I need a bit more information...',
        'web_search': 'Searching for additional information...',
        'plan': 'Let me think about your question...',
        'analyzing': 'Understanding your question...',
        'searching': 'Finding relevant information...',
    }
}


def get_agent_thinking_message(tool_name: str, language: str) -> str:
    """Get human-readable conversational message for agent activity."""
    msgs = AGENT_THINKING_MESSAGES.get(language, AGENT_THINKING_MESSAGES['en'])
    return msgs.get(tool_name, 'Thinking...')


# --- Initialize Tools ---
logger.info("Initializing agent tools...")
# Use lower threshold (0.1) for better recall - can be tuned based on results
db_search_tool = create_db_search_tool(
    supabase, embedding_model, match_threshold=0.1, match_count=5)
web_search_tool = create_web_search_tool()
clarify_question_tool = create_clarify_question_tool()
static_response_tool = create_static_response_tool()
tools = [db_search_tool,
         static_response_tool,
         clarify_question_tool,
         web_search_tool]
# Filter out None values if any tool failed to initialize
tools = [t for t in tools if t is not None]
logger.info(f"Initialized {len(tools)} tools: {[tool.name for tool in tools]}")


def _get_llm_with_tools(provider: str | None, model: str | None):
    """Create an LLM bound with tools based on requested provider/model.

    Supported providers: 'llama' (Ollama preferred, Groq fallback), 'openai', 'deepseek'.
    Defaults: provider='llama', model from OLLAMA_MODEL or 'llama3.2';
    for OpenAI, default model='gpt-4o-mini'. For DeepSeek, default model='deepseek-chat'.
    """
    # Honor lock: if locked, override with persisted selection
    if CURRENT_SELECTION.get("locked"):
        provider = CURRENT_SELECTION["provider"]
        model = CURRENT_SELECTION["model"]

    selected_provider = (provider or CURRENT_SELECTION["provider"] or "llama").lower()
    if selected_provider == "llama":
        # Prefer local Ollama
        if ollama_base_url:
            use_model = model or ollama_model or "llama3.2"
            local_llm = ChatOllama(
                temperature=0, model=use_model, base_url=ollama_base_url)
            return local_llm.bind_tools(tools)
        # Fallback to Groq-hosted Llama if available
        if groq_api_key:
            use_model = model or "llama-3.1-8b-instant"
            groq_llm = ChatGroq(
                temperature=0, groq_api_key=groq_api_key, model_name=use_model)
            return groq_llm.bind_tools(tools)
        # Last resort: if nothing available, raise
        raise RuntimeError(
            "Llama provider requested but neither Ollama nor Groq are configured.")
    elif selected_provider == "openai":
        if not openai_api_key:
            raise RuntimeError(
                "OpenAI provider requested but OPENAI_API_KEY/OPEN_API_KEY is not set.")
        use_model = model or CURRENT_SELECTION.get("model") or "gpt-4o-mini"
        openai_llm = ChatOpenAI(
            temperature=0, api_key=openai_api_key, model=use_model)
        return openai_llm.bind_tools(tools)
    elif selected_provider == "deepseek":
        if not deepseek_api_key:
            raise RuntimeError(
                "DeepSeek provider requested but DEEPSEEK_API_KEY is not set.")
        # DeepSeek offers OpenAI-compatible API; use ChatOpenAI with base_url
        use_model = model or CURRENT_SELECTION.get("model") or "deepseek-chat"
        deepseek_llm = ChatOpenAI(
            temperature=0,
            api_key=deepseek_api_key,
            model=use_model,
            base_url=os.environ.get(
                "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        )
        return deepseek_llm.bind_tools(tools)
    else:
        raise RuntimeError(
            f"Unsupported provider: {selected_provider}. Use 'llama' or 'openai'.")


def _sanitize_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """Sanitize messages to ensure all content fields are strings.

    Some LLM APIs (like DeepSeek) require message content to be strings,
    but LangChain's ToolNode can produce messages with list content.
    This function converts any non-string content to a string.
    """
    sanitized = []
    for msg in messages:
        # Make a copy of the message to avoid modifying the original
        if isinstance(msg, ToolMessage):
            # ToolMessage content can be a list; convert to string
            content = msg.content
            if isinstance(content, list):
                # Convert list to JSON string
                content = json.dumps(content, ensure_ascii=False)
            # Create new ToolMessage with string content
            sanitized.append(ToolMessage(
                content=content,
                tool_call_id=msg.tool_call_id,
                name=msg.name if hasattr(msg, 'name') else None
            ))
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
            msg_dict['content'] = content
            sanitized.append(msg.__class__(**msg_dict))
    return sanitized

# --- Define Agent Node ---


def agent_node(state: AgentState) -> AgentState:
    """Agent node that calls the LLM with tool binding."""
    logger.info("Agent node: Processing messages...")

    # Log the current conversation state for debugging
    last_message = state["messages"][-1]
    if hasattr(last_message, 'content'):
        logger.debug(
            f"Last message content: {last_message.content[:200] if isinstance(last_message.content, str) else last_message.content}")

    # Select LLM per request
    llm_with_tools = _get_llm_with_tools(
        state.get("provider"), state.get("model"))

    # Sanitize messages to ensure all content is strings (required by some APIs like DeepSeek)
    sanitized_messages = _sanitize_messages(state["messages"])

    # Rate-limit handling: retry on Groq 429 errors with suggested wait
    # Import groq lazily to avoid hard dependency in environments where it's unavailable
    try:
        import re
        import groq  # type: ignore
    except Exception:
        re = None
        groq = None

    attempts = 0
    max_attempts = 3
    last_exc = None
    while attempts < max_attempts:
        try:
            response = llm_with_tools.invoke(sanitized_messages)
            return {"messages": [response]}
        except Exception as e:
            last_exc = e
            is_rate_limit = e.__class__.__name__ == "RateLimitError" or (
                groq is not None and isinstance(
                    e, getattr(groq, "RateLimitError", Exception))
            )
            if not is_rate_limit:
                raise
            # Parse suggested wait time from message, fallback to 5s
            wait_seconds = 5.0
            msg = str(e)
            if re is not None:
                m = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", msg)
                if m:
                    try:
                        wait_seconds = float(m.group(1))
                    except Exception:
                        pass
            logger.warning(
                f"Groq rate limit hit. Waiting {wait_seconds:.2f}s before retry ({attempts+1}/{max_attempts})."
            )
            time.sleep(wait_seconds)
            attempts += 1
    # If all retries failed, re-raise the last exception
    raise last_exc


def classify_query_complexity(state: AgentState) -> str:
    """Classify if query needs planning or can go straight to agent using LLM.

    Uses the LLM to intelligently determine query complexity.

    Returns:
        - "simple" for straightforward questions that don't need planning
        - "complex" for questions requiring planning and multi-step reasoning
    """
    question = state["question"]
    language = state["language"]

    # Create classification prompt
    if language == 'es':
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
        # Use lightweight LLM for classification
        llm = _get_llm_with_tools(state.get("provider"), state.get("model"))

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
                f"Query classified as {result.upper()} by fallback heuristic ({word_count} words)")
            return result

    except Exception as e:
        logger.warning(
            f"LLM classification failed ({e}), using fallback heuristic")
        # Fallback: word count heuristic
        word_count = len(question.split())
        result = "simple" if word_count < 10 else "complex"
        logger.info(
            f"Query classified as {result.upper()} by fallback ({word_count} words)")
        return result


def planning_node(state: AgentState) -> AgentState:
    """Planning node that analyzes the question and creates a search strategy.

    This node runs before tool execution to:
    1. Analyze the user's question
    2. Identify key concepts and search terms
    3. Plan which tools to use and in what order
    4. Store the plan for reference
    """
    logger.info(
        "Planning node: Analyzing question and creating search strategy...")

    llm_with_tools = _get_llm_with_tools(
        state.get("provider"), state.get("model"))

    question = state["question"]
    language = state["language"]

    # Create planning prompt with location context
    if language == 'es':
        planning_prompt = f"""Analiza esta pregunta del usuario y crea un plan de búsqueda específico para {LOCATION_CONTEXT['location']}.

CONTEXTO: Eres un asistente para {LOCATION_CONTEXT['organization']} en {LOCATION_CONTEXT['location']}.
Las áreas de enfoque incluyen: {', '.join(LOCATION_CONTEXT['focus_areas'])}

PREGUNTA: "{question}"

Tu tarea es:
1. Identificar los conceptos clave en la pregunta
2. Determinar si la pregunta es relevante para {LOCATION_CONTEXT['location']} (Rhode Island)
3. Identificar qué tipo de información se necesita (servicios locales, ubicación específica, etc.)
4. Sugerir qué herramientas usar en qué orden

Responde en este formato:
CONCEPTOS CLAVE: [lista los conceptos principales]
RELEVANCIA LOCAL: [es aplicable a {LOCATION_CONTEXT['location']}? Sí/No/Parcialmente]
TIPO DE INFORMACIÓN: [qué tipo de información busca el usuario]
PLAN DE BÚSQUEDA: [describe el orden de búsqueda recomendado]
BÚSQUEDA NECESITA CLARIFICACIÓN: [sí/no - ¿necesitamos más detalles del usuario?]
CONTEXTO UBICACIÓN: [si aplica, notas sobre la ubicación específica requerida]
"""
    else:
        planning_prompt = f"""Analyze this user question and create a search plan specific to {LOCATION_CONTEXT['location']}.

CONTEXT: You are an assistant for {LOCATION_CONTEXT['organization']} in {LOCATION_CONTEXT['location']}.
Focus areas include: {', '.join(LOCATION_CONTEXT['focus_areas'])}

QUESTION: "{question}"

Your task is:
1. Identify key concepts in the question
2. Determine if the question is relevant to {LOCATION_CONTEXT['location']} (Rhode Island)
3. Identify what type of information is needed (local services, specific location, etc.)
4. Suggest which tools to use and in what order

Respond in this format:
KEY CONCEPTS: [list the main concepts]
LOCAL RELEVANCE: [is it applicable to {LOCATION_CONTEXT['location']}? Yes/No/Partially]
INFORMATION TYPE: [what type of information the user is searching for]
SEARCH PLAN: [describe the recommended search order]
SEARCH NEEDS CLARIFICATION: [yes/no - do we need more details from the user?]
LOCATION CONTEXT: [if applicable, notes about the specific location required]
"""

    # Get planning from LLM
    try:
        planning_response = llm_with_tools.invoke([
            SystemMessage(content="You are a search strategy analyst. Analyze questions and create search plans." if language ==
                          'en' else "Eres un analista de estrategia de búsqueda. Analiza preguntas y crea planes de búsqueda."),
            HumanMessage(content=planning_prompt)
        ])

        plan = planning_response.content if hasattr(
            planning_response, 'content') else str(planning_response)
        logger.info(f"Search plan created: {plan[:200]}...")

        # Add plan to state
        return {
            "messages": state["messages"],
            "plan": plan
        }
    except Exception as e:
        logger.warning(f"Planning failed, continuing without plan: {e}")
        return {"plan": ""}


def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue or end."""
    last_message = state["messages"][-1]

    # Log whether this message has tool calls
    has_tool_calls = hasattr(
        last_message, "tool_calls") and last_message.tool_calls

    if not has_tool_calls:
        logger.info(
            f"Agent ended: No tool calls found. Final response type: {type(last_message).__name__}")
        if hasattr(last_message, 'content') and isinstance(last_message.content, str):
            logger.debug(
                f"Final response preview: {last_message.content[:150]}...")
        return END

    # Log tool calls that will be executed
    tool_names = [call.get('name') if isinstance(call, dict) else getattr(call, 'name', 'unknown')
                  for call in last_message.tool_calls]
    logger.info(f"Agent continuing with tool calls: {tool_names}")
    return "tools"


def check_for_empty_db_search(state: AgentState) -> bool:
    """Check if the most recent db_search tool call returned 0 documents.

    This helps detect when we should suggest clarification instead of
    immediately falling back to web search.
    """
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'name') and msg.name == 'db_search':
            # Check if the content indicates 0 documents
            content = msg.content if isinstance(
                msg.content, str) else str(msg.content)
            if 'found 0' in content.lower() or 'no documents' in content.lower():
                return True
    return False


# --- Build LangGraph ---
logger.info("Building LangGraph workflow...")
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("planning", planning_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

# Add conditional routing from START based on query complexity
# Simple queries skip planning and go straight to agent
workflow.add_conditional_edges(
    START,
    classify_query_complexity,
    {
        "simple": "agent",    # Simple queries: direct to agent
        "complex": "planning"  # Complex queries: plan first
    }
)

# Planning always goes to agent
workflow.add_edge("planning", "agent")

# Agent decides: continue with tools or end
workflow.add_conditional_edges("agent", should_continue, ["tools", END])

# Tools loop back to agent
workflow.add_edge("tools", "agent")

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
        table = str.maketrans('', '', string.punctuation + "¿¡")
        q_clean = q.translate(table)
        # Remove accents for robust matching

        def _unaccent(s: str) -> str:
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
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
                    k_clean in q_clean or q_clean in k_clean or
                    k_unaccent in q_unaccent or q_unaccent in k_unaccent
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
            "config": "/config"
        },
        "message": "Use the React frontend at http://localhost:3000 or call /ask endpoint directly"
    }


# --- Favicon endpoint removed - using separate React frontend ---


@app.get("/health")
async def health():
    """Simple healthcheck endpoint used by Docker Compose."""
    return {"status": "ok"}


@app.get("/test-db-search")
def test_db_search(query: str = "community resources"):
    """Test database search functionality and return diagnostic info.

    Args:
        query: Test query string (default: "community resources")

    Returns:
        Diagnostic information about the search operation
    """
    diagnostics = {}

    try:
        logger.info(f"Test DB Search: Query = '{query}'")

        # Step 1: Check if table exists and has data
        try:
            table_result = supabase.table('document_chunks').select(
                'id', count='exact').limit(1).execute()
            total_rows = table_result.count if hasattr(table_result, 'count') else len(
                table_result.data) if table_result.data else 0
            diagnostics['table_exists'] = True
            diagnostics['total_rows'] = total_rows
            logger.info(f"Test DB Search: Table has {total_rows} rows")
        except Exception as e:
            diagnostics['table_exists'] = False
            diagnostics['table_error'] = str(e)
            logger.error(f"Test DB Search: Table check failed: {e}")

        # Step 2: Check if embeddings exist and are non-null
        try:
            embedding_check = supabase.table('document_chunks').select(
                'id,embedding').limit(5).execute()
            if embedding_check.data:
                non_null_embeddings = sum(
                    1 for row in embedding_check.data if row.get('embedding') is not None)
                diagnostics['embeddings_exist'] = non_null_embeddings > 0
                diagnostics['sample_embedding_count'] = non_null_embeddings
                diagnostics['sample_size'] = len(embedding_check.data)

                # Check embedding dimension if we have one
                if non_null_embeddings > 0:
                    sample_embedding = next(
                        (row['embedding'] for row in embedding_check.data if row.get('embedding')), None)
                    if sample_embedding:
                        if isinstance(sample_embedding, list):
                            diagnostics['stored_embedding_dimension'] = len(
                                sample_embedding)
                        elif isinstance(sample_embedding, str):
                            # Might be stored as string, try to parse
                            try:
                                import json
                                parsed = json.loads(sample_embedding)
                                diagnostics['stored_embedding_dimension'] = len(
                                    parsed)
                            except:
                                diagnostics['stored_embedding_dimension'] = 'unknown (string format)'
                        else:
                            diagnostics[
                                'stored_embedding_dimension'] = f'unknown (type: {type(sample_embedding).__name__})'

                logger.info(
                    f"Test DB Search: {non_null_embeddings}/{len(embedding_check.data)} sample rows have embeddings")
            else:
                diagnostics['embeddings_exist'] = False
                diagnostics['embedding_check_error'] = 'No data returned'
        except Exception as e:
            diagnostics['embeddings_exist'] = False
            diagnostics['embedding_check_error'] = str(e)
            logger.error(f"Test DB Search: Embedding check failed: {e}")

        # Step 3: Check if RPC function exists
        try:
            # Try calling RPC with a simple test embedding (all zeros)
            test_embedding = [0.0] * 384
            rpc_test = supabase.rpc(
                "search_similar_documents",
                {
                    "query_embedding": test_embedding,
                    "match_threshold": 0.0,
                    "match_count": 1
                }
            ).execute()
            diagnostics['rpc_function_exists'] = True
            diagnostics['rpc_test_results'] = len(
                rpc_test.data) if rpc_test.data else 0
            logger.info(
                f"Test DB Search: RPC function exists and returned {diagnostics['rpc_test_results']} results with test embedding")
        except Exception as e:
            diagnostics['rpc_function_exists'] = False
            diagnostics['rpc_error'] = str(e)
            logger.error(f"Test DB Search: RPC function test failed: {e}")

        # Step 4: Generate embedding from query
        question_embedding = embedding_model.embed_query(query)
        diagnostics['query_embedding_dimension'] = len(question_embedding)
        logger.info(
            f"Test DB Search: Generated embedding dimension = {len(question_embedding)}")
        logger.info(
            f"Test DB Search: First 5 values = {question_embedding[:5]}")

        # Step 5: Try actual search with threshold=0.0
        test_threshold = 0.0
        logger.info(
            f"Test DB Search: Searching with threshold = {test_threshold}")

        result = supabase.rpc(
            "search_similar_documents",
            {
                "query_embedding": question_embedding,
                "match_threshold": test_threshold,
                "match_count": 10
            },
        ).execute()

        logger.info(
            f"Test DB Search: Found {len(result.data) if result.data else 0} results")
        diagnostics['search_results_found'] = len(
            result.data) if result.data else 0

        if result.data:
            # Show similarity scores
            similarities = [doc.get('similarity', 0) for doc in result.data]
            logger.info(f"Test DB Search: Similarity scores = {similarities}")

            return {
                "status": "success",
                "query": query,
                "diagnostics": diagnostics,
                "results_found": len(result.data),
                "similarity_range": {
                    "min": min(similarities),
                    "max": max(similarities),
                    "avg": sum(similarities) / len(similarities)
                },
                "sample_result": {
                    "content_preview": result.data[0].get('content', '')[:200],
                    "source_url": result.data[0].get('source_url', 'N/A'),
                    "similarity": result.data[0].get('similarity', 0)
                },
                "all_similarities": similarities
            }
        else:
            return {
                "status": "no_results",
                "query": query,
                "diagnostics": diagnostics,
                "message": "No results found. See diagnostics for details.",
                "recommendations": _get_recommendations(diagnostics)
            }

    except Exception as e:
        logger.error(f"Test DB Search Error: {e}")
        return {
            "status": "error",
            "query": query,
            "diagnostics": diagnostics,
            "error": str(e),
            "error_type": type(e).__name__
        }


def _get_recommendations(diagnostics: dict) -> list:
    """Generate recommendations based on diagnostic results."""
    recommendations = []

    if not diagnostics.get('table_exists'):
        recommendations.append(
            "❌ Table 'document_chunks' not found or not accessible. Check database connection and permissions.")

    if diagnostics.get('total_rows', 0) == 0:
        recommendations.append(
            "❌ Table is empty. Run the scraper to populate data: cd backend && uv run python src/utils/vector_loader.py")

    if not diagnostics.get('embeddings_exist'):
        recommendations.append(
            "❌ Embeddings are NULL in database. Re-run vector loader to generate embeddings.")

    if not diagnostics.get('rpc_function_exists'):
        recommendations.append(
            "❌ RPC function 'search_similar_documents' not found. Run: psql $DATABASE_URL -f backend/scripts/schema_install.sql")
    elif diagnostics.get('rpc_test_results', 0) == 0 and diagnostics.get('total_rows', 0) > 0:
        recommendations.append(
            "⚠️ RPC function exists but returns no results with test embedding. Check function implementation.")

    stored_dim = diagnostics.get('stored_embedding_dimension')
    query_dim = diagnostics.get('query_embedding_dimension')
    if stored_dim and query_dim and stored_dim != query_dim:
        recommendations.append(
            f"❌ DIMENSION MISMATCH: Stored embeddings are {stored_dim}D but query is {query_dim}D. Re-generate embeddings with correct model.")

    if diagnostics.get('search_results_found', 0) == 0 and diagnostics.get('rpc_test_results', 0) > 0:
        recommendations.append(
            "⚠️ RPC works with test embedding but not with query embedding. Check if embeddings were generated with the same model.")

    if not recommendations:
        recommendations.append(
            "✅ All diagnostics passed. Issue may be with query content or similarity calculation.")

    return recommendations


@app.get("/db-info")
def get_db_info():
    """Get basic database information for debugging.

    Returns:
        Database statistics and sample data
    """
    try:
        info = {}

        # Get row count
        try:
            count_result = supabase.table('document_chunks').select(
                'id', count='exact').limit(1).execute()
            info['total_rows'] = count_result.count if hasattr(count_result, 'count') else len(
                supabase.table('document_chunks').select('id').execute().data)
        except Exception as e:
            info['total_rows'] = f'error: {e}'

        # Get sample rows with embeddings
        try:
            sample_result = supabase.table('document_chunks').select(
                'id,source_url,chunk_index,embedding,content').limit(3).execute()
            if sample_result.data:
                samples = []
                for row in sample_result.data:
                    sample = {
                        'id': row.get('id'),
                        'source_url': row.get('source_url'),
                        'chunk_index': row.get('chunk_index'),
                        'content_preview': row.get('content', '')[:100] + '...' if row.get('content') else None,
                        'has_embedding': row.get('embedding') is not None,
                    }

                    # Try to get embedding dimension
                    if row.get('embedding'):
                        emb = row['embedding']
                        if isinstance(emb, list):
                            sample['embedding_dimension'] = len(emb)
                            sample['embedding_type'] = 'list'
                        elif isinstance(emb, str):
                            sample['embedding_type'] = 'string'
                            try:
                                import json
                                parsed = json.loads(emb)
                                sample['embedding_dimension'] = len(parsed)
                            except:
                                sample['embedding_dimension'] = 'parse_failed'
                        else:
                            sample['embedding_type'] = type(emb).__name__

                    samples.append(sample)

                info['sample_rows'] = samples
        except Exception as e:
            info['sample_error'] = str(e)

        # Check RPC function
        try:
            test_embedding = [0.0] * 384
            rpc_result = supabase.rpc(
                "search_similar_documents",
                {
                    "query_embedding": test_embedding,
                    "match_threshold": 0.0,
                    "match_count": 1
                }
            ).execute()
            info['rpc_function_works'] = True
            info['rpc_test_returned'] = len(
                rpc_result.data) if rpc_result.data else 0
        except Exception as e:
            info['rpc_function_works'] = False
            info['rpc_error'] = str(e)

        return {
            "status": "success",
            "database_info": info,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "expected_dimension": 384
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


@app.get("/ask")
async def ask_question(
    question: str | None = Query(default=None),
    query: str | None = Query(default=None),
    thread_id: str = "default",
    lang: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    """Handles Q&A requests from the UI or API using LangGraph agent"""
    # Accept both 'question' and legacy 'query' parameter names
    if question is None and query is not None:
        question = query
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question parameter cannot be empty. Use 'question' or 'query'.",
        )

    try:
        # Detect language unless explicitly provided
        if not lang:
            try:
                lang = detect(question)
            except LangDetectException:
                lang = "en"
                logger.warning(
                    "Language detection failed for question: '%s'. Defaulting to English.", question)
            # Heuristic override: treat as Spanish if question contains Spanish punctuation or accents
            if lang != 'es':
                if any(ch in question for ch in ['¿', '¡', 'á', 'é', 'í', 'ó', 'ú', 'ñ']):
                    lang = 'es'

        logger.info(
            f"\n--- New request received: '{question}' (Detected Language: {lang}, Thread: {thread_id}) ---")

        # Try static response first for deterministic FAQ handling in both languages
        local_static = _find_static_faq_answer(question, lang)
        if local_static:
            logger.info("Returning static FAQ answer (local matcher).")
            return {"answer": local_static, "thread_id": thread_id}
        # Fallback to tool-based static matcher (optional)
        try:
            static_answer = static_response_tool.invoke({
                "query": question,
                "language": lang
            })
            if static_answer:
                logger.info(
                    "Returning static FAQ answer without invoking agent (tool).")
                return {"answer": static_answer, "thread_id": thread_id}
        except Exception as static_exc:
            logger.warning(f"Static response check failed: {static_exc}")

        # Build system prompt based on language
        if lang == 'es':
            system_prompt = f"""
            Eres un asistente comunitario de {LOCATION_CONTEXT['organization']}, servicial y profesional.
            Ubicado en {LOCATION_CONTEXT['location']} ({LOCATION_CONTEXT['address']}).
            
            Tu objetivo es dar respuestas claras, concisas y precisas basadas en la información disponible
            sobre recursos de la comunidad de Rhode Island, especialmente relacionados con:
            {', '.join(LOCATION_CONTEXT['focus_areas'])}

            CONTEXTO IMPORTANTE:
            - Sirves a la comunidad de la cuenca {LOCATION_CONTEXT['service_area']}
            - Enfócate en recursos y programas locales de Rhode Island
            - Si una pregunta no es sobre {LOCATION_CONTEXT['location']}, ayuda a aclarar la ubicación correcta

            HERRAMIENTAS DISPONIBLES:
            1. static_response_tool: Preguntas frecuentes sobre Vecinita
            2. db_search: Busca en la base de datos interna de documentos comunitarios
            3. clarify_question: Hacer preguntas de seguimiento cuando la búsqueda en BD no da resultados
            4. web_search: Usa como ÚLTIMO RECURSO para buscar información externa

            REGLAS OBLIGATORIAS (DEBES SEGUIRLAS EXACTAMENTE):
            1. PRIMERO: SIEMPRE llama static_response_tool para CADA pregunta
            2. SEGUNDO: Si static_response_tool no da respuesta, DEBES llamar db_search (OBLIGATORIO)
            3. Si db_search retorna 0 documentos, DEBES llamar clarify_question para pedir más detalles
            4. SOLO usa web_search si db_search falla y clarify_question no obtiene respuesta
            5. NUNCA inventar respuestas sin usar las herramientas disponibles
            6. SIEMPRE citar fuentes con formato: "(Fuente: URL)" o "(Fuente: Documento interno)"
            7. Responde SIEMPRE en español

            IMPORTANTE: No describas lo que vas a hacer. HAZLO. Llama las herramientas directamente.
            """
        else:  # Default to English
            system_prompt = f"""
            You are a community assistant for {LOCATION_CONTEXT['organization']}, helpful and professional.
            Located in {LOCATION_CONTEXT['location']} ({LOCATION_CONTEXT['address']}).
            
            Your goal is to provide clear, concise, and accurate answers based on available information
            about community resources in Rhode Island, especially related to:
            {', '.join(LOCATION_CONTEXT['focus_areas'])}

            IMPORTANT CONTEXT:
            - You serve the {LOCATION_CONTEXT['service_area']} community
            - Focus on local Rhode Island resources and programs
            - If a question is not about {LOCATION_CONTEXT['location']}, help clarify the correct location

            AVAILABLE TOOLS:
            1. static_response_tool: Frequently asked questions about Vecinita
            2. db_search: Search the internal database of community documents
            3. clarify_question: Ask follow-up questions when database search returns no results
            4. web_search: Use as LAST RESORT for external information

            MANDATORY RULES (FOLLOW EXACTLY):
            1. FIRST: ALWAYS call static_response_tool for EVERY question
            2. SECOND: If static_response_tool has no answer, you MUST call db_search (MANDATORY)
            3. If db_search returns 0 documents, you MUST call clarify_question to ask for details
            4. ONLY use web_search if db_search fails and clarify_question gets no response
            5. NEVER make up answers without using available tools
            6. ALWAYS cite sources with format: "(Source: URL)" or "(Source: Internal Document)"
            7. Always respond in the user's language

            IMPORTANT: Do not describe what you will do. DO IT. Call the tools directly.
            """

        # Create messages for the agent
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]

        # Prepare state
        initial_state = {
            "messages": messages,
            "question": question,
            "language": lang,
            "provider": provider,
            "model": model,
        }

        # Configure graph execution with thread_id for conversation history
        config = {"configurable": {"thread_id": thread_id}}

        logger.info("Invoking LangGraph agent...")
        result = graph.invoke(initial_state, config)
        logger.info("Agent execution completed")

        # Extract the final answer from messages
        final_message = result["messages"][-1]
        answer = final_message.content if hasattr(
            final_message, "content") else str(final_message)

        logger.info(f"Agent response: {answer[:200]}...")

        # Extract sources from ToolMessage objects in the conversation history
        sources: list[dict] = []
        seen_urls = set()  # Deduplicate sources by URL

        logger.info(
            f"Extracting sources from {len(result['messages'])} messages in conversation history")

        for msg in result["messages"]:
            if not isinstance(msg, ToolMessage):
                continue

            tool_name = getattr(msg, 'name', None)
            content = msg.content

            logger.debug(
                f"Processing ToolMessage from tool: {tool_name}, content type: {type(content)}")

            # Parse JSON content if it's a string
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                    logger.debug(
                        f"Parsed JSON content, result type: {type(content)}, length: {len(content) if isinstance(content, list) else 'N/A'}")
                except (json.JSONDecodeError, ValueError):
                    logger.debug(
                        f"Failed to parse JSON content: {content[:100]}")
                    continue

            # Extract DB search results
            if tool_name == 'db_search' and isinstance(content, list):
                for d in content[:5]:
                    url = d.get("source_url") or ""
                    if url and url not in seen_urls:
                        seen_urls.add(url)

                        # Extract clean title from content by removing scraper metadata header
                        content_text = d.get("content", "")
                        clean_title = None

                        # Check if content starts with scraper metadata header
                        if content_text.startswith("DOCUMENTS_LOADED:"):
                            # Find the end of the metadata line (first newline)
                            lines = content_text.split('\n', 2)
                            if len(lines) >= 2:
                                # Use the first non-empty line after metadata as title
                                for line in lines[1:]:
                                    stripped = line.strip()
                                    if stripped and len(stripped) > 3:
                                        # Take first 100 chars as title
                                        clean_title = stripped[:100] + \
                                            ("..." if len(stripped) > 100 else "")
                                        break

                        # If no clean title extracted, try first line of content
                        if not clean_title and content_text:
                            first_line = content_text.split('\n')[0].strip()
                            if first_line and len(first_line) > 3:
                                clean_title = first_line[:100] + \
                                    ("..." if len(first_line) > 100 else "")

                        # Fallback to domain name or filename from URL
                        if not clean_title:
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(url)
                                # Try filename first
                                path_parts = parsed.path.rstrip('/').split('/')
                                if path_parts and path_parts[-1]:
                                    clean_title = path_parts[-1]
                                else:
                                    # Use domain
                                    clean_title = parsed.netloc or url.split(
                                        '/')[-1] or "Internal Document"
                            except:
                                clean_title = url.split(
                                    '/')[-1] or "Internal Document"

                        entry = {
                            "title": clean_title,
                            "url": url,
                            "type": "document",
                        }
                        lower = url.lower()
                        entry["isDownload"] = any(lower.endswith(ext) for ext in [
                            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"
                        ])
                        # Add position information if available
                        if 'chunk_index' in d:
                            entry['chunkIndex'] = d['chunk_index']
                        if 'char_start' in d:
                            entry['charStart'] = d['char_start']
                        if 'char_end' in d:
                            entry['charEnd'] = d['char_end']
                        if 'doc_index' in d:
                            entry['docIndex'] = d['doc_index']
                        # Add total_chunks for multi-chunk sources
                        if 'total_chunks' in d:
                            entry['totalChunks'] = d['total_chunks']
                        # Add metadata (includes link type, link source, loader type, etc.)
                        if 'metadata' in d and d['metadata']:
                            entry['metadata'] = d['metadata']
                        sources.append(entry)

            # Extract web search results
            elif tool_name == 'web_search' and isinstance(content, list):
                for r in content[:5]:
                    url = r.get("url") or ""
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        entry = {
                            "title": r.get("title") or url.split('/')[-1] or "Web Result",
                            "url": url,
                            "type": "link",
                            "isDownload": url.lower().endswith(".pdf"),
                        }
                        sources.append(entry)

        logger.info(f"Extracted {len(sources)} sources from tool calls")

        return {"answer": answer, "sources": sources, "thread_id": thread_id}

    except Exception as e:
        logger.error("Error processing question '%s': %s", question, str(e))
        logger.error("Full traceback:\n%s", traceback.format_exc())
        # Graceful handling of Groq rate limits: return a friendly message instead of 500
        try:
            import re
            import groq  # type: ignore
        except Exception:
            re = None
            groq = None
        is_rate_limit = e.__class__.__name__ == "RateLimitError" or (
            groq is not None and isinstance(
                e, getattr(groq, "RateLimitError", Exception))
        )
        if is_rate_limit:
            wait_seconds = 10.0
            msg = str(e)
            if re is not None:
                m = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", msg)
                if m:
                    try:
                        wait_seconds = float(m.group(1))
                    except Exception:
                        pass
            # Language-aware fallback
            if 'lang' in locals() and lang == 'es':
                fallback = (
                    f"El asistente está limitado por tasa temporalmente. Intenta nuevamente en {wait_seconds:.0f} segundos. "
                    "Si necesitas una descripción rápida: Vecinita es un asistente comunitario de preguntas y respuestas (Q&A)."
                )
            else:
                fallback = (
                    f"The assistant is temporarily rate limited. Please try again in {wait_seconds:.0f} seconds. "
                    "Quick summary: Vecinita is a community Q&A assistant."
                )
            return {"answer": fallback, "thread_id": thread_id}
        # Non-rate-limit errors: propagate as HTTP 500
        raise HTTPException(status_code=500, detail=str(e))


# --- Helper function for tracking tool execution in streaming ---
def _execute_agent_with_tool_progress(initial_state, config):
    """Execute agent and yield tool execution updates.

    Yields tuples of (tool_name, message) as tools are executed.
    """
    executed_tools = set()

    # Use stream mode to track execution
    for event in graph.stream(initial_state, config, stream_mode="updates"):
        if event:
            for node_name, node_update in event.items():
                if node_name == "tools" and node_update:
                    # Extract tool calls from ToolMessage results
                    messages_list = node_update.get("messages", [])
                    for msg in messages_list:
                        if hasattr(msg, 'name') and msg.name:
                            tool_name = msg.name
                            if tool_name not in executed_tools:
                                executed_tools.add(tool_name)
                                yield tool_name


@app.get("/ask-stream")
async def ask_question_stream(
    question: str | None = Query(default=None),
    query: str | None = Query(default=None),
    thread_id: str = "default",
    lang: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
    clarification_response: str | None = Query(default=None),
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
            # Detect language unless explicitly provided
            if not lang:
                try:
                    detected_lang = detect(question)
                    lang_local = detected_lang if detected_lang in [
                        'es', 'en'] else 'en'
                except LangDetectException:
                    lang_local = 'en'
                # Heuristic override: treat as Spanish if question contains Spanish punctuation or accents
                if lang_local != 'es':
                    if any(c in question for c in '¿¡áéíóúñü'):
                        lang_local = 'es'
            else:
                lang_local = lang

            logger.info(
                f"\n--- Streaming request received: '{question}' (Language: {lang_local}, Thread: {thread_id}) ---")

            # Yield thinking message for FAQ check
            msg = get_agent_thinking_message('static_response', lang_local)
            yield f'data: {json.dumps({"type": "thinking", "message": msg})}\n\n'

            # Try static response first
            local_static = _find_static_faq_answer(question, lang_local)
            if local_static:
                logger.info("Returning static FAQ answer (streaming).")
                yield f'data: {json.dumps({"type": "complete", "answer": local_static, "sources": [], "thread_id": thread_id, "plan": ""})}\n\n'
                return

            # Yield thinking message for analysis
            msg = get_agent_thinking_message('analyzing', lang_local)
            yield f'data: {json.dumps({"type": "thinking", "message": msg})}\n\n'

            # Build system prompt based on language
            if lang_local == 'es':
                system_prompt = """
Eres un asistente comunitario, servicial y profesional para el proyecto Vecinita.
Tu objetivo es dar respuestas claras, concisas y precisas basadas en la información disponible.

HERRAMIENTAS DISPONIBLES:
1. static_response_tool: Preguntas frecuentes sobre Vecinita
2. db_search: Busca en la base de datos interna de documentos comunitarios
3. clarify_question: Hacer preguntas de seguimiento cuando la búsqueda en BD no da resultados
4. web_search: Usa como ÚLTIMO RECURSO para buscar información externa

REGLAS OBLIGATORIAS (DEBES SEGUIRLAS EXACTAMENTE):
1. PRIMERO: SIEMPRE llama static_response_tool para CADA pregunta
2. SEGUNDO: Si static_response_tool no da respuesta, DEBES llamar db_search (OBLIGATORIO)
3. Si db_search retorna 0 documentos, DEBES llamar clarify_question para pedir más detalles
4. SOLO usa web_search si db_search falla y clarify_question no obtiene respuesta
5. NUNCA inventar respuestas sin usar las herramientas disponibles
6. SIEMPRE citar fuentes con formato: "(Fuente: URL)" o "(Fuente: Documento interno)"
7. Responde SIEMPRE en español

IMPORTANTE: No describas lo que vas a hacer. HAZLO. Llama las herramientas directamente.
"""
            else:  # Default to English
                system_prompt = """
You are a helpful and professional community assistant for the Vecinita project.
Your goal is to provide clear, concise, and accurate answers based on available information.

AVAILABLE TOOLS:
1. static_response_tool: Frequently asked questions about Vecinita
2. db_search: Search the internal database of community documents
3. clarify_question: Ask follow-up questions when database search returns no results
4. web_search: Use as LAST RESORT for external information

MANDATORY RULES (FOLLOW EXACTLY):
1. FIRST: ALWAYS call static_response_tool for EVERY question
2. SECOND: If static_response_tool has no answer, you MUST call db_search (MANDATORY)
3. If db_search returns 0 documents, you MUST call clarify_question to ask for details
4. ONLY use web_search if db_search fails and clarify_question gets no response
5. NEVER make up answers without using available tools
6. ALWAYS cite sources with format: "(Source: URL)" or "(Source: Internal Document)"
7. Always respond in the user's language

IMPORTANT: Do not describe what you will do. DO IT. Call the tools directly.
"""

            # Create messages for the agent
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=question)
            ]

            # If this is a clarification response, add it to the conversation
            if clarification_response:
                messages.append(HumanMessage(
                    content=f"Based on your questions, here is my clarification: {clarification_response}"))

            # Prepare state
            initial_state = {
                "messages": messages,
                "question": question,
                "language": lang_local,
                "provider": provider,
                "model": model,
                "plan": None,
            }

            # Configure graph execution with thread_id for conversation history
            config = {"configurable": {"thread_id": thread_id}}

            logger.info(
                "Invoking LangGraph agent with tool progress tracking (streaming)...")

            # Track which tools have been executed
            executed_tools = set()

            # Execute graph with streaming and track tool execution
            try:
                # Use streaming to track tool execution with friendly messages
                for tool_name in _execute_agent_with_tool_progress(initial_state, config):
                    if tool_name not in executed_tools:
                        executed_tools.add(tool_name)
                        tool_msg = get_agent_thinking_message(
                            tool_name, lang_local)
                        logger.info(f"Agent activity: {tool_name}")
                        yield f'data: {json.dumps({"type": "thinking", "message": tool_msg})}\n\n'

                # Get final result
                result = graph.invoke(initial_state, config)
            except Exception as e:
                logger.error(f"Graph invocation error: {e}")
                raise

            logger.info("Agent execution completed (streaming)")

            # Extract the final answer from messages
            final_message = result["messages"][-1]
            answer = final_message.content if hasattr(
                final_message, "content") else str(final_message)

            logger.info(f"Agent response (streaming): {answer[:200]}...")

            # Extract sources from ToolMessage objects
            sources: list[dict] = []
            seen_urls = set()

            logger.info(
                f"Extracting sources from {len(result['messages'])} messages in conversation history (streaming)")

            for msg in result["messages"]:
                # Check if this is a ToolMessage with db_search results
                if hasattr(msg, 'name') and msg.name == 'db_search':
                    try:
                        content = msg.content if isinstance(
                            msg.content, str) else str(msg.content)
                        docs = json.loads(
                            content) if content.strip().startswith('[') else []
                        for doc in docs:
                            url = doc.get('source_url', '')
                            if url and url not in seen_urls:
                                sources.append({
                                    "title": doc.get('content', '')[:60] + '...',
                                    "url": url,
                                    "type": "document",
                                    "similarity": doc.get('similarity', 0)
                                })
                                seen_urls.add(url)
                    except Exception:
                        pass

                # Check if this is a ToolMessage with web_search results
                elif hasattr(msg, 'name') and msg.name == 'web_search':
                    try:
                        content = msg.content if isinstance(
                            msg.content, str) else str(msg.content)
                        results = json.loads(
                            content) if content.strip().startswith('[') else []
                        for r in results:
                            url = r.get('url')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                entry = {
                                    "title": r.get("title") or url.split('/')[-1] or "Web Result",
                                    "url": url,
                                    "type": "link",
                                    "isDownload": url.lower().endswith(".pdf"),
                                }
                                sources.append(entry)
                    except Exception:
                        pass

            logger.info(
                f"Extracted {len(sources)} sources from tool calls (streaming)")

            # Extract plan if available
            plan = result.get("plan", "")

            # Yield complete response
            yield f'data: {json.dumps({"type": "complete", "answer": answer, "sources": sources, "thread_id": thread_id, "plan": plan})}\n\n'

        except Exception as e:
            logger.error("Error in streaming endpoint '%s': %s",
                         question, str(e))
            logger.error("Full traceback:\n%s", traceback.format_exc())

            # Handle rate limits gracefully
            try:
                import re
                import groq  # type: ignore
            except Exception:
                re = None
                groq = None

            is_rate_limit = e.__class__.__name__ == "RateLimitError" or (
                groq is not None and isinstance(
                    e, getattr(groq, "RateLimitError", Exception))
            )

            if is_rate_limit:
                fallback = "Service temporarily rate limited. Please try again in a moment."
            else:
                fallback = f"Error processing question: {str(e)}"

            yield f'data: {json.dumps({"type": "error", "message": fallback})}\n\n'

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})


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
    """Set provider/model if not locked. Developers can freeze via env or file."""
    if CURRENT_SELECTION.get("locked"):
        raise HTTPException(status_code=403, detail="Model selection is locked")

    available = config()
    providers = [p["key"] for p in available["providers"]]
    if selection.provider not in providers:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {selection.provider}")

    # Validate model if provided
    if selection.model:
        avail_models = available["models"].get(selection.provider, [])
        if selection.model not in avail_models:
            raise HTTPException(status_code=400, detail=f"Unsupported model for {selection.provider}: {selection.model}")

    # Save selection (file + in-memory)
    _save_model_selection_to_file(selection.provider.lower(), selection.model, selection.lock)
    return {"status": "ok", "current": CURRENT_SELECTION}


@app.get("/config")
def config():
    """Expose available providers/models based on environment for frontend discovery."""
    providers = []
    models = {}
    # DeepSeek (default/primary)
    if deepseek_api_key:
        providers.append({"key": "deepseek", "label": "DeepSeek"})
        models["deepseek"] = ["deepseek-chat", "deepseek-reasoner"]
    # Groq (Llama)
    if groq_api_key:
        providers.append({"key": "groq", "label": "Groq (Llama)"})
        models["groq"] = ["llama-3.1-8b-instant"]
    # OpenAI if key present
    if openai_api_key:
        providers.append({"key": "openai", "label": "OpenAI"})
        models["openai"] = ["gpt-4o-mini"]
    # Llama via Ollama
    if ollama_base_url:
        providers.append({"key": "llama", "label": "Llama (Local)"})
        models["llama"] = [ollama_model or "llama3.2"]
    return {"providers": providers, "models": models}


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

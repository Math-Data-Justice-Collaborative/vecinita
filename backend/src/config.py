"""
Central configuration for the Vecinita backend.

Single source of truth for embedding model, LLM provider chain,
and runtime feature flags. Import from here — never hardcode model
names or provider strings in other modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Embedding (must be consistent across indexing AND query-time)
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
EMBEDDING_SERVICE_URL: str = os.getenv(
    "EMBEDDING_SERVICE_URL", "http://embedding-service:8001"
)

# ---------------------------------------------------------------------------
# LLM Provider chain  (Ollama → DeepSeek → OpenAI → error)
# Groq / X.AI / Twitter AI intentionally excluded.
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str | None = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

DEEPSEEK_API_KEY: str | None = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL: str = os.getenv(
    "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
)
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "ollama").lower()

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# ---------------------------------------------------------------------------
# Guardrails AI feature flags
# Disable individual guards via env without redeploying.
# ---------------------------------------------------------------------------
GUARDRAILS_ENABLED: bool = os.getenv("GUARDRAILS_ENABLED", "true").lower() in ("1", "true", "yes")
GUARDRAILS_PROMPT_INJECTION: bool = os.getenv("GUARDRAILS_PROMPT_INJECTION", "true").lower() in ("1", "true", "yes")
GUARDRAILS_TOPIC_RELEVANCE: bool = os.getenv("GUARDRAILS_TOPIC_RELEVANCE", "true").lower() in ("1", "true", "yes")
GUARDRAILS_PII: bool = os.getenv("GUARDRAILS_PII", "true").lower() in ("1", "true", "yes")
GUARDRAILS_TOXICITY: bool = os.getenv("GUARDRAILS_TOXICITY", "true").lower() in ("1", "true", "yes")
GUARDRAILS_HALLUCINATION: bool = os.getenv("GUARDRAILS_HALLUCINATION", "true").lower() in ("1", "true", "yes")

# Seed topic list for the topic-relevance guardrail.
# Override via GUARDRAILS_TOPICS env var (comma-separated).
_default_topics = (
    "water,watershed,environment,climate,habitat,restoration,"
    "community,health,rhode island,providence,woonasquatucket,"
    "pollution,air quality,recycling,sustainability,flood,stormwater,"
    "wildlife,green space,conservation,education,volunteer"
)
GUARDRAILS_TOPIC_LIST: list[str] = [
    t.strip()
    for t in os.getenv("GUARDRAILS_TOPICS", _default_topics).split(",")
    if t.strip()
]

# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
ADMIN_TOKEN: str | None = os.getenv("ADMIN_TOKEN")  # optional extra gate
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).parent
DATA_DIR: Path = BASE_DIR.parent / "data"

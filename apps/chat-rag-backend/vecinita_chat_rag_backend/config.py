"""ChatRAG backend settings (docs/config-spec.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from vecinita_rag.cache import (
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_CACHE_TTL_S,
    DEFAULT_SEMANTIC_THRESHOLD,
)
from vecinita_rag.packing import DEFAULT_CONTEXT_MAX_CHARS, PackerMode
from vecinita_rag.pipeline_knobs import (
    MAX_MULTI_QUERY_COUNT,
    MIN_CONTEXT_MAX_CHARS,
    MIN_MULTI_QUERY_COUNT,
)
from vecinita_rag.rerank import DEFAULT_CE_MODEL_ID, DEFAULT_CE_TOP_N
from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_MAX_TOKENS,
    DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
    DEFAULT_EVAL_MODEL_ID,
    DEFAULT_EVAL_SYSTEM_PROMPT,
    DEFAULT_EVAL_TEMPERATURE,
    DEFAULT_EVAL_TOP_K,
)

_MIN_MULTI_QUERY_COUNT = MIN_MULTI_QUERY_COUNT
_MAX_MULTI_QUERY_COUNT = MAX_MULTI_QUERY_COUNT
_MIN_CONTEXT_MAX_CHARS = MIN_CONTEXT_MAX_CHARS
_MIN_CACHE_TTL_S = 60
_MAX_CACHE_TTL_S = 86400
_MIN_CACHE_MAX_ENTRIES = 16
_MAX_CACHE_MAX_ENTRIES = 100000
_MIN_CACHE_SEMANTIC_THRESHOLD = 0.5
_MAX_CACHE_SEMANTIC_THRESHOLD = 1.0
_MAX_CE_TOP_N = 50
_MIN_REFINE_COUNT = 1
_MAX_REFINE_COUNT = 3
_MIN_OUTPUT_VERIFY_MIN = 0.0
_MAX_OUTPUT_VERIFY_MIN = 1.0


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return int(raw)


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return float(raw)


def _str_env(name: str, default: str) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw


def _bool_env(name: str, default: bool) -> bool:  # noqa: FBT001  # internal helper mirrors _int_env/_float_env positional default style
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _rag_packer_env(name: str, default: PackerMode) -> PackerMode:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value == "p1":
        return "p1"
    if value == "p3":
        return "p3"
    msg = f"{name} must be 'p1' or 'p3' (got {raw!r})"
    raise ValueError(msg)


def _validate_f42_rag_knobs(
    *,
    rag_multi_query_count: int,
    rag_packer: PackerMode,
    rag_context_max_chars: int,
) -> None:
    if not (_MIN_MULTI_QUERY_COUNT <= rag_multi_query_count <= _MAX_MULTI_QUERY_COUNT):
        msg = (
            "VECINITA_RAG_MULTI_QUERY_COUNT must be between "
            f"{_MIN_MULTI_QUERY_COUNT} and {_MAX_MULTI_QUERY_COUNT}"
        )
        raise ValueError(msg)
    if rag_packer not in ("p1", "p3"):
        msg = f"VECINITA_RAG_PACKER must be 'p1' or 'p3' (got {rag_packer!r})"
        raise ValueError(msg)
    if rag_context_max_chars < _MIN_CONTEXT_MAX_CHARS:
        msg = f"VECINITA_RAG_CONTEXT_MAX_CHARS must be >= {_MIN_CONTEXT_MAX_CHARS}"
        raise ValueError(msg)


def _validate_f43_rag_cache_knobs(
    *,
    rag_cache_ttl_s: int,
    rag_cache_max_entries: int,
    rag_cache_semantic_threshold: float,
) -> None:
    if not (_MIN_CACHE_TTL_S <= rag_cache_ttl_s <= _MAX_CACHE_TTL_S):
        msg = f"VECINITA_RAG_CACHE_TTL_S must be between {_MIN_CACHE_TTL_S} and {_MAX_CACHE_TTL_S}"
        raise ValueError(msg)
    if not (_MIN_CACHE_MAX_ENTRIES <= rag_cache_max_entries <= _MAX_CACHE_MAX_ENTRIES):
        msg = (
            "VECINITA_RAG_CACHE_MAX_ENTRIES must be between "
            f"{_MIN_CACHE_MAX_ENTRIES} and {_MAX_CACHE_MAX_ENTRIES}"
        )
        raise ValueError(msg)
    if not (
        _MIN_CACHE_SEMANTIC_THRESHOLD
        <= rag_cache_semantic_threshold
        <= _MAX_CACHE_SEMANTIC_THRESHOLD
    ):
        msg = (
            "VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD must be between "
            f"{_MIN_CACHE_SEMANTIC_THRESHOLD} and {_MAX_CACHE_SEMANTIC_THRESHOLD}"
        )
        raise ValueError(msg)


def _validate_f45_rag_ce_knobs(*, top_k: int, rag_rerank_ce_top_n: int) -> None:
    if not (top_k <= rag_rerank_ce_top_n <= _MAX_CE_TOP_N):
        msg = f"VECINITA_RAG_RERANK_CE_TOP_N must be between top_k ({top_k}) and {_MAX_CE_TOP_N}"
        raise ValueError(msg)


def _validate_f81_query_refine_knobs(*, rag_query_refine_count: int) -> None:
    if not (_MIN_REFINE_COUNT <= rag_query_refine_count <= _MAX_REFINE_COUNT):
        msg = (
            f"VECINITA_RAG_QUERY_REFINE_COUNT must be between "
            f"{_MIN_REFINE_COUNT} and {_MAX_REFINE_COUNT}"
        )
        raise ValueError(msg)


def _validate_f82_output_verify_knobs(*, rag_output_verify_min: float) -> None:
    if not (_MIN_OUTPUT_VERIFY_MIN <= rag_output_verify_min <= _MAX_OUTPUT_VERIFY_MIN):
        msg = (
            "VECINITA_RAG_OUTPUT_VERIFY_MIN must be between "
            f"{_MIN_OUTPUT_VERIFY_MIN} and {_MAX_OUTPUT_VERIFY_MIN}"
        )
        raise ValueError(msg)


def _validate_f45_rerank_url(*, rag_rerank_ce: bool, rerank_url: str | None) -> None:
    if rag_rerank_ce and not rerank_url:
        msg = "VECINITA_MODAL_RERANK_URL is required when VECINITA_RAG_RERANK_CE=true"
        raise ValueError(msg)


@dataclass(frozen=True)
class ChatRagSettings:
    """Runtime settings for retrieval, embedding, and LLM upstreams."""

    database_url: str
    top_k: int
    embed_url: str | None
    llm_url: str | None
    request_timeout_s: float
    min_retrieval_score: float = 0.2
    chat_max_tokens: int = 256
    browse_page_size: int = 20
    internal_write_url: str | None = None
    internal_api_key: str | None = None
    stats_enabled: bool = True
    llm_model_id: str | None = None
    fallback_top_k: int = DEFAULT_EVAL_TOP_K
    fallback_min_retrieval_score: float = DEFAULT_EVAL_MIN_RETRIEVAL_SCORE
    fallback_system_prompt: str = DEFAULT_EVAL_SYSTEM_PROMPT
    fallback_max_tokens: int = DEFAULT_EVAL_MAX_TOKENS
    fallback_temperature: float = DEFAULT_EVAL_TEMPERATURE
    fallback_model_id: str = DEFAULT_EVAL_MODEL_ID
    rag_multi_query: bool = True
    rag_multi_query_count: int = 3
    rag_packer: PackerMode = "p3"
    rag_context_max_chars: int = DEFAULT_CONTEXT_MAX_CHARS
    rag_cache: bool = True
    rag_cache_ttl_s: int = DEFAULT_CACHE_TTL_S
    rag_cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
    rag_cache_semantic: bool = True
    rag_cache_semantic_threshold: float = DEFAULT_SEMANTIC_THRESHOLD
    rag_soft_language_fallback: bool = False
    rag_rerank_ce: bool = False
    rag_rerank_ce_model: str = DEFAULT_CE_MODEL_ID
    rag_rerank_ce_top_n: int = DEFAULT_CE_TOP_N
    rerank_url: str | None = None
    rag_query_refine: bool = False
    rag_query_refine_count: int = 2
    rag_output_verify: bool = False
    rag_output_verify_min: float = 1.0
    # F65 / ADR-047 energy heuristic knobs
    energy_gpu_tdp_w: float = 70.0
    energy_gpu_util: float = 0.5
    energy_gco2e_per_kwh: float = 386.0
    energy_car_gco2e_per_km: float = 251.0

    @classmethod
    def from_env(cls) -> ChatRagSettings:
        """Load settings from process environment variables."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            msg = "DATABASE_URL is required for ChatRAG backend"
            raise RuntimeError(msg)
        top_k = _int_env("VECINITA_TOP_K", 8)
        rag_multi_query_count = _int_env("VECINITA_RAG_MULTI_QUERY_COUNT", 3)
        rag_packer: PackerMode = _rag_packer_env("VECINITA_RAG_PACKER", "p3")
        rag_context_max_chars = _int_env(
            "VECINITA_RAG_CONTEXT_MAX_CHARS",
            DEFAULT_CONTEXT_MAX_CHARS,
        )
        _validate_f42_rag_knobs(
            rag_multi_query_count=rag_multi_query_count,
            rag_packer=rag_packer,
            rag_context_max_chars=rag_context_max_chars,
        )
        rag_cache_ttl_s = _int_env("VECINITA_RAG_CACHE_TTL_S", DEFAULT_CACHE_TTL_S)
        rag_cache_max_entries = _int_env(
            "VECINITA_RAG_CACHE_MAX_ENTRIES",
            DEFAULT_CACHE_MAX_ENTRIES,
        )
        rag_cache_semantic_threshold = _float_env(
            "VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD",
            DEFAULT_SEMANTIC_THRESHOLD,
        )
        _validate_f43_rag_cache_knobs(
            rag_cache_ttl_s=rag_cache_ttl_s,
            rag_cache_max_entries=rag_cache_max_entries,
            rag_cache_semantic_threshold=rag_cache_semantic_threshold,
        )
        rag_rerank_ce_top_n = _int_env("VECINITA_RAG_RERANK_CE_TOP_N", DEFAULT_CE_TOP_N)
        _validate_f45_rag_ce_knobs(top_k=top_k, rag_rerank_ce_top_n=rag_rerank_ce_top_n)
        rag_rerank_ce = _bool_env("VECINITA_RAG_RERANK_CE", default=False)
        rerank_url = os.environ.get("VECINITA_MODAL_RERANK_URL")
        _validate_f45_rerank_url(rag_rerank_ce=rag_rerank_ce, rerank_url=rerank_url)
        rag_query_refine_count = _int_env("VECINITA_RAG_QUERY_REFINE_COUNT", 2)
        _validate_f81_query_refine_knobs(rag_query_refine_count=rag_query_refine_count)
        rag_output_verify_min = _float_env("VECINITA_RAG_OUTPUT_VERIFY_MIN", 1.0)
        _validate_f82_output_verify_knobs(rag_output_verify_min=rag_output_verify_min)
        return cls(
            database_url=_normalize_database_url(database_url),
            top_k=top_k,
            min_retrieval_score=_float_env("VECINITA_MIN_RETRIEVAL_SCORE", 0.2),
            chat_max_tokens=_int_env("VECINITA_CHAT_MAX_TOKENS", 256),
            browse_page_size=_int_env("VECINITA_BROWSE_PAGE_SIZE", 20),
            embed_url=os.environ.get("VECINITA_MODAL_EMBED_URL"),
            llm_url=os.environ.get("VECINITA_MODAL_LLM_URL"),
            request_timeout_s=float(os.environ.get("VECINITA_REQUEST_TIMEOUT_S", "120")),
            internal_write_url=os.environ.get("VECINITA_INTERNAL_WRITE_URL"),
            internal_api_key=os.environ.get("VECINITA_INTERNAL_API_KEY"),
            stats_enabled=_bool_env("VECINITA_STATS_ENABLED", default=True),
            llm_model_id=os.environ.get("VECINITA_LLM_MODEL_ID")
            or os.environ.get("VECINITA_OLLAMA_MODEL_ID", DEFAULT_EVAL_MODEL_ID),
            fallback_top_k=_int_env("VECINITA_RAG_CONFIG_FALLBACK_TOP_K", DEFAULT_EVAL_TOP_K),
            fallback_min_retrieval_score=_float_env(
                "VECINITA_RAG_CONFIG_FALLBACK_MIN_RETRIEVAL_SCORE",
                DEFAULT_EVAL_MIN_RETRIEVAL_SCORE,
            ),
            fallback_system_prompt=_str_env(
                "VECINITA_RAG_CONFIG_FALLBACK_SYSTEM_PROMPT",
                DEFAULT_EVAL_SYSTEM_PROMPT,
            ),
            fallback_max_tokens=_int_env(
                "VECINITA_RAG_CONFIG_FALLBACK_MAX_TOKENS",
                DEFAULT_EVAL_MAX_TOKENS,
            ),
            fallback_temperature=_float_env(
                "VECINITA_RAG_CONFIG_FALLBACK_TEMPERATURE",
                DEFAULT_EVAL_TEMPERATURE,
            ),
            fallback_model_id=os.environ.get(
                "VECINITA_RAG_CONFIG_FALLBACK_MODEL_ID",
                DEFAULT_EVAL_MODEL_ID,
            ),
            rag_multi_query=_bool_env("VECINITA_RAG_MULTI_QUERY", default=True),
            rag_multi_query_count=rag_multi_query_count,
            rag_packer=rag_packer,
            rag_context_max_chars=rag_context_max_chars,
            rag_cache=_bool_env("VECINITA_RAG_CACHE", default=True),
            rag_cache_ttl_s=rag_cache_ttl_s,
            rag_cache_max_entries=rag_cache_max_entries,
            rag_cache_semantic=_bool_env("VECINITA_RAG_CACHE_SEMANTIC", default=True),
            rag_cache_semantic_threshold=rag_cache_semantic_threshold,
            rag_soft_language_fallback=_bool_env(
                "VECINITA_RAG_SOFT_LANGUAGE_FALLBACK",
                default=False,
            ),
            rag_rerank_ce=rag_rerank_ce,
            rag_rerank_ce_model=_str_env(
                "VECINITA_RAG_RERANK_CE_MODEL",
                DEFAULT_CE_MODEL_ID,
            ),
            rag_rerank_ce_top_n=rag_rerank_ce_top_n,
            rerank_url=rerank_url,
            rag_query_refine=_bool_env("VECINITA_RAG_QUERY_REFINE", default=False),
            rag_query_refine_count=rag_query_refine_count,
            rag_output_verify=_bool_env("VECINITA_RAG_OUTPUT_VERIFY", default=False),
            rag_output_verify_min=rag_output_verify_min,
            energy_gpu_tdp_w=_float_env("VECINITA_ENERGY_GPU_TDP_W", 70.0),
            energy_gpu_util=_float_env("VECINITA_ENERGY_GPU_UTIL", 0.5),
            energy_gco2e_per_kwh=_float_env("VECINITA_ENERGY_GCO2E_PER_KWH", 386.0),
            energy_car_gco2e_per_km=_float_env("VECINITA_ENERGY_CAR_GCO2E_PER_KM", 251.0),
        )

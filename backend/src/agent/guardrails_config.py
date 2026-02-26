"""Guardrails configuration for Vecinita.

This module uses the Guardrails AI Hub SDK when available and falls back to
local deterministic checks when Hub validators are unavailable.

Goals:
- block prompt-injection and DB-attack attempts at input time
- optionally redact PII in user input
- optionally block toxic output
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

_HUB_INPUT_GUARD = None
_HUB_OUTPUT_GUARD = None
_HUB_INITIALIZED = False

# ---------------------------------------------------------------------------
# Lazy import helpers — graceful degradation if guardrails not installed
# ---------------------------------------------------------------------------

def _try_import_guardrails():
    try:
        import guardrails as grd  # noqa: F401
        return grd
    except Exception as exc:
        logger.warning(
            "Guardrails SDK unavailable (%s). Falling back to local guardrails checks.",
            exc,
        )
        return None


def _configure_hub_api_key() -> None:
    """Ensure the Guardrails SDK can see an API key if provided by env."""
    # Prefer standard Guardrails env var, fallback to project-specific alias.
    hub_key = os.getenv("GUARDRAILS_API_KEY") or os.getenv("GUARDRAILS_AI_API_KEY")
    if hub_key and not os.getenv("GUARDRAILS_API_KEY"):
        os.environ["GUARDRAILS_API_KEY"] = hub_key


def _safe_install_validator(grd: Any, uri_candidates: list[str], attr_candidates: list[str]):
    """Try installing a hub validator and returning its class.

    Returns the validator class or None.
    """
    for uri in uri_candidates:
        try:
            module = grd.install(uri, install_local_models=False, quiet=True)
            for attr in attr_candidates:
                validator_cls = getattr(module, attr, None)
                if validator_cls is not None:
                    logger.info(f"[GUARDRAILS] Loaded validator {attr} from {uri}")
                    return validator_cls
        except SystemExit as exc:
            logger.warning(f"[GUARDRAILS] Validator install exited for {uri}: {exc}")
        except Exception as exc:
            logger.warning(f"[GUARDRAILS] Failed to install {uri}: {exc}")
    return None


def _build_hub_guards() -> tuple[Any, Any]:
    """Build Guardrails input/output guards from Hub validators.

    If validators cannot be installed, returns (None, None).
    """
    grd = _try_import_guardrails()
    if grd is None:
        return None, None

    _configure_hub_api_key()

    try:
        input_guard = grd.Guard()
        output_guard = None

        from src.config import GUARDRAILS_PII

        if GUARDRAILS_PII:
            detect_pii_cls = _safe_install_validator(
                grd,
                uri_candidates=[
                    "hub://guardrails/detect_pii",
                    "hub://guardrails/pii",
                ],
                attr_candidates=["DetectPII", "PIIFilter", "PiiFilter"],
            )
            if detect_pii_cls is not None:
                try:
                    input_guard = input_guard.use(
                        detect_pii_cls(
                            pii_entities=[
                                "EMAIL_ADDRESS",
                                "PHONE_NUMBER",
                                "US_SOCIAL_SECURITY_NUMBER",
                                "CREDIT_CARD",
                            ],
                            on_fail="fix",
                        )
                    )
                except TypeError:
                    input_guard = input_guard.use(detect_pii_cls())

        return input_guard, output_guard
    except SystemExit as exc:
        logger.warning(f"[GUARDRAILS] Hub guard initialization exited: {exc}")
        return None, None
    except Exception as exc:
        logger.warning(f"[GUARDRAILS] Hub guard initialization failed: {exc}")
        return None, None


def _get_hub_guards() -> tuple[Any, Any]:
    """Initialize Hub guards once and return them."""
    global _HUB_INITIALIZED, _HUB_INPUT_GUARD, _HUB_OUTPUT_GUARD

    if not _HUB_INITIALIZED:
        _HUB_INPUT_GUARD, _HUB_OUTPUT_GUARD = _build_hub_guards()
        _HUB_INITIALIZED = True

    return _HUB_INPUT_GUARD, _HUB_OUTPUT_GUARD


# ---------------------------------------------------------------------------
# Known prompt-injection patterns
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"forget\s+(all\s+)?previous\s+instructions?",
    r"you\s+are\s+now\s+(a\s+)?(?!vecinita)",  # "you are now X" (not Vecinita)
    r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(?!vecinita)",
    r"jailbreak",
    r"dan\s+mode",
    r"pretend\s+(you(\s+are|\s+have)|to\s+be)",
    r"override\s+(your\s+)?(system\s+)?prompt",
    r"disregard\s+(all\s+)?previous",
    r"system\s*:\s*you",  # injected system turn
    r"<\|.*?\|>",  # special token injection
]
_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    re.IGNORECASE | re.UNICODE,
)

_SQLI_PATTERNS = [
    r"\b(drop|truncate|alter|delete|insert|update|grant|revoke)\b\s+\b(table|database|schema|role|user)\b",
    r"\bunion\b\s+\bselect\b",
    r"\bor\b\s+1\s*=\s*1",
    r"\band\b\s+1\s*=\s*1",
    r"--",
    r"/\*.*?\*/",
    r";\s*(select|drop|delete|insert|update)",
    r"\binformation_schema\b",
    r"\bpg_sleep\s*\(",
    r"\bxp_cmdshell\b",
]
_SQLI_RE = re.compile("|".join(_SQLI_PATTERNS), re.IGNORECASE | re.UNICODE)


# ---------------------------------------------------------------------------
# PII patterns (lightweight regex, not ML-based — fast, no external call)
# ---------------------------------------------------------------------------
_PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "phone_us": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
}


def _contains_pii(text: str) -> tuple[bool, list[str]]:
    """Return (found, list_of_pii_types_detected)."""
    found = []
    for pii_type, pattern in _PII_PATTERNS.items():
        if pattern.search(text):
            found.append(pii_type)
    return bool(found), found


# ---------------------------------------------------------------------------
# Toxicity keyword list (lightweight blocklist — replace with ML model later)
# ---------------------------------------------------------------------------
_TOXIC_WORDS = re.compile(
    r"\b(fuck|shit|asshole|bitch|cunt|damn|bastard|nigger|faggot|kill yourself|kys)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Topic relevance check
# ---------------------------------------------------------------------------
def _is_topic_relevant(text: str, topic_list: list[str]) -> bool:
    """Return True if at least one corpus topic keyword appears in the text."""
    lower = text.lower()
    return any(topic.lower() in lower for topic in topic_list)


# ---------------------------------------------------------------------------
# Public validation functions
# (Used by agent/graph.py — not wrapped in a Guard class to avoid hard dep)
# ---------------------------------------------------------------------------

class GuardResult:
    """Lightweight result object returned by validate_input / validate_output."""

    def __init__(self, passed: bool, reason: str = "", redacted: str | None = None):
        self.passed = passed
        self.reason = reason
        self.redacted = redacted  # sanitised version of the text, if applicable

    def __bool__(self):
        return self.passed


def validate_input(text: str) -> GuardResult:
    """
    Run all enabled input guards against user text.

    Returns GuardResult(passed=False, reason=...) if any guard fails.
    The agent should short-circuit and return reason to the user directly.
    """
    from src.config import (
        GUARDRAILS_ENABLED,
        GUARDRAILS_PROMPT_INJECTION,
        GUARDRAILS_PII,
        GUARDRAILS_TOPIC_RELEVANCE,
        GUARDRAILS_TOPIC_LIST,
    )

    if not GUARDRAILS_ENABLED:
        return GuardResult(passed=True)

    # 1. Prompt injection / jailbreak detection
    if GUARDRAILS_PROMPT_INJECTION and _INJECTION_RE.search(text):
        logger.warning(f"[GUARDRAILS] Prompt injection detected: {text[:120]!r}")
        return GuardResult(
            passed=False,
            reason=(
                "I'm not able to process that request. "
                "Please ask me about the Woonasquatucket River Watershed or related topics."
            ),
        )

    # 1b. SQL / DB attack detection
    if _SQLI_RE.search(text):
        logger.warning(f"[GUARDRAILS] SQL/DB attack-like input detected: {text[:120]!r}")
        return GuardResult(
            passed=False,
            reason=(
                "I can't help with database access, schema manipulation, or injection-style requests. "
                "Please ask a normal information question instead."
            ),
        )

    # 2. Guardrails Hub SDK input validation (PII redaction, etc.)
    hub_input_guard, _ = _get_hub_guards()
    if hub_input_guard is not None:
        try:
            outcome = hub_input_guard.validate(text)
            validation_passed = bool(getattr(outcome, "validation_passed", True))
            validated_output = getattr(outcome, "validated_output", text)

            if not validation_passed:
                return GuardResult(
                    passed=False,
                    reason=(
                        "Your request did not pass safety validation. "
                        "Please rephrase without unsafe or sensitive content."
                    ),
                )

            if isinstance(validated_output, str) and validated_output != text:
                return GuardResult(passed=True, redacted=validated_output)
        except SystemExit as exc:
            logger.warning(f"[GUARDRAILS] Hub input validation exited, using local fallback: {exc}")
        except Exception as exc:
            logger.warning(f"[GUARDRAILS] Hub input validation failed, using local fallback: {exc}")

    # 3. Local PII fallback — redact rather than block
    if GUARDRAILS_PII:
        found_pii, pii_types = _contains_pii(text)
        if found_pii:
            logger.info(f"[GUARDRAILS] PII detected in input ({pii_types}). Redacting.")
            redacted = text
            for pii_type, pattern in _PII_PATTERNS.items():
                if pii_type in pii_types:
                    redacted = pattern.sub(f"[{pii_type.upper()}_REDACTED]", redacted)
            # Allow the request through with redacted text
            return GuardResult(passed=True, redacted=redacted)

    # 4. Topic relevance — only block if question is clearly off-topic
    #    (short/greeting messages are always allowed)
    if GUARDRAILS_TOPIC_RELEVANCE and len(text.split()) > 5:
        if not _is_topic_relevant(text, GUARDRAILS_TOPIC_LIST):
            logger.info(f"[GUARDRAILS] Off-topic query: {text[:120]!r}")
            return GuardResult(
                passed=False,
                reason=(
                    "I can only answer questions related to the Woonasquatucket River Watershed, "
                    "environmental topics in Rhode Island, and related community resources. "
                    "Please ask me something related to those areas."
                ),
            )

    return GuardResult(passed=True)


def validate_output(text: str) -> GuardResult:
    """
    Run all enabled output guards against LLM response text.

    Returns GuardResult(passed=False, reason=...) if the output should
    be replaced with a safe fallback message.
    """
    from src.config import (
        GUARDRAILS_ENABLED,
        GUARDRAILS_TOXICITY,
        GUARDRAILS_HALLUCINATION,
    )

    if not GUARDRAILS_ENABLED:
        return GuardResult(passed=True)

    # 1. Guardrails Hub SDK output validation (toxicity, etc.)
    _, hub_output_guard = _get_hub_guards()
    if hub_output_guard is not None:
        try:
            outcome = hub_output_guard.validate(text)
            validation_passed = bool(getattr(outcome, "validation_passed", True))
            validated_output = getattr(outcome, "validated_output", text)

            if not validation_passed:
                return GuardResult(
                    passed=False,
                    reason=(
                        "I'm sorry, I wasn't able to generate an appropriate response. "
                        "Please try rephrasing your question."
                    ),
                )

            if isinstance(validated_output, str) and validated_output != text:
                return GuardResult(passed=True, redacted=validated_output)
        except Exception as exc:
            logger.warning(f"[GUARDRAILS] Hub output validation failed, using local fallback: {exc}")

    # 2. Local toxicity fallback
    if GUARDRAILS_TOXICITY and _TOXIC_WORDS.search(text):
        logger.warning("[GUARDRAILS] Toxic content detected in LLM output.")
        return GuardResult(
            passed=False,
            reason=(
                "I'm sorry, I wasn't able to generate an appropriate response. "
                "Please try rephrasing your question."
            ),
        )

    # 3. Hallucination / citation check
    #    Heuristic: if response claims a source but no URL pattern present,
    #    flag it. Full provenance checking requires the retrieved documents
    #    context, which is injected by the agent node.
    if GUARDRAILS_HALLUCINATION:
        source_claim = re.search(
            r"\b(source|fuente|according to|según|cited in|referencia)\b",
            text,
            re.IGNORECASE,
        )
        has_url = re.search(r"https?://\S+", text)
        if source_claim and not has_url:
            logger.warning(
                "[GUARDRAILS] Source claim without URL in LLM output — potential hallucination."
            )
            # Soft warning: don't block, but log. 
            # To block: return GuardResult(passed=False, reason="...")

    return GuardResult(passed=True)

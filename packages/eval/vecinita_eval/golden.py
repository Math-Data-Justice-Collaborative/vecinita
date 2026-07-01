"""Load and validate the golden eval fixture (eval-golden-set.md)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from vecinita_shared_schemas.json_types import JsonObject, as_json_object

RetrievalExpectation = Literal["hit", "any_of", "abstain", "empty"]
GoldenDomain = Literal["community", "housing", "legal", "edge"]
GoldenLocale = Literal["en", "es"]

_DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "eval" / "qa_pairs.json"
)


@dataclass(frozen=True, slots=True)
class GoldenRow:
    """One locale variant of a golden eval case."""

    id: str
    locale: GoldenLocale
    domain: GoldenDomain
    question: str
    retrieval_expectation: RetrievalExpectation
    required_facts: tuple[str, ...]
    expected_doc_url: str | None = None
    expected_doc_urls: tuple[str, ...] = ()


def _require_str(row: JsonObject, key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        msg = f"golden row missing required string field {key!r}"
        raise ValueError(msg)
    return value


def _parse_row(raw: JsonObject) -> GoldenRow:
    expectation = _require_str(raw, "retrieval_expectation")
    if expectation not in {"hit", "any_of", "abstain", "empty"}:
        msg = f"invalid retrieval_expectation: {expectation!r}"
        raise ValueError(msg)
    domain = _require_str(raw, "domain")
    if domain not in {"community", "housing", "legal", "edge"}:
        msg = f"invalid domain: {domain!r}"
        raise ValueError(msg)
    locale = _require_str(raw, "locale")
    if locale not in {"en", "es"}:
        msg = f"invalid locale: {locale!r}"
        raise ValueError(msg)
    facts_raw = raw.get("required_facts")
    if not isinstance(facts_raw, list) or not facts_raw:
        msg = "required_facts must be a non-empty list"
        raise ValueError(msg)
    facts = tuple(str(item) for item in cast("list[object]", facts_raw))
    expected_url = raw.get("expected_doc_url")
    expected_urls_raw = raw.get("expected_doc_urls")
    expected_urls: tuple[str, ...] = ()
    if isinstance(expected_urls_raw, list):
        expected_urls = tuple(str(item) for item in cast("list[object]", expected_urls_raw))
    return GoldenRow(
        id=_require_str(raw, "id"),
        locale=cast("GoldenLocale", locale),
        domain=cast("GoldenDomain", domain),
        question=_require_str(raw, "question"),
        retrieval_expectation=cast("RetrievalExpectation", expectation),
        required_facts=facts,
        expected_doc_url=expected_url if isinstance(expected_url, str) else None,
        expected_doc_urls=expected_urls,
    )


def load_golden_rows(*, fixture_path: Path | None = None) -> list[GoldenRow]:
    """Load golden rows from the fixture JSON array."""
    path = fixture_path or _DEFAULT_FIXTURE
    loaded_raw = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(loaded_raw, list):
        msg = f"Expected JSON array in {path}"
        raise TypeError(msg)
    entries = cast("list[object]", loaded_raw)
    return [_parse_row(as_json_object(item)) for item in entries]

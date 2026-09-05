"""Helpers to draft and append golden eval examples (eval-golden-set.md)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from vecinita_eval.golden import GoldenRow, load_golden_rows

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

RetrievalExpectation = Literal["hit", "any_of", "abstain", "empty"]
GoldenDomain = Literal["community", "housing", "legal", "edge"]
GoldenLocale = Literal["en", "es"]

_VALID_EXPECTATIONS = frozenset({"hit", "any_of", "abstain", "empty"})
_VALID_DOMAINS = frozenset({"community", "housing", "legal", "edge"})
_VALID_LOCALES = frozenset({"en", "es"})


def golden_row_to_json(row: GoldenRow) -> JsonObject:
    """Serialize a golden row to the fixture JSON object shape."""
    payload: JsonObject = {
        "id": row.id,
        "locale": row.locale,
        "domain": row.domain,
        "question": row.question,
        "retrieval_expectation": row.retrieval_expectation,
        "required_facts": list(row.required_facts),
    }
    if row.expected_doc_url is not None:
        payload["expected_doc_url"] = row.expected_doc_url
    if row.expected_doc_urls:
        payload["expected_doc_urls"] = list(row.expected_doc_urls)
    return payload


def build_golden_row(  # noqa: PLR0913
    *,
    case_id: str,
    locale: str,
    domain: str,
    question: str,
    retrieval_expectation: str,
    required_facts: Sequence[str],
    expected_doc_url: str | None = None,
    expected_doc_urls: Sequence[str] | None = None,
) -> GoldenRow:
    """Validate fields and build a ``GoldenRow`` (same rules as the fixture loader)."""
    if not case_id.strip():
        msg = "id must be non-empty"
        raise ValueError(msg)
    if locale not in _VALID_LOCALES:
        msg = f"invalid locale: {locale!r}"
        raise ValueError(msg)
    if domain not in _VALID_DOMAINS:
        msg = f"invalid domain: {domain!r}"
        raise ValueError(msg)
    if retrieval_expectation not in _VALID_EXPECTATIONS:
        msg = f"invalid retrieval_expectation: {retrieval_expectation!r}"
        raise ValueError(msg)
    if not question.strip():
        msg = "question must be non-empty"
        raise ValueError(msg)
    facts = tuple(fact.strip() for fact in required_facts if fact.strip())
    if not facts:
        msg = "required_facts must be a non-empty list"
        raise ValueError(msg)
    if retrieval_expectation == "hit" and not (expected_doc_url and expected_doc_url.strip()):
        msg = "expected_doc_url is required when retrieval_expectation is hit"
        raise ValueError(msg)
    if retrieval_expectation == "any_of" and not expected_doc_urls:
        msg = "expected_doc_urls is required when retrieval_expectation is any_of"
        raise ValueError(msg)
    return GoldenRow(
        id=case_id.strip(),
        locale=cast("GoldenLocale", locale),
        domain=cast("GoldenDomain", domain),
        question=question.strip(),
        retrieval_expectation=cast("RetrievalExpectation", retrieval_expectation),
        required_facts=facts,
        expected_doc_url=expected_doc_url.strip() if expected_doc_url else None,
        expected_doc_urls=tuple(expected_doc_urls or ()),
    )


def parse_golden_draft(raw: object) -> list[GoldenRow]:
    """Parse a JSON array (or single object) of golden draft rows."""
    if isinstance(raw, dict):
        entries: list[object] = [raw]
    elif isinstance(raw, list):
        entries = cast("list[object]", raw)
    else:
        msg = "draft must be a JSON object or array"
        raise TypeError(msg)
    rows: list[GoldenRow] = []
    for item in entries:
        obj = as_json_object(item)
        facts_raw = obj.get("required_facts")
        if not isinstance(facts_raw, list):
            msg = "required_facts must be a list"
            raise TypeError(msg)
        urls_raw = obj.get("expected_doc_urls")
        urls: list[str] = []
        if isinstance(urls_raw, list):
            urls = [str(u) for u in cast("list[object]", urls_raw)]
        expected = obj.get("expected_doc_url")
        rows.append(
            build_golden_row(
                case_id=str(obj.get("id", "")),
                locale=str(obj.get("locale", "")),
                domain=str(obj.get("domain", "")),
                question=str(obj.get("question", "")),
                retrieval_expectation=str(obj.get("retrieval_expectation", "")),
                required_facts=[str(f) for f in cast("list[object]", facts_raw)],
                expected_doc_url=expected if isinstance(expected, str) else None,
                expected_doc_urls=urls,
            )
        )
    return rows


def append_golden_rows(
    *,
    fixture_path: Path,
    new_rows: Sequence[GoldenRow],
    replace_same_id_locale: bool = False,
) -> list[GoldenRow]:
    """Append (or replace) rows in a golden fixture file; return the full set."""
    existing = load_golden_rows(fixture_path=fixture_path) if fixture_path.is_file() else []
    if replace_same_id_locale:
        drop = {(row.id, row.locale) for row in new_rows}
        existing = [row for row in existing if (row.id, row.locale) not in drop]
    else:
        collisions = {
            (row.id, row.locale)
            for row in existing
            if (row.id, row.locale) in {(n.id, n.locale) for n in new_rows}
        }
        if collisions:
            msg = f"golden rows already exist for {sorted(collisions)!r}; use replace"
            raise ValueError(msg)
    merged = [*existing, *new_rows]
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    _ = fixture_path.write_text(
        json.dumps([golden_row_to_json(row) for row in merged], indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return merged

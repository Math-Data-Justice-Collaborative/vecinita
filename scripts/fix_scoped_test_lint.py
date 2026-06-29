#!/usr/bin/env python3
"""Safe batch fixes: HTTPStatus + type annotations (no docstring insertion)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = [
    ROOT / "tests" / "integration",
    ROOT / "tests" / "e2e",
    ROOT / "tests" / "smoke",
    ROOT / "tests" / "privacy",
    ROOT / "tests" / "eval",
    ROOT / "tests" / "bugs",
    ROOT / "tests" / "helpers",
    ROOT / "tests" / "conftest.py",
]

HTTP_STATUS_MAP: dict[str, str] = {
    "200": "HTTPStatus.OK",
    "201": "HTTPStatus.CREATED",
    "202": "HTTPStatus.ACCEPTED",
    "204": "HTTPStatus.NO_CONTENT",
    "400": "HTTPStatus.BAD_REQUEST",
    "401": "HTTPStatus.UNAUTHORIZED",
    "403": "HTTPStatus.FORBIDDEN",
    "404": "HTTPStatus.NOT_FOUND",
    "422": "HTTPStatus.UNPROCESSABLE_ENTITY",
    "500": "HTTPStatus.INTERNAL_SERVER_ERROR",
    "503": "HTTPStatus.SERVICE_UNAVAILABLE",
}

PARAM_TYPES: dict[str, str] = {
    "client": "TestClient",
    "write_client": "TestClient",
    "write_auth_client": "TestClient",
    "dm_client": "TestClient",
    "dm_auth_client": "TestClient",
    "chat_client": "TestClient",
    "engine": "Engine",
    "sample_docs": "list[UUID]",
    "seeded_corpus_db": "str",
    "chat_settings": "ChatRagSettings",
    "chat_service": "ChatRagService",
    "job_store": "InMemoryJobStore",
    "mock_write": "_MockWriteClient",
    "monkeypatch": "pytest.MonkeyPatch",
    "request": "pytest.FixtureRequest",
    "internal_api_key": "None",
    "supabase_auth_env": "EllipticCurvePrivateKey",
    "internal_api_auth_headers": "dict[str, str]",
    "proxy_key_env": "None",
}

FIXTURE_RETURNS: dict[str, str] = {
    "engine": "Engine",
    "client": "TestClient",
    "write_client": "TestClient",
    "write_auth_client": "TestClient",
    "dm_client": "TestClient",
    "dm_auth_client": "TestClient",
    "chat_client": "TestClient",
    "job_store": "InMemoryJobStore",
    "mock_write": "_MockWriteClient",
    "chat_settings": "ChatRagSettings",
    "chat_service": "ChatRagService",
    "seeded_corpus_db": "str",
    "internal_api_key": "None",
    "internal_api_auth_headers": "dict[str, str]",
    "supabase_auth_env": "EllipticCurvePrivateKey",
    "proxy_key_env": "None",
}

YIELD_FIXTURES = frozenset({"sample_docs", "seeded_document"})

TC_IMPORTS: dict[str, str] = {
    "Engine": "sqlalchemy.engine",
    "Iterator": "collections.abc",
    "Generator": "collections.abc",
    "EllipticCurvePrivateKey": "cryptography.hazmat.primitives.asymmetric.ec",
    "ChatRagSettings": "vecinita_chat_rag_backend.config",
    "ChatRagService": "vecinita_chat_rag_backend.service",
    "InMemoryJobStore": "vecinita_data_management_backend.store",
}

SINGLE_LINE_DEF = re.compile(
    r"^(\s*)(async\s+)?def\s+(\w+)\(([^)]*)\)(\s*->[^:]+)?:(\s*)$",
)


def iter_files() -> list[Path]:
    files: list[Path] = []
    for p in SCOPE:
        if p.is_file():
            files.append(p)
        else:
            files.extend(sorted(p.rglob("*.py")))
    return files


def split_params(params: str) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    for ch in params:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return parts


def annotate_param(param: str) -> str:
    p = param.strip()
    if not p or p.startswith("*") or ":" in p:
        return param
    if "=" in p:
        name, _, default = p.partition("=")
        name = name.strip()
        if name in PARAM_TYPES:
            return f"{name}: {PARAM_TYPES[name]} ={default}"
        return param
    if p in PARAM_TYPES:
        return f"{p}: {PARAM_TYPES[p]}"
    return param


def annotate_params(params: str) -> str:
    if not params.strip():
        return params
    return ", ".join(annotate_param(x) for x in split_params(params))


def fix_single_line_def(line: str, *, is_fixture: bool) -> str:
    m = SINGLE_LINE_DEF.match(line.rstrip("\n"))
    if not m:
        return line
    indent, async_kw, name, params, ret, trailing = m.groups()
    new_params = annotate_params(params)
    return_type = ret or ""
    if not return_type and is_fixture:
        if name in FIXTURE_RETURNS:
            return_type = f" -> {FIXTURE_RETURNS[name]}"
        elif name in YIELD_FIXTURES:
            return_type = " -> Iterator[list[UUID]]"
    async_part = async_kw or ""
    nl = "\n" if line.endswith("\n") else ""
    return f"{indent}{async_part}def {name}({new_params}){return_type}:{trailing}{nl}"


def fix_http_status(text: str) -> str:
    for code, status in HTTP_STATUS_MAP.items():
        text = re.sub(rf"\bstatus_code\s*==\s*{code}\b", f"status_code == {status}", text)
    text = text.replace(
        "status_code in (200, 204)",
        "status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)",
    )
    return text.replace(
        "status_code in (204, 200)",
        "status_code in (HTTPStatus.NO_CONTENT, HTTPStatus.OK)",
    )


def remove_cast_object(text: str) -> str:
    return re.sub(r"cast\(\"object\",\s*([^)]+)\)", r"\1", text)


def insert_after_future(text: str, line: str) -> str:
    if line.strip() in text:
        return text
    m = re.search(r"(from __future__ import annotations\n\n)", text)
    if m:
        return text.replace(m.group(1), m.group(1) + line, 1)
    return text


def ensure_tc_imports(text: str) -> str:
    needed = [n for n in TC_IMPORTS if re.search(rf"\b{n}\b", text)]
    if not needed:
        return text
    if "from typing import TYPE_CHECKING" not in text:
        text = insert_after_future(text, "from typing import TYPE_CHECKING\n\n")
    for name in needed:
        mod = TC_IMPORTS[name]
        imp = f"    from {mod} import {name}"
        if imp in text:
            continue
        tc = re.search(r"if TYPE_CHECKING:\n((?:    .+\n)*)", text)
        if tc:
            text = text.replace(
                f"if TYPE_CHECKING:\n{tc.group(1)}",
                f"if TYPE_CHECKING:\n{tc.group(1)}{imp}\n",
            )
        else:
            block = "if TYPE_CHECKING:\n" + "\n".join(
                f"    from {TC_IMPORTS[n]} import {n}" for n in needed
            )
            text = insert_after_future(text, block + "\n\n")
            break
    return text


def process_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = fix_http_status(remove_cast_object(original))
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("@pytest.fixture"):
            out.append(line)
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("@"):
                out.append(lines[i])
                i += 1
            if i < len(lines):
                out.append(fix_single_line_def(lines[i], is_fixture=True))
                i += 1
            continue
        if re.match(r"\s*def test_\w+\(", line):
            out.append(fix_single_line_def(line, is_fixture=False))
            i += 1
            continue
        out.append(line)
        i += 1
    text = "".join(out)

    if "HTTPStatus." in text:
        text = insert_after_future(text, "from http import HTTPStatus\n")
    if re.search(r"\bTestClient\b", text):
        text = insert_after_future(text, "from fastapi.testclient import TestClient\n")
    if re.search(r"\bUUID\b", text) and "from uuid import UUID" not in text:
        text = insert_after_future(text, "from uuid import UUID\n")
    text = ensure_tc_imports(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    n = sum(1 for p in iter_files() if process_file(p))
    print(f"Updated {n} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

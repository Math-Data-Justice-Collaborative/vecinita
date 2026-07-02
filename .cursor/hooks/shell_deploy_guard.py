"""Cursor preToolUse hook: advisory guards for staging DB tests and DO secret sync.

Fires on Shell tool use. Never blocks — injects additional_context reminders.
"""

from __future__ import annotations

import json
import re
import sys

_STAGING_DB = re.compile(r"ondigitalocean\.com|\.supabase\.co", re.IGNORECASE)
_FONTFACE = re.compile(r"fontface--", re.IGNORECASE)
_PROD_ENV_SOURCE = re.compile(r"source\s+prod\.env|set\s+-a.*prod\.env", re.IGNORECASE)
_PYTEST = re.compile(r"\b(pytest|make\s+test-py|make\s+test\b|uv\s+run\s+pytest)\b")
_CORPUS_RESET = re.compile(
    r"\b(seed_eval_corpus|reset_corpus_tables|load_corpus|TRUNCATE)\b",
    re.IGNORECASE,
)
_DO_SYNC = re.compile(r"do_apps\.py\s+(sync-all-secrets|sync-secrets)")
_MODAL_URL_EXPORT = re.compile(r"VECINITA_MODAL_(EMBED|LLM)_URL", re.IGNORECASE)


def check_shell_command(command: str) -> list[str]:
    notes: list[str] = []
    lower = command.lower()

    if _STAGING_DB.search(command) and (_PYTEST.search(command) or _CORPUS_RESET.search(command)):
        notes.append(
            "[corpus-db-safety] Command may hit staging Postgres. Do not pytest/seed/TRUNCATE "
            "against .ondigitalocean.com — use local DATABASE_URL or read "
            ".cursor/skills/corpus-db-safety/SKILL.md."
        )

    if _PROD_ENV_SOURCE.search(command) and _PYTEST.search(command):
        notes.append(
            "[corpus-db-safety] Sourcing prod.env before pytest risks wiping staging corpus "
            "if DATABASE_URL is DO Managed Postgres. Use a separate shell with localhost DB."
        )

    if _FONTFACE.search(command):
        notes.append(
            "[modal-do-secrets] Command contains fontface-- Modal prefix — use vecinita-- "
            "workspace URLs. See .cursor/skills/do-secrets-sync/SKILL.md."
        )

    if _MODAL_URL_EXPORT.search(command) and "/health" in lower:
        notes.append(
            "[modal-do-secrets] VECINITA_MODAL_*_URL must be base ASGI URL without /health suffix."
        )

    if _DO_SYNC.search(command):
        notes.append(
            "[do-secrets-sync] After DO secret sync: (1) validate URLs in prod.env, "
            "(2) redeploy vecinita-internal-write-api + vecinita-chat-rag-backend, "
            "(3) bash scripts/deploy/sync_github_secrets.sh --apply, "
            "(4) bash scripts/infra/do_verify_required_secrets.sh. "
            "Skill: .cursor/skills/do-secrets-sync/SKILL.md."
        )

    return notes


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    command = payload.get("command") or payload.get("input") or ""
    if not command:
        print("{}")
        return 0

    notes = check_shell_command(command)
    if notes:
        result = {"additional_context": " ".join(notes)}
    else:
        result = {}

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

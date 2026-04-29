#!/usr/bin/env bash
# Cursor afterFileEdit / afterTabFileEdit hook: when a path matches an entry in
# registry-contract-pact-tests.json, run the associated contract or Pact command
# from the repo root (stderr log only; always exit 0 so edits are not blocked).
#
# Disable: SKIP_CONTRACT_PACT_EDIT_HOOK=1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export ROOT
REGISTRY="$ROOT/.cursor/hooks/registry-contract-pact-tests.json"

if [[ "${SKIP_CONTRACT_PACT_EDIT_HOOK:-}" == "1" ]]; then
	echo "[cursor hook contract/pact] SKIP_CONTRACT_PACT_EDIT_HOOK=1 — skipping" >&2
	printf '%s\n' '{}'
	exit 0
fi

INPUT=$(cat || true)

python3 - "$ROOT" "$REGISTRY" "$INPUT" <<'PY'
import json
import os
import subprocess
import sys

root, registry_path, raw = sys.argv[1], sys.argv[2], sys.argv[3]

def main() -> None:
	def out_empty() -> None:
		print("{}")

	try:
		with open(registry_path, encoding="utf-8") as f:
			reg = json.load(f)
	except (OSError, json.JSONDecodeError) as e:
		print(f"[cursor hook contract/pact] bad registry: {e}", file=sys.stderr)
		out_empty()
		return

	try:
		payload = json.loads(raw) if raw.strip() else {}
	except json.JSONDecodeError:
		out_empty()
		return

	file_path = str(payload.get("file_path") or "").strip()
	if not file_path:
		out_empty()
		return

	try:
		rel = os.path.relpath(file_path, root)
	except ValueError:
		out_empty()
		return

	rel_n = rel.replace("\\", "/")
	if rel_n.startswith(".."):
		out_empty()
		return

	entries = reg.get("entries")
	if not isinstance(entries, list):
		out_empty()
		return

	def matches(prefixes: object) -> bool:
		if not isinstance(prefixes, list):
			return False
		for p in prefixes:
			ps = str(p).replace("\\", "/")
			if rel_n == ps or rel_n.startswith(ps + "/"):
				return True
		return False

	seen: set[str] = set()
	commands: list[str] = []
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		prefixes = entry.get("path_prefixes")
		cmd = entry.get("command")
		if not matches(prefixes) or not isinstance(cmd, str) or not cmd.strip():
			continue
		c = cmd.strip()
		if c in seen:
			continue
		seen.add(c)
		commands.append(c)

	if not commands:
		out_empty()
		return

	print(
		f"[cursor hook contract/pact] {rel_n}: running {len(commands)} command(s)",
		file=sys.stderr,
	)
	failures = 0
	for i, cmd in enumerate(commands, start=1):
		print(f"[cursor hook contract/pact] --- ({i}/{len(commands)}) {cmd}", file=sys.stderr)
		# Keep stdout clean for hook JSON; test runners log to stderr.
		r = subprocess.run(
			cmd,
			shell=True,
			cwd=root,
			stdout=sys.stderr,
			stderr=subprocess.STDOUT,
		)
		if r.returncode != 0:
			failures += 1
			print(
				f"[cursor hook contract/pact] FAILED (exit {r.returncode})",
				file=sys.stderr,
			)
	if failures:
		print(
			f"[cursor hook contract/pact] {failures}/{len(commands)} command(s) failed "
			"(fix tests or adjust code; `make ci` also covers these suites).",
			file=sys.stderr,
		)
	out_empty()


main()
PY

exit 0

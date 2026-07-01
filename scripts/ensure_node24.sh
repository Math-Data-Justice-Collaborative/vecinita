#!/usr/bin/env bash
# Ensure Node.js 24+ before frontend npm commands (QA-S006-001 / ADR-018).
# ESLint 9 on Node 22 can fail with SyntaxError in eslint internals.
set -euo pipefail

_need_major=24

_node_major() {
  node -p "process.versions.node.split('.')[0]" 2>/dev/null || echo 0
}

if [[ "$(_node_major)" -ge "$_need_major" ]]; then
  exit 0
fi

if ! command -v fnm >/dev/null 2>&1; then
  export PATH="${HOME}/.local/share/fnm:${PATH}"
fi

if command -v fnm >/dev/null 2>&1; then
  # shellcheck disable=SC1090
  eval "$(fnm env)"
  if [[ -f .nvmrc ]]; then
    fnm use >/dev/null 2>&1 || fnm install "$(tr -d 'v' < .nvmrc)" && fnm use
  else
    fnm use "$_need_major" >/dev/null 2>&1 || fnm install "$_need_major" && fnm use "$_need_major"
  fi
fi

if [[ "$(_node_major)" -ge "$_need_major" ]]; then
  exit 0
fi

echo "ERROR: Node $(_node_major).x detected; Vecinita requires Node >= $_need_major (see .nvmrc)." >&2
echo "Fix: fnm install && fnm use   — or: nvm use" >&2
exit 1

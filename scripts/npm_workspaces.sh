#!/usr/bin/env bash
# Install and run npm scripts in repo-root workspaces (ADR-021 TP-035).
# Per-app npm ci breaks hoisted devDependencies (eslint, tsc) after the second app installs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

has_root_workspaces() {
  [[ -f package.json && -f package-lock.json ]] \
    && node -e "const p=require('./package.json'); process.exit(Array.isArray(p.workspaces)?0:1)"
}

needs_npm_ci() {
  if [[ ! -x node_modules/.bin/eslint ]] || [[ ! -x node_modules/.bin/tsc ]]; then
    return 0
  fi
  if [[ ! -f node_modules/.package-lock.json ]]; then
    return 0
  fi
  if ! cmp -s package-lock.json node_modules/.package-lock.json; then
    return 0
  fi
  return 1
}

ensure_installed() {
  if has_root_workspaces; then
    if needs_npm_ci; then
      echo "==> npm ci (root workspaces)"
      npm ci
    fi
    return 0
  fi
  return 1
}

install_legacy_apps() {
  for app in chat-rag-frontend data-management-frontend; do
    echo "==> npm ci apps/${app}"
    rm -rf "apps/${app}/node_modules"
    ( cd "apps/${app}" && npm ci )
  done
}

cmd="${1:-}"
shift || true

case "$cmd" in
  install)
    if has_root_workspaces; then
      echo "==> npm ci (root workspaces)"
      npm ci
    else
      install_legacy_apps
    fi
    ;;
  run)
    script="${1:?npm script name required}"
    shift
    workspaces=("$@")
    if [[ ${#workspaces[@]} -eq 0 ]]; then
      workspaces=(
        vecinita-chat-rag-frontend
        vecinita-data-management-frontend
      )
    fi
    if ensure_installed; then
      for ws in "${workspaces[@]}"; do
        echo "==> npm run ${script} -w ${ws}"
        npm run "${script}" -w "${ws}"
      done
    else
      for app in chat-rag-frontend data-management-frontend; do
        echo "==> npm run ${script} apps/${app}"
        ( cd "apps/${app}" && npm run "${script}" )
      done
    fi
    ;;
  *)
    echo "usage: $0 install | run <script> [workspace...]" >&2
    exit 2
    ;;
esac

#!/usr/bin/env bash
# Sync vecinita-scraper (modal-apps/scraper) with origin/main using rebase + tags.
# Use this when VS Code / `git pull --tags origin main` fails with:
#   fatal: Not possible to fast-forward, aborting.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SC="${ROOT}/modal-apps/scraper"

if [[ ! -f "${SC}/.git" ]] && [[ ! -d "${SC}/.git" ]]; then
  echo "Expected git checkout at ${SC}" >&2
  exit 1
fi

# Local overrides (survive global pull.ff=only / VS Code merge pulls)
git -C "${SC}" config pull.rebase true
git -C "${SC}" config pull.ff false
git -C "${SC}" config merge.ff false
git -C "${SC}" config branch.main.rebase true

git -C "${SC}" fetch origin --tags
git -C "${SC}" pull --rebase --tags origin main

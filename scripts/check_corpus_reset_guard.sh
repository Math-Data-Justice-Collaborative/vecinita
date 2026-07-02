#!/usr/bin/env bash
# CI guard: corpus reset helpers must refuse DigitalOcean Managed Postgres hosts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if ! rg -q 'assert_corpus_reset_allowed' tests/unit/rag/conftest.py; then
  echo "ERROR: tests/unit/rag/conftest.py must call assert_corpus_reset_allowed before TRUNCATE." >&2
  exit 1
fi

if ! rg -q 'ondigitalocean.com' tests/helpers/corpus_db_guard.py; then
  echo "ERROR: corpus_db_guard must block .ondigitalocean.com hosts." >&2
  exit 1
fi

echo "OK: corpus reset guard wired for Managed Postgres protection."

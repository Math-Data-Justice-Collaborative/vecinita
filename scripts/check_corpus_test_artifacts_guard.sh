#!/usr/bin/env bash
# CI guard: test-artifact classifier + cleanup script + cursor rule must stay wired.
# Prevents regression of HF-prod-corpus-test-artifacts (managed corpus pollution).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ ! -f tests/helpers/corpus_test_artifacts.py ]]; then
  echo "ERROR: tests/helpers/corpus_test_artifacts.py missing." >&2
  exit 1
fi

if ! rg -q 'def is_corpus_test_artifact_url' tests/helpers/corpus_test_artifacts.py; then
  echo "ERROR: is_corpus_test_artifact_url must be defined." >&2
  exit 1
fi

if ! rg -q 'example\.com' tests/helpers/corpus_test_artifacts.py; then
  echo "ERROR: classifier must mention example.com." >&2
  exit 1
fi

if ! rg -q 'fixture://' tests/helpers/corpus_test_artifacts.py; then
  echo "ERROR: classifier must mention fixture://." >&2
  exit 1
fi

if [[ ! -f scripts/ops/cleanup_corpus_test_artifacts.py ]]; then
  echo "ERROR: scripts/ops/cleanup_corpus_test_artifacts.py missing." >&2
  exit 1
fi

if ! rg -q 'assert_corpus_reset_allowed' scripts/ops/cleanup_corpus_test_artifacts.py; then
  echo "ERROR: cleanup script must call assert_corpus_reset_allowed before deletes." >&2
  exit 1
fi

if [[ ! -f .cursor/rules/no-corpus-test-artifacts.mdc ]]; then
  echo "ERROR: .cursor/rules/no-corpus-test-artifacts.mdc missing." >&2
  exit 1
fi

if ! rg -q 'is_corpus_test_artifact_url' tests/unit/test_corpus_test_artifacts.py; then
  echo "ERROR: unit coverage for classifier missing." >&2
  exit 1
fi

echo "OK: corpus test-artifact classifier, cleanup script, and rule are wired."

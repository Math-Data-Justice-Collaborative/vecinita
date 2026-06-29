#!/usr/bin/env bash
# Offline guard for supabase/config.toml — invite-only admin auth (ADR-026/027, F34).
# Safe to run without Supabase login or Docker (used in CI validate job before `supabase start`).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/supabase/config.toml"
CANONICAL_REF="cfuvghdsuwactfeamtym"

if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: missing $CONFIG" >&2
  exit 1
fi

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

grep -q "project_id = \"${CANONICAL_REF}\"" "$CONFIG" \
  || fail "project_id must be ${CANONICAL_REF}"

grep -q "enable_signup = false" "$CONFIG" \
  || fail "[auth] enable_signup must be false (invite-only)"

grep -q "enable_anonymous_sign_ins = false" "$CONFIG" \
  || fail "[auth] enable_anonymous_sign_ins must be false"

grep -q '\[auth.email\]' "$CONFIG" || fail "missing [auth.email] section"

grep -A20 '\[auth.email\]' "$CONFIG" | grep -q "enable_signup = false" \
  || fail "[auth.email] enable_signup must be false"

# SMTP placeholders must not embed live secrets (operator contract only).
grep -q 'pass = "env(' "$CONFIG" \
  || fail "[auth.email.smtp] pass must use env(...) placeholder"

echo "OK: supabase/config.toml passes offline contract checks."

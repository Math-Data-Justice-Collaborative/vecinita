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

# --- EV-006 F35: Resend SMTP + versioned email templates (TC-094, TC-095) ---

# SMTP must be enabled and point at Resend, with the password sourced from an env() ref
# (never a literal secret).
grep -q '\[auth.email.smtp\]' "$CONFIG" || fail "missing [auth.email.smtp] section"
grep -A8 '\[auth.email.smtp\]' "$CONFIG" | grep -q 'enabled = true' \
  || fail "[auth.email.smtp] must be enabled = true (Resend production delivery)"
grep -q 'host = "smtp.resend.com"' "$CONFIG" \
  || fail "[auth.email.smtp] host must be smtp.resend.com"
grep -q 'pass = "env(SUPABASE_SMTP_PASS)"' "$CONFIG" \
  || fail "[auth.email.smtp] pass must reference env(SUPABASE_SMTP_PASS)"

# No literal Resend API key may be committed (keys appear as a quoted "re_..." token).
if grep -Eq '"re_[A-Za-z0-9]{8,}' "$CONFIG"; then
  fail "config.toml appears to contain a literal Resend key (re_...)"
fi

# Email rate limit, OTP expiry, and password policy (TP-S005-07/11).
grep -q 'email_sent = 30' "$CONFIG" || fail "[auth.rate_limit] email_sent must be 30"
grep -q 'otp_expiry = 3600' "$CONFIG" || fail "[auth.email] otp_expiry must be 3600"
grep -q 'minimum_password_length = 8' "$CONFIG" \
  || fail "[auth] minimum_password_length must be 8"

# Template path-resolution convention (CLI #5124):
#   auth.email.template.*      content_path resolves from the PROJECT ROOT.
#   auth.email.notification.*  content_path resolves from the supabase/ directory.
ROOT_TEMPLATES=(
  "supabase/templates/invite.html"
  "supabase/templates/recovery.html"
  "supabase/templates/confirmation.html"
  "supabase/templates/magic_link.html"
  "supabase/templates/email_change.html"
)
for tpl in "${ROOT_TEMPLATES[@]}"; do
  grep -q "content_path = \"${tpl}\"" "$CONFIG" \
    || fail "missing template content_path: ${tpl}"
  [[ -f "$ROOT/$tpl" ]] || fail "template file missing (root-relative): ${tpl}"
done

NOTIFICATION_TEMPLATES=(
  "templates/password-changed.html"
)
for tpl in "${NOTIFICATION_TEMPLATES[@]}"; do
  grep -q "content_path = \"${tpl}\"" "$CONFIG" \
    || fail "missing notification content_path: ${tpl}"
  [[ -f "$ROOT/supabase/$tpl" ]] || fail "template file missing (supabase-relative): ${tpl}"
done

echo "OK: supabase/config.toml passes offline contract checks."

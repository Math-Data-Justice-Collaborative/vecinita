#!/usr/bin/env bash
# Portable install: OpenGrep, 2ms, KICS, Grype, Microsoft SBOM Tool.
# Installs to ~/.local/share/security-static-analysis/{bin,assets}
#
# GitHub Releases API + downloads retry on transient failures (#227 / BUG-2026-08-06).
# Optional GH_TOKEN / GITHUB_TOKEN raises api.github.com quota (never commit tokens).
set -euo pipefail

PREFIX="${SEC_TOOLS_DIR:-${HOME}/.local/share/security-static-analysis}"
BIN_DIR="${PREFIX}/bin"
ASSETS_DIR="${PREFIX}/assets"
mkdir -p "${BIN_DIR}" "${ASSETS_DIR}"
export PATH="${BIN_DIR}:${PATH}"

# Retries for api.github.com + asset downloads (CI flake: rate limit / empty / timeout).
SEC_GITHUB_API_RETRIES="${SEC_GITHUB_API_RETRIES:-5}"
SEC_GITHUB_API_RETRY_DELAY="${SEC_GITHUB_API_RETRY_DELAY:-2}"

log() { printf '[security] %s\n' "$*"; }
err() { printf '[security] ERROR: %s\n' "$*" >&2; }

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH_RAW="$(uname -m)"
case "${ARCH_RAW}" in
  x86_64 | amd64) ARCH="amd64" ;;
  aarch64 | arm64) ARCH="arm64" ;;
  *) err "unsupported arch ${ARCH_RAW}"; exit 1 ;;
esac

# Retry curl until success or attempts exhausted. Hard-fail after N — never soft-skip.
_curl_retry() {
  local max="${SEC_GITHUB_API_RETRIES}"
  local delay="${SEC_GITHUB_API_RETRY_DELAY}"
  local attempt=1
  local rc=0

  while ((attempt <= max)); do
    if curl "$@"; then
      return 0
    fi
    rc=$?
    if ((attempt < max)); then
      log "fetch attempt ${attempt}/${max} failed (rc=${rc}); retry in ${delay}s..."
      sleep "${delay}"
    fi
    attempt=$((attempt + 1))
  done
  return "${rc}"
}

# Authenticated GitHub API GET when GH_TOKEN / GITHUB_TOKEN is set (stdout body).
_github_api_get() {
  local url="$1"
  local -a hdr=(
    -H "Accept: application/vnd.github+json"
    -H "User-Agent: vecinita-ci"
  )
  local token="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
  if [[ -n "${token}" ]]; then
    hdr+=(-H "Authorization: Bearer ${token}" -H "X-GitHub-Api-Version: 2022-11-28")
  fi
  _curl_retry -fsSL "${hdr[@]}" "${url}"
}

download() {
  _curl_retry -fsSL "$1" -o "$2"
}

log "installing → ${BIN_DIR} (${OS}/${ARCH})"

# OpenGrep
if [[ ! -x "${BIN_DIR}/opengrep" || "${SEC_FORCE:-0}" == "1" ]]; then
  # Official installer; downloaded to a temp file (not curl|bash) then executed.
  _og_install="$(mktemp)"
  download "https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh" "${_og_install}"
  bash "${_og_install}"
  rm -f "${_og_install}"
  ln -sfn "${HOME}/.opengrep/cli/latest/opengrep" "${BIN_DIR}/opengrep"
fi

# 2ms — resolve asset URL via GitHub API (avoids /latest/download 404 races)
if [[ ! -x "${BIN_DIR}/2ms" || "${SEC_FORCE:-0}" == "1" ]]; then
  case "${OS}-${ARCH}" in
    linux-amd64) A=linux-amd64.zip ;;
    linux-arm64) A=linux-arm64.zip ;;
    darwin-amd64) A=macos-amd64.zip ;;
    darwin-arm64) A=macos-arm64.zip ;;
    *) err "no 2ms asset"; exit 1 ;;
  esac
  tmp="$(mktemp -d)"
  asset_url="$(
    _github_api_get "https://api.github.com/repos/checkmarx/2ms/releases/latest" \
      | sed -n "s/.*\"browser_download_url\": *\"\\([^\"]*${A}\\)\".*/\\1/p" \
      | head -1
  )"
  if [[ -z "${asset_url}" ]]; then
    asset_url="https://github.com/checkmarx/2ms/releases/latest/download/${A}"
  fi
  download "${asset_url}" "${tmp}/${A}"
  unzip -qo "${tmp}/${A}" -d "${tmp}/out"
  bin="$(find "${tmp}/out" -type f \( -name 2ms -o -name 2ms.exe \) | head -1)"
  install -m 0755 "${bin}" "${BIN_DIR}/2ms"
  rm -rf "${tmp}"
fi

# KICS — skip draft/empty "latest" releases; pick newest tag with a linux/darwin tarball
if [[ ! -x "${BIN_DIR}/kics" || ! -d "${ASSETS_DIR}/kics/assets/queries" || "${SEC_FORCE:-0}" == "1" ]]; then
  case "${OS}" in linux) osn=linux ;; darwin) osn=darwin ;; esac
  tmp="$(mktemp -d)"
  # Prints: tag_name|browser_download_url|asset_name
  kics_meta="$(
    SEC_GITHUB_API_RETRIES="${SEC_GITHUB_API_RETRIES}" \
      SEC_GITHUB_API_RETRY_DELAY="${SEC_GITHUB_API_RETRY_DELAY}" \
      GH_TOKEN="${GH_TOKEN:-}" \
      GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
      python3 - "${osn}" "${ARCH}" <<'PY'
import json
import os
import sys
import time
import urllib.error
import urllib.request

osn, arch = sys.argv[1], sys.argv[2]
suffix = f"_{osn}_{arch}.tar.gz"
url = "https://api.github.com/repos/Checkmarx/kics/releases?per_page=30"
retries = int(os.environ.get("SEC_GITHUB_API_RETRIES", "5"))
delay = float(os.environ.get("SEC_GITHUB_API_RETRY_DELAY", "2"))
token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "vecinita-ci",
}
if token:
    headers["Authorization"] = f"Bearer {token}"
    headers["X-GitHub-Api-Version"] = "2022-11-28"

releases = None
last_err = None
for attempt in range(1, retries + 1):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            releases = json.load(resp)
        break
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        last_err = exc
        if attempt < retries:
            time.sleep(delay)
        else:
            raise SystemExit(
                f"GitHub API failed after {retries} attempts: {exc}"
            ) from exc

if not isinstance(releases, list):
    raise SystemExit(f"unexpected GitHub releases payload: {last_err!r}")

for rel in releases:
    tag = rel.get("tag_name") or ""
    for asset in rel.get("assets") or []:
        name = asset.get("name") or ""
        if name.startswith("kics_") and name.endswith(suffix):
            asset_url = asset.get("browser_download_url") or ""
            if tag and asset_url:
                print(f"{tag}|{asset_url}|{name}")
                raise SystemExit(0)
raise SystemExit("no KICS release asset found for " + suffix)
PY
  )"
  ver="${kics_meta%%|*}"
  rest="${kics_meta#*|}"
  asset_url="${rest%%|*}"
  asset="${rest##*|}"
  download "${asset_url}" "${tmp}/${asset}"
  tar -xzf "${tmp}/${asset}" -C "${tmp}"
  bin="$(find "${tmp}" -type f -name kics | head -1)"
  install -m 0755 "${bin}" "${BIN_DIR}/kics"
  rm -rf "${ASSETS_DIR}/kics"
  mkdir -p "${ASSETS_DIR}/kics"
  if [[ -d "${tmp}/assets/queries" ]]; then
    cp -R "${tmp}/assets" "${ASSETS_DIR}/kics/"
  else
    download "https://github.com/Checkmarx/kics/releases/download/${ver}/extracted-info.zip" "${tmp}/extracted-info.zip"
    unzip -qo "${tmp}/extracted-info.zip" -d "${tmp}/extracted"
    cp -R "${tmp}/extracted/assets" "${ASSETS_DIR}/kics/"
  fi
  rm -rf "${tmp}"
fi

# Grype
if [[ ! -x "${BIN_DIR}/grype" || "${SEC_FORCE:-0}" == "1" ]]; then
  # Official installer downloaded to a temp file (avoids curl|sh); -b sets install dir.
  _grype_install="$(mktemp)"
  _curl_retry -sSfL https://get.anchore.io/grype -o "${_grype_install}"
  sh "${_grype_install}" -b "${BIN_DIR}"
  rm -f "${_grype_install}"
fi

# SBOM Tool
if [[ ! -x "${BIN_DIR}/sbom-tool" || "${SEC_FORCE:-0}" == "1" ]]; then
  case "${OS}-${ARCH}" in
    linux-amd64) A=sbom-tool-linux-x64 ;;
    darwin-amd64) A=sbom-tool-osx-x64 ;;
    darwin-arm64) A=sbom-tool-osx-arm64 ;;
    *) err "no sbom-tool asset for ${OS}-${ARCH}"; exit 1 ;;
  esac
  download "https://github.com/microsoft/sbom-tool/releases/latest/download/${A}" "${BIN_DIR}/sbom-tool"
  chmod 0755 "${BIN_DIR}/sbom-tool"
fi

log "done — export PATH=\"${BIN_DIR}:\$PATH\""
printf '%s\n' "${BIN_DIR}"

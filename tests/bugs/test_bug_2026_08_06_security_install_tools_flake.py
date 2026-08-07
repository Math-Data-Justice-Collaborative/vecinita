"""BUG-2026-08-06: install-tools.sh must retry transient GitHub API failures (#227).

Failure mode: api.github.com releases fetch returns 403/empty/timeout once; without
retries, pre-commit / CI security install goes red. Rerun usually succeeds.

[Corpus: WAIVED — no Fn yet; reason: tooling CI flake from RET-002; decided: 2026-08-06]
[Spec: docs/security/static-analysis.md]
[Spec: docs/bug-reports/BUG-2026-08-06-security-install-tools-flake.md]
"""

from __future__ import annotations

import os
import platform
import stat
import subprocess
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_MIN_GITHUB_API_CALLS = 2


def _2ms_asset_name() -> str:
    """Match scripts/security/install-tools.sh OS/ARCH asset naming for 2ms."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "amd64" if machine in {"x86_64", "amd64"} else "arm64"
    if system == "darwin":
        return f"macos-{arch}.zip"
    if system == "linux":
        return f"linux-{arch}.zip"
    msg = f"unsupported platform for 2ms fixture: {system}/{machine}"
    raise RuntimeError(msg)


def test_install_tools_retries_transient_github_api_failure(tmp_path: Path) -> None:
    """First GitHub API curls fail; install retries and succeeds (S027-FLAKY-SECURITY-INSTALL)."""
    tools = tmp_path / "tools"
    bin_dir = tools / "bin"
    assets = tools / "assets" / "kics" / "assets" / "queries"
    bin_dir.mkdir(parents=True)
    assets.mkdir(parents=True)
    for name in ("opengrep", "kics", "grype", "sbom-tool"):
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)

    asset = _2ms_asset_name()
    zip_path = tmp_path / asset
    with zipfile.ZipFile(zip_path, "w") as zf:
        info = zipfile.ZipInfo("2ms")
        info.external_attr = 0o755 << 16
        zf.writestr(info, b"#!/bin/sh\necho 2ms-fixture\n")

    counter = tmp_path / "github_api_calls"
    counter.write_text("0", encoding="utf-8")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_curl = fake_bin / "curl"
    # Fail first API hit, then return a release JSON whose asset URL is served from fixture.
    fake_curl.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
COUNTER="{counter}"
ZIP="{zip_path}"
ASSET="{asset}"
out=""
url=""
args=("$@")
i=0
while [[ $i -lt ${{#args[@]}} ]]; do
  a="${{args[$i]}}"
  if [[ "$a" == "-o" || "$a" == "--output" ]]; then
    i=$((i + 1))
    out="${{args[$i]}}"
  elif [[ "$a" == http://* || "$a" == https://* ]]; then
    url="$a"
  fi
  i=$((i + 1))
done
if [[ -z "$url" ]]; then
  echo "curl-fixture: missing url: $*" >&2
  exit 2
fi
if [[ "$url" == *api.github.com/repos/checkmarx/2ms/releases/latest* ]]; then
  n=$(cat "$COUNTER")
  n=$((n + 1))
  echo "$n" > "$COUNTER"
  if [[ "$n" -lt {_MIN_GITHUB_API_CALLS} ]]; then
    echo "Failed to fetch available versions from GitHub." >&2
    exit 22
  fi
  body=$(cat <<EOF
{{"tag_name":"v0.0.0-fixture","assets":[{{"name":"$ASSET","browser_download_url":"https://github.com/checkmarx/2ms/releases/download/v0.0.0-fixture/$ASSET"}}]}}
EOF
)
  if [[ -n "$out" ]]; then
    printf '%s' "$body" > "$out"
  else
    printf '%s' "$body"
  fi
  exit 0
fi
if [[ "$url" == *"/checkmarx/2ms/releases/download/"*"$ASSET"* ]]; then
  if [[ -z "$out" ]]; then
    echo "curl-fixture: download needs -o" >&2
    exit 2
  fi
  cp "$ZIP" "$out"
  exit 0
fi
echo "curl-fixture: unexpected url $url" >&2
exit 2
""",
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
    env["SEC_TOOLS_DIR"] = str(tools)
    env["SEC_FORCE"] = "0"
    # Contract expected by fix (#227): retries + zero delay for tests.
    env["SEC_GITHUB_API_RETRIES"] = "3"
    env["SEC_GITHUB_API_RETRY_DELAY"] = "0"
    env["HOME"] = str(tmp_path / "home")
    (tmp_path / "home").mkdir()

    result = subprocess.run(  # noqa: S603
        ["bash", str(REPO_ROOT / "scripts/security/install-tools.sh")],  # noqa: S607
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"install-tools.sh failed under transient GitHub API error\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    installed = bin_dir / "2ms"
    assert installed.is_file(), "2ms binary was not installed"
    assert os.access(installed, os.X_OK), "2ms binary is not executable"
    assert int(counter.read_text(encoding="utf-8")) >= _MIN_GITHUB_API_CALLS

"""Modal container image definitions.

Separate images keep image build times fast by only including the
dependencies actually needed by each function.
"""

import modal

# Base image used by Ollama-backed model functions.
# Installs a pinned Ollama server binary and the Python client library.
# The binary is checksum-verified to avoid executing remote install scripts.
OLLAMA_VERSION = "0.6.1"
OLLAMA_TARBALL = "ollama-linux-amd64.tgz"
OLLAMA_URL = (
    f"https://github.com/ollama/ollama/releases/download/v{OLLAMA_VERSION}/"
    f"{OLLAMA_TARBALL}"
)
# SHA-256 for ollama-linux-amd64.tgz from the v0.6.1 release.
OLLAMA_SHA256 = "b17f2f8233f2c40b8391eb9f45331967221c76cef0506aeb93f4ae7be02afe9f"

ollama_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("curl", "ca-certificates")
    .run_commands(
        "set -eu && "
        "curl -fsSL -o /tmp/ollama.tgz "
        f"{OLLAMA_URL} && "
        f"echo '{OLLAMA_SHA256}  /tmp/ollama.tgz' | sha256sum -c - && "
        "tar -xzf /tmp/ollama.tgz -C /usr/local && "
        "rm -f /tmp/ollama.tgz"
    )
    .pip_install(
        "fastapi[standard]>=0.115.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "ollama>=0.4.0",
    )
    .add_local_dir("src/vecinita", remote_path="/root/vecinita")
)

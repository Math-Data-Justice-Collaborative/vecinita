"""EV-354 / #354: warm-before-smoke helper + CI contract (TC-326).

[Corpus: staging]
[Corpus: feature-list.md §F83]
[Spec: docs/test-plan.md §TC-326]
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from scripts.ops import warm_staging_for_smoke as warm

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-staging.yml"
HELPER = REPO_ROOT / "scripts" / "ops" / "warm_staging_for_smoke.py"

_WARM_SERVICE_COUNT = 2


def test_warm_helper_module_exists() -> None:
    """TC-326: warm-before-smoke entrypoint is present in-repo."""
    assert HELPER.is_file()
    assert HELPER.stat().st_size > 0


def test_deploy_staging_smoke_invokes_warm_helper() -> None:
    """TC-326: staging-smoke job warms Modal before H1-H3."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "staging-smoke" in text
    assert "warm_staging_for_smoke" in text
    warm_idx = text.index("warm_staging_for_smoke")
    smoke_idx = text.index("test_staging_health.py")
    assert warm_idx < smoke_idx


def test_resolve_warm_targets_requires_urls() -> None:
    """Fail closed when embed/LLM staging URLs are missing."""
    with pytest.raises(ValueError, match="VECINITA"):
        _ = warm.resolve_warm_targets(embed_url="", llm_url="", proxy_key="k")


def test_resolve_warm_targets_requires_proxy_key() -> None:
    """Proxy key required for Modal /warm (RD-165)."""
    with pytest.raises(ValueError, match="PROXY"):
        _ = warm.resolve_warm_targets(
            embed_url="https://example.modal.run",
            llm_url="https://example.modal.run",
            proxy_key="",
        )


def test_post_warm_posts_to_warm_path() -> None:
    """POST {base}/warm with proxy header."""
    seen: list[tuple[str, dict[str, str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), dict(request.headers)))
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        warm.post_warm(
            client=client,
            base_url="https://vecinita-staging--vecinita-llm.modal.run/",
            proxy_key="secret-key",
            timeout_s=5.0,
        )

    assert len(seen) == 1
    url, headers = seen[0]
    assert url == "https://vecinita-staging--vecinita-llm.modal.run/warm"
    assert headers.get("x-vecinita-proxy-key") == "secret-key"


def test_run_warm_calls_embed_and_llm() -> None:
    """Both embed and LLM bases are warmed."""
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, json={"status": "ok"})

    targets = warm.WarmTargets(
        embed_url="https://embed.example",
        llm_url="https://llm.example",
        proxy_key="k",
    )
    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        code = warm.run_warm(targets, timeout_s=1.0, dry_run=False, client=client)
    assert code == 0
    assert urls == [
        "https://embed.example/warm",
        "https://llm.example/warm",
    ]
    assert len(urls) == _WARM_SERVICE_COUNT


def test_run_warm_dry_run_skips_network() -> None:
    """Dry-run validates targets without HTTP."""
    targets = warm.WarmTargets(
        embed_url="https://embed.example",
        llm_url="https://llm.example",
        proxy_key="k",
    )
    hits = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal hits
        del request
        hits += 1
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        code = warm.run_warm(targets, timeout_s=1.0, dry_run=True, client=client)
    assert code == 0
    assert hits == 0


def test_run_warm_propagates_http_errors() -> None:
    """Non-2xx warm fails the helper (smoke must not proceed silently)."""
    targets = warm.WarmTargets(
        embed_url="https://embed.example",
        llm_url="https://llm.example",
        proxy_key="k",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(503)

    transport = httpx.MockTransport(handler)
    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(httpx.HTTPStatusError),
    ):
        _ = warm.run_warm(targets, timeout_s=1.0, dry_run=False, client=client)

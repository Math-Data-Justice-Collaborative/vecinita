"""TC-305 / TC-306 — staging observability compose contracts (F84 / ADR-055).

[Corpus: feature-list.md §F84]
[Spec: docs/adr/ADR-055-operational-monitoring-grafana-loki.md]
[Spec: docs/test-plan.md §TC-305 §TC-306]
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
OBS = REPO_ROOT / "infra" / "observability"

FORBIDDEN_CONTENT_KEYS = frozenset(
    {"question", "answer", "prompt", "message", "messages", "raw_prompt", "text"},
)

# Pins locked for M139 (also documented in docs/dependency-inventory.md).
EXPECTED_IMAGE_PINS: dict[str, str] = {
    "grafana": "grafana/grafana:11.6.1",
    "loki": "grafana/loki:3.4.2",
    "alloy": "grafana/alloy:v1.8.3",
    "prometheus": "prom/prometheus:v2.55.1",
    "alertmanager": "prom/alertmanager:v0.28.1",
}


def _load_yaml(path: Path) -> object:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw is not None
    return raw


def test_observability_compose_pins_exact_image_tags() -> None:
    """Compose must pin Grafana/Loki/Alloy/Prometheus/Alertmanager (not :latest)."""
    compose_path = OBS / "docker-compose.yml"
    assert compose_path.is_file(), "infra/observability/docker-compose.yml missing"
    data = cast("dict[str, object]", _load_yaml(compose_path))
    services = cast("dict[str, dict[str, object]]", data["services"])
    for name, image in EXPECTED_IMAGE_PINS.items():
        assert name in services, f"missing service {name}"
        assert services[name]["image"] == image
        assert not str(services[name]["image"]).endswith(":latest")


def test_loki_retention_is_short_window_tc305() -> None:
    """AC-MON6: Loki retention ≤ 7 days (168h)."""
    loki_path = OBS / "loki-config.yaml"
    assert loki_path.is_file()
    data = cast("dict[str, object]", _load_yaml(loki_path))
    limits = cast("dict[str, object]", data["limits_config"])
    retention = str(limits["retention_period"])
    assert retention.endswith("h")
    hours = int(retention.removesuffix("h"))
    assert hours <= 168
    assert hours >= 24


def test_alloy_pipeline_drops_forbidden_content_keys_tc305() -> None:
    """Alloy config must document/drop ADR-004 / F17 prompt-like fields."""
    alloy_path = OBS / "config.alloy"
    assert alloy_path.is_file()
    text = alloy_path.read_text(encoding="utf-8")
    for key in ("question", "answer", "prompt", "message", "raw_prompt"):
        assert key in text, f"alloy must mention drop/redact of {key}"


def test_alertmanager_webhook_receiver_tc306() -> None:
    """AC-MON8: Alertmanager routes to webhook; no chat content keys in templates."""
    am_path = OBS / "alertmanager.yml"
    assert am_path.is_file()
    data = cast("dict[str, object]", _load_yaml(am_path))
    receivers = cast("list[dict[str, object]]", data["receivers"])
    webhook_receivers = [r for r in receivers if r.get("webhook_configs")]
    assert webhook_receivers, "expected ≥1 webhook receiver"
    blob = yaml.dump(data)
    for key in FORBIDDEN_CONTENT_KEYS:
        assert key not in blob.lower() or key == "message", (
            f"alertmanager config must not embed content key {key}"
        )
    # "message" may appear as Alertmanager template field name — ensure no chat fields
    assert "question" not in blob.lower()
    assert "answer" not in blob.lower()
    assert "prompt" not in blob.lower()
    assert "raw_prompt" not in blob.lower()


def test_prometheus_has_ingest_or_health_alert_rule_tc306() -> None:
    """≥1 Prometheus alert rule for staging (ingest failure or scrape down)."""
    rules_path = OBS / "prometheus" / "alert-rules.yml"
    assert rules_path.is_file()
    data = cast("dict[str, object]", _load_yaml(rules_path))
    groups = cast("list[dict[str, object]]", data["groups"])
    alerts: list[str] = []
    for group in groups:
        for rule in cast("list[dict[str, object]]", group["rules"]):
            name = rule.get("alert")
            if isinstance(name, str):
                alerts.append(name)
    assert alerts, "expected ≥1 alert rule"
    assert any("ingest" in a.lower() or "health" in a.lower() or "up" in a.lower() for a in alerts)
    blob = yaml.dump(data).lower()
    assert "question" not in blob
    assert "answer" not in blob
    assert "prompt" not in blob

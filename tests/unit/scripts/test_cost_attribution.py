"""Unit tests for Vecinita cost attribution name filter (EV-323 / #323).

[Corpus: ADR-004]
"""

from __future__ import annotations

from scripts.ops.cost_attribution import classify_names, is_vecinita_resource_name


def test_is_vecinita_resource_name_includes_vecinita_apps() -> None:
    """Vecinita-prefixed cloud names are in-envelope."""
    assert is_vecinita_resource_name("vecinita-staging-db") is True
    assert is_vecinita_resource_name("vecinita-chat-rag-backend") is True
    assert is_vecinita_resource_name("vecinita-staging-restored-20260701") is True
    assert is_vecinita_resource_name("vecinita-staging-obs") is True


def test_is_vecinita_resource_name_excludes_sibling_projects() -> None:
    """Metar / empiric / unrelated names stay out of the Vecinita envelope."""
    assert is_vecinita_resource_name("metar-iwxxm") is False
    assert is_vecinita_resource_name("metar-iwxxm-staging") is False
    assert is_vecinita_resource_name("empiric-mlflow-server") is False
    assert is_vecinita_resource_name("empiric-mlflow-pg") is False
    assert is_vecinita_resource_name("random-droplet") is False
    assert is_vecinita_resource_name("") is False


def test_classify_names_splits_included_and_excluded() -> None:
    """classify_names partitions a mixed list."""
    result = classify_names(
        [
            "vecinita-staging-db",
            "metar-iwxxm",
            "vecinita-admin-frontend",
            "empiric-mlflow-pg",
        ]
    )
    assert result == {
        "vecinita": ["vecinita-staging-db", "vecinita-admin-frontend"],
        "excluded": ["metar-iwxxm", "empiric-mlflow-pg"],
    }

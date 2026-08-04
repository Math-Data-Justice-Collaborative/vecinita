"""Unit tests for F65 energy heuristic (TC-218 / ADR-047 / AC-UX3)."""

from __future__ import annotations

import pytest
from vecinita_chat_rag_backend.energy import (
    DEFAULT_CAR_GCO2E_PER_KM,
    DEFAULT_GCO2E_PER_KWH,
    DEFAULT_GPU_TDP_W,
    DEFAULT_GPU_UTIL,
    ENERGY_METHOD,
    EnergyKnobs,
    compute_energy_estimate,
)


def test_compute_energy_estimate_one_hour_defaults() -> None:
    """Wh = TDP * util * duration_s / 3600; gCO2e and car_* from defaults."""
    estimate = compute_energy_estimate(duration_s=3600.0)
    assert estimate.method == ENERGY_METHOD
    assert estimate.method == "tdp_util_walltime_v1"
    assert estimate.wh == pytest.approx(DEFAULT_GPU_TDP_W * DEFAULT_GPU_UTIL)
    assert estimate.g_co2e == pytest.approx(
        (estimate.wh / 1000.0) * DEFAULT_GCO2E_PER_KWH,
    )
    assert estimate.car_km_equiv == pytest.approx(
        estimate.g_co2e / DEFAULT_CAR_GCO2E_PER_KM,
    )
    assert estimate.car_m_equiv == pytest.approx(estimate.car_km_equiv * 1000.0)
    assert estimate.advisory
    assert "approximate" in estimate.advisory.lower() or "approx" in estimate.advisory.lower()


def test_compute_energy_estimate_scales_with_duration() -> None:
    """Doubling wall time doubles Wh (linear heuristic)."""
    short = compute_energy_estimate(duration_s=2.0)
    long = compute_energy_estimate(duration_s=4.0)
    assert long.wh == pytest.approx(short.wh * 2.0)
    assert long.g_co2e == pytest.approx(short.g_co2e * 2.0)
    assert long.car_m_equiv == pytest.approx(short.car_m_equiv * 2.0)


def test_compute_energy_estimate_respects_overrides() -> None:
    """Config knobs (TDP / util / intensity / car g/km) feed the formula."""
    estimate = compute_energy_estimate(
        3600.0,
        EnergyKnobs(
            gpu_tdp_w=100.0,
            gpu_util=1.0,
            gco2e_per_kwh=400.0,
            car_gco2e_per_km=200.0,
        ),
    )
    assert estimate.wh == pytest.approx(100.0)
    assert estimate.g_co2e == pytest.approx(40.0)
    assert estimate.car_km_equiv == pytest.approx(0.2)
    assert estimate.car_m_equiv == pytest.approx(200.0)


def test_compute_energy_estimate_rejects_non_positive_duration() -> None:
    """Wall time must be positive."""
    with pytest.raises(ValueError, match="duration"):
        compute_energy_estimate(duration_s=0.0)
    with pytest.raises(ValueError, match="duration"):
        compute_energy_estimate(duration_s=-1.0)

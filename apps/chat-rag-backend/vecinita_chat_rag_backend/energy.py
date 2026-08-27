"""F65 ask energy heuristic + car-travel equivalent (ADR-047 / AC-UX3)."""

from __future__ import annotations

from dataclasses import dataclass

from vecinita_shared_schemas.chat_rag import EnergyEstimate

ENERGY_METHOD = "tdp_util_walltime_v1"
DEFAULT_GPU_TDP_W = 70.0
DEFAULT_GPU_UTIL = 0.5
DEFAULT_GCO2E_PER_KWH = 386.0
DEFAULT_CAR_GCO2E_PER_KM = 251.0
DEFAULT_ADVISORY = (
    "Approximate energy and CO2e from GPU TDP x utilization x wall time -- "
    + "not live Modal power telemetry."
)


@dataclass(frozen=True, slots=True)
class EnergyKnobs:
    """Configurable constants for the TDP x util x wall-time heuristic."""

    gpu_tdp_w: float = DEFAULT_GPU_TDP_W
    gpu_util: float = DEFAULT_GPU_UTIL
    gco2e_per_kwh: float = DEFAULT_GCO2E_PER_KWH
    car_gco2e_per_km: float = DEFAULT_CAR_GCO2E_PER_KM
    advisory: str = DEFAULT_ADVISORY


def compute_energy_estimate(
    duration_s: float,
    knobs: EnergyKnobs | None = None,
) -> EnergyEstimate:
    """Compute heuristic Wh / gCO2e / car distance for an ask wall duration."""
    cfg = knobs if knobs is not None else EnergyKnobs()
    if duration_s <= 0:
        msg = "duration_s must be positive"
        raise ValueError(msg)
    if cfg.gpu_tdp_w <= 0:
        msg = "gpu_tdp_w must be positive"
        raise ValueError(msg)
    if not 0 < cfg.gpu_util <= 1:
        msg = "gpu_util must be in (0, 1]"
        raise ValueError(msg)
    if cfg.gco2e_per_kwh <= 0:
        msg = "gco2e_per_kwh must be positive"
        raise ValueError(msg)
    if cfg.car_gco2e_per_km <= 0:
        msg = "car_gco2e_per_km must be positive"
        raise ValueError(msg)

    wh = cfg.gpu_tdp_w * cfg.gpu_util * duration_s / 3600.0
    g_co2e = (wh / 1000.0) * cfg.gco2e_per_kwh
    car_km_equiv = g_co2e / cfg.car_gco2e_per_km
    car_m_equiv = car_km_equiv * 1000.0
    return EnergyEstimate(
        wh=wh,
        g_co2e=g_co2e,
        method=ENERGY_METHOD,
        advisory=cfg.advisory,
        car_km_equiv=car_km_equiv,
        car_m_equiv=car_m_equiv,
    )

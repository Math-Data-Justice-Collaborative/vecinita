import type { EnergyEstimate } from "./types";

/** Parse optional energy_estimate from a stream done payload. */
export function parseEnergyEstimate(
  value: unknown,
): EnergyEstimate | undefined {
  if (typeof value !== "object" || value === null) {
    return undefined;
  }
  const o = value as Record<string, unknown>;
  if (
    typeof o["wh"] !== "number" ||
    typeof o["g_co2e"] !== "number" ||
    typeof o["car_km_equiv"] !== "number" ||
    typeof o["car_m_equiv"] !== "number" ||
    typeof o["advisory"] !== "string" ||
    o["method"] !== "tdp_util_walltime_v1"
  ) {
    return undefined;
  }
  return {
    wh: o["wh"],
    g_co2e: o["g_co2e"],
    method: "tdp_util_walltime_v1",
    advisory: o["advisory"],
    car_km_equiv: o["car_km_equiv"],
    car_m_equiv: o["car_m_equiv"],
  };
}

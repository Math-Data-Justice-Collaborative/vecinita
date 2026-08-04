import { describe, expect, it } from "vitest";

import { parseEnergyEstimate } from "./energyEstimate";

describe("parseEnergyEstimate (F65)", () => {
  const valid = {
    wh: 0.02,
    g_co2e: 0.008,
    method: "tdp_util_walltime_v1",
    advisory: "Approximate.",
    car_km_equiv: 0.00003,
    car_m_equiv: 0.03,
  };

  it("returns EnergyEstimate for a valid payload", () => {
    expect(parseEnergyEstimate(valid)).toEqual(valid);
  });

  it("returns undefined for null, non-objects, and primitives", () => {
    expect(parseEnergyEstimate(null)).toBeUndefined();
    expect(parseEnergyEstimate(undefined)).toBeUndefined();
    expect(parseEnergyEstimate("x")).toBeUndefined();
    expect(parseEnergyEstimate(1)).toBeUndefined();
  });

  it("returns undefined when method is not tdp_util_walltime_v1", () => {
    expect(parseEnergyEstimate({ ...valid, method: "other" })).toBeUndefined();
  });

  it("returns undefined when required numeric or advisory fields are wrong", () => {
    expect(parseEnergyEstimate({ ...valid, wh: "1" })).toBeUndefined();
    expect(parseEnergyEstimate({ ...valid, g_co2e: null })).toBeUndefined();
    expect(
      parseEnergyEstimate({ ...valid, car_km_equiv: undefined }),
    ).toBeUndefined();
    expect(parseEnergyEstimate({ ...valid, car_m_equiv: "0" })).toBeUndefined();
    expect(parseEnergyEstimate({ ...valid, advisory: 1 })).toBeUndefined();
  });
});

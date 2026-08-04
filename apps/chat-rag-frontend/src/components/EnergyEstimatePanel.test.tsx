import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { EnergyEstimate } from "../api/types";
import { renderWithLocale } from "../test/renderWithLocale";
import { EnergyEstimatePanel } from "./EnergyEstimatePanel";

const SAMPLE: EnergyEstimate = {
  wh: 0.0194,
  g_co2e: 0.0075,
  method: "tdp_util_walltime_v1",
  advisory: "Approximate energy and CO2e from GPU TDP.",
  car_km_equiv: 0.0000299,
  car_m_equiv: 0.0299,
};

describe("EnergyEstimatePanel (TC-220, TC-231 / F65)", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows Wh/gCO2e chip, car meters/miles, and advisory (EN)", () => {
    renderWithLocale(<EnergyEstimatePanel estimate={SAMPLE} locale="en" />);

    const root = screen.getByTestId("energy-estimate");
    expect(root).toBeInTheDocument();
    expect(screen.getByTestId("energy-chip")).toHaveTextContent(/Wh/i);
    expect(screen.getByTestId("energy-chip")).toHaveTextContent(
      /gCO2e|g CO₂e|gCO₂e/i,
    );
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent(/≈/);
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent(/m/);
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent(/mi/);
    expect(screen.getByTestId("energy-advisory")).toHaveTextContent(
      /approximate/i,
    );
  });

  it("renders Spanish advisory and use-guide copy", () => {
    renderWithLocale(<EnergyEstimatePanel estimate={SAMPLE} locale="es" />);
    expect(screen.getByTestId("energy-advisory")).toHaveTextContent(
      /aproximad/i,
    );
    fireEvent.click(screen.getByTestId("energy-use-guide-toggle"));
    expect(screen.getByTestId("energy-use-guide")).toBeInTheDocument();
    expect(screen.getByTestId("energy-use-guide")).toHaveTextContent(
      /consulta|pregunta|energ/i,
    );
  });

  it("toggles use guide open/closed", () => {
    renderWithLocale(<EnergyEstimatePanel estimate={SAMPLE} locale="en" />);
    expect(screen.queryByTestId("energy-use-guide")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("energy-use-guide-toggle"));
    expect(screen.getByTestId("energy-use-guide")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("energy-use-guide-toggle"));
    expect(screen.queryByTestId("energy-use-guide")).not.toBeInTheDocument();
  });

  it("formats larger Wh/gCO2e and kilometer-scale car distance", () => {
    renderWithLocale(
      <EnergyEstimatePanel
        estimate={{
          ...SAMPLE,
          wh: 1.25,
          g_co2e: 0.48,
          car_km_equiv: 1.5,
          car_m_equiv: 1500,
        }}
        locale="en"
      />,
    );
    expect(screen.getByTestId("energy-chip")).toHaveTextContent("1.25 Wh");
    expect(screen.getByTestId("energy-chip")).toHaveTextContent("0.48 gCO2e");
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent("1500 m");
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent(/mi/);
  });

  it("formats mid-range meters and sub-mile car distance", () => {
    renderWithLocale(
      <EnergyEstimatePanel
        estimate={{
          ...SAMPLE,
          wh: 0.05,
          g_co2e: 0.02,
          car_km_equiv: 0.05,
          car_m_equiv: 50,
        }}
        locale="en"
      />,
    );
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent("50.0 m");
    expect(screen.getByTestId("energy-chip")).toHaveTextContent("0.05 Wh");
  });
});

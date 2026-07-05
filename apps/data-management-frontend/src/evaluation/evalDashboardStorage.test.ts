import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_EXPLORE_LAYOUT,
  EXPLORE_STORAGE_KEY,
  loadEvalDashboardLayout,
  loadEvalExploreLayout,
  saveEvalDashboardLayout,
  saveEvalExploreLayout,
  type EvalDashboardLayout,
  type EvalExploreLayout,
} from "./evalDashboardStorage";

const DASHBOARD_KEY = "vecinita.eval.dashboard.v1";

const TIME_RANGE_DEFAULTS = {
  timeRangePreset: "7D" as const,
  customRangeStart: null,
  customRangeEnd: null,
};

describe("evalDashboardStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("loadEvalDashboardLayout returns defaults when storage is empty", () => {
    const layout = loadEvalDashboardLayout();
    expect(layout.chartType).toBe("line");
    expect(layout.showThresholds).toBe(true);
    expect(layout.selectedMetrics).toEqual([
      "retrieval_relevance",
      "faithfulness",
      "answer_relevancy",
    ]);
  });

  it("loadEvalDashboardLayout merges persisted layout and falls back on invalid JSON", () => {
    const saved: EvalDashboardLayout = {
      collapsedPanels: { faithfulness: true },
      selectedMetrics: ["latency_p95_ms"],
      chartType: "area",
      showThresholds: false,
      ...TIME_RANGE_DEFAULTS,
    };
    localStorage.setItem(DASHBOARD_KEY, JSON.stringify(saved));
    expect(loadEvalDashboardLayout()).toEqual(saved);

    localStorage.setItem(DASHBOARD_KEY, "not-json");
    const fallback = loadEvalDashboardLayout();
    expect(fallback.chartType).toBe("line");
    expect(fallback.selectedMetrics).toEqual([
      "retrieval_relevance",
      "faithfulness",
      "answer_relevancy",
    ]);
  });

  it("loadEvalDashboardLayout uses defaults when selectedMetrics is empty", () => {
    localStorage.setItem(
      DASHBOARD_KEY,
      JSON.stringify({ selectedMetrics: [], chartType: "line" }),
    );
    expect(loadEvalDashboardLayout().selectedMetrics).toEqual([
      "retrieval_relevance",
      "faithfulness",
      "answer_relevancy",
    ]);
  });

  it("loadEvalDashboardLayout treats unknown chartType as line", () => {
    localStorage.setItem(
      DASHBOARD_KEY,
      JSON.stringify({
        collapsedPanels: {},
        selectedMetrics: ["faithfulness"],
        chartType: "bar",
        showThresholds: true,
      }),
    );
    expect(loadEvalDashboardLayout().chartType).toBe("line");
  });

  it("loadEvalDashboardLayout preserves explicit showThresholds false", () => {
    localStorage.setItem(
      DASHBOARD_KEY,
      JSON.stringify({
        collapsedPanels: {},
        selectedMetrics: ["faithfulness"],
        chartType: "line",
        showThresholds: false,
      }),
    );
    expect(loadEvalDashboardLayout().showThresholds).toBe(false);
  });

  it("loadEvalDashboardLayout falls back for unknown time range preset", () => {
    localStorage.setItem(
      DASHBOARD_KEY,
      JSON.stringify({
        collapsedPanels: {},
        selectedMetrics: ["faithfulness"],
        chartType: "line",
        showThresholds: true,
        timeRangePreset: "invalid",
        customRangeStart: 123,
        customRangeEnd: null,
      }),
    );
    const layout = loadEvalDashboardLayout();
    expect(layout.timeRangePreset).toBe("7D");
    expect(layout.customRangeStart).toBeNull();
  });

  it("saveEvalDashboardLayout persists layout and degrades on quota errors", () => {
    const layout: EvalDashboardLayout = {
      collapsedPanels: {},
      selectedMetrics: ["faithfulness"],
      chartType: "line",
      showThresholds: true,
      ...TIME_RANGE_DEFAULTS,
    };
    saveEvalDashboardLayout(layout);
    expect(JSON.parse(localStorage.getItem(DASHBOARD_KEY) ?? "{}")).toEqual(
      layout,
    );

    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => {
      saveEvalDashboardLayout(layout);
    }).not.toThrow();
  });

  it("loadEvalExploreLayout merges persisted axes", () => {
    const saved: EvalExploreLayout = {
      rowAxis: "case_id",
      columnAxis: "pass_fail",
      valueMeasure: "count",
    };
    localStorage.setItem(EXPLORE_STORAGE_KEY, JSON.stringify(saved));
    expect(loadEvalExploreLayout()).toEqual(saved);

    localStorage.setItem(EXPLORE_STORAGE_KEY, "{bad");
    expect(loadEvalExploreLayout()).toEqual(DEFAULT_EXPLORE_LAYOUT);
  });

  it("loadEvalExploreLayout fills missing axis fields from defaults", () => {
    localStorage.setItem(EXPLORE_STORAGE_KEY, JSON.stringify({}));
    expect(loadEvalExploreLayout()).toEqual(DEFAULT_EXPLORE_LAYOUT);
  });

  it("loadEvalExploreLayout returns defaults when storage is empty", () => {
    expect(loadEvalExploreLayout()).toEqual(DEFAULT_EXPLORE_LAYOUT);
  });

  it("saveEvalExploreLayout persists layout and degrades on quota errors", () => {
    const layout: EvalExploreLayout = {
      rowAxis: "metric",
      columnAxis: "locale",
      valueMeasure: "pass_rate",
    };
    saveEvalExploreLayout(layout);
    expect(
      JSON.parse(localStorage.getItem(EXPLORE_STORAGE_KEY) ?? "{}"),
    ).toEqual(layout);

    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() => {
      saveEvalExploreLayout(layout);
    }).not.toThrow();
  });
});

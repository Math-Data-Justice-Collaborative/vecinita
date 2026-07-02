import { describe, expect, it } from "vitest";

import type { EvalTimeseriesPointApi } from "@/api/admin";
import {
  filterEvalTimeseriesPoints,
  formatEvalChartLabel,
  xAxisGranularity,
} from "./evalTimeRange";

const POINTS: EvalTimeseriesPointApi[] = [
  {
    run_id: "00000000-0000-0000-0000-000000000099",
    completed_at: "2026-07-01T12:01:00Z",
    metrics_summary: { retrieval_relevance: 0.9 },
  },
  {
    run_id: "00000000-0000-0000-0000-000000000088",
    completed_at: "2026-07-02T12:01:00Z",
    metrics_summary: { retrieval_relevance: 0.8 },
  },
];

describe("evalTimeRange", () => {
  it("filters points to the last 7 days from a reference now", () => {
    const now = new Date("2026-07-02T18:00:00Z");
    const filtered = filterEvalTimeseriesPoints(POINTS, "7D", null, null, now);
    expect(filtered).toHaveLength(2);
  });

  it("returns empty for custom range outside all points (TC-126)", () => {
    const filtered = filterEvalTimeseriesPoints(
      POINTS,
      "custom",
      "2025-01-01",
      "2025-01-31",
    );
    expect(filtered).toHaveLength(0);
  });

  it("uses hour granularity for 1D and month for 1Y", () => {
    expect(xAxisGranularity("1D")).toBe("hour");
    expect(xAxisGranularity("1Y")).toBe("month");
    expect(xAxisGranularity("7D")).toBe("day");
  });

  it("formats chart labels by granularity", () => {
    const hourLabel = formatEvalChartLabel("2026-07-01T12:01:00Z", "hour");
    expect(hourLabel.length).toBeGreaterThan(0);
    const dayLabel = formatEvalChartLabel("2026-07-01T12:01:00Z", "day");
    expect(dayLabel.length).toBeGreaterThan(0);
    const monthLabel = formatEvalChartLabel("2026-07-01T12:01:00Z", "month");
    expect(monthLabel.length).toBeGreaterThan(0);
  });

  it("returns all points for custom preset without both bounds", () => {
    expect(filterEvalTimeseriesPoints(POINTS, "custom", null, null)).toEqual(
      POINTS,
    );
    expect(
      filterEvalTimeseriesPoints(POINTS, "custom", "invalid", "2026-07-02"),
    ).toEqual(POINTS);
  });

  it("filters points inside a custom date window", () => {
    const filtered = filterEvalTimeseriesPoints(
      POINTS,
      "custom",
      "2026-07-01",
      "2026-07-02",
    );
    expect(filtered).toHaveLength(1);
  });
});

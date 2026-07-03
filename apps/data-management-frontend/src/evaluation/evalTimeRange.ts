import type { EvalTimeseriesPointApi } from "@/api/admin";

export type EvalTimeRangePreset = "1D" | "7D" | "10D" | "1M" | "1Y" | "custom";

export type EvalXAxisGranularity = "hour" | "day" | "month";

const DAY_MS = 24 * 60 * 60 * 1000;

const PRESET_WINDOW_MS: Record<
  Exclude<EvalTimeRangePreset, "custom">,
  number
> = {
  "1D": DAY_MS,
  "7D": 7 * DAY_MS,
  "10D": 10 * DAY_MS,
  "1M": 30 * DAY_MS,
  "1Y": 365 * DAY_MS,
};

export function xAxisGranularity(
  preset: EvalTimeRangePreset,
): EvalXAxisGranularity {
  if (preset === "1D") return "hour";
  if (preset === "1Y") return "month";
  return "day";
}

export function formatEvalChartLabel(
  isoTimestamp: string,
  granularity: EvalXAxisGranularity,
): string {
  const date = new Date(isoTimestamp);
  if (granularity === "hour") {
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    });
  }
  if (granularity === "month") {
    return date.toLocaleString(undefined, { month: "short", year: "numeric" });
  }
  return date.toLocaleString(undefined, { month: "short", day: "numeric" });
}

export function filterEvalTimeseriesPoints(
  points: EvalTimeseriesPointApi[],
  preset: EvalTimeRangePreset,
  customStart: string | null | undefined,
  customEnd: string | null | undefined,
  now: Date = new Date(),
): EvalTimeseriesPointApi[] {
  if (preset === "custom") {
    if (!customStart || !customEnd) return points;
    const startMs = new Date(customStart).getTime();
    const endMs = new Date(customEnd).getTime();
    if (Number.isNaN(startMs) || Number.isNaN(endMs)) return points;
    return points.filter((point) => {
      const completedMs = new Date(point.completed_at).getTime();
      return completedMs >= startMs && completedMs <= endMs;
    });
  }
  const cutoff = now.getTime() - PRESET_WINDOW_MS[preset];
  return points.filter((point) => {
    return new Date(point.completed_at).getTime() >= cutoff;
  });
}

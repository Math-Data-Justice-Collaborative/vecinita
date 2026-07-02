const STORAGE_KEY = "vecinita.eval.dashboard.v1";

export type EvalChartType = "line" | "area" | "scatter";

export type EvalTimeRangePreset = "1D" | "7D" | "10D" | "1M" | "1Y" | "custom";

export interface EvalDashboardLayout {
  collapsedPanels: Record<string, boolean>;
  selectedMetrics: string[];
  chartType: EvalChartType;
  showThresholds: boolean;
  timeRangePreset: EvalTimeRangePreset;
  customRangeStart: string | null;
  customRangeEnd: string | null;
}

const DEFAULT_LAYOUT: EvalDashboardLayout = {
  collapsedPanels: {},
  selectedMetrics: ["retrieval_relevance", "faithfulness", "answer_relevancy"],
  chartType: "line",
  showThresholds: true,
  timeRangePreset: "7D",
  customRangeStart: null,
  customRangeEnd: null,
};

export function loadEvalDashboardLayout(): EvalDashboardLayout {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_LAYOUT;
    const parsed = JSON.parse(raw) as Partial<EvalDashboardLayout>;
    return {
      collapsedPanels: parsed.collapsedPanels ?? {},
      selectedMetrics:
        parsed.selectedMetrics && parsed.selectedMetrics.length > 0
          ? parsed.selectedMetrics
          : DEFAULT_LAYOUT.selectedMetrics,
      chartType:
        parsed.chartType === "area" || parsed.chartType === "scatter"
          ? parsed.chartType
          : "line",
      showThresholds: parsed.showThresholds ?? true,
      timeRangePreset:
        parsed.timeRangePreset === "1D" ||
        parsed.timeRangePreset === "7D" ||
        parsed.timeRangePreset === "10D" ||
        parsed.timeRangePreset === "1M" ||
        parsed.timeRangePreset === "1Y" ||
        parsed.timeRangePreset === "custom"
          ? parsed.timeRangePreset
          : DEFAULT_LAYOUT.timeRangePreset,
      customRangeStart:
        typeof parsed.customRangeStart === "string"
          ? parsed.customRangeStart
          : null,
      customRangeEnd:
        typeof parsed.customRangeEnd === "string" ? parsed.customRangeEnd : null,
    };
  } catch {
    return DEFAULT_LAYOUT;
  }
}

export function saveEvalDashboardLayout(layout: EvalDashboardLayout): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
  } catch {
    // degrade silently per ADR-004 localStorage policy
  }
}

export const EXPLORE_STORAGE_KEY = "vecinita.eval.explore.v1";

export type EvalPivotAxis =
  | "locale"
  | "case_id"
  | "metric"
  | "pass_fail"
  | "run_date";

export type EvalPivotValue = "avg_score" | "count" | "pass_rate";

export interface EvalExploreLayout {
  rowAxis: EvalPivotAxis;
  columnAxis: EvalPivotAxis;
  valueMeasure: EvalPivotValue;
}

export const DEFAULT_EXPLORE_LAYOUT: EvalExploreLayout = {
  rowAxis: "locale",
  columnAxis: "metric",
  valueMeasure: "avg_score",
};

export function loadEvalExploreLayout(): EvalExploreLayout {
  try {
    const raw = localStorage.getItem(EXPLORE_STORAGE_KEY);
    if (!raw) return DEFAULT_EXPLORE_LAYOUT;
    const parsed = JSON.parse(raw) as Partial<EvalExploreLayout>;
    return {
      rowAxis: parsed.rowAxis ?? DEFAULT_EXPLORE_LAYOUT.rowAxis,
      columnAxis: parsed.columnAxis ?? DEFAULT_EXPLORE_LAYOUT.columnAxis,
      valueMeasure: parsed.valueMeasure ?? DEFAULT_EXPLORE_LAYOUT.valueMeasure,
    };
  } catch {
    return DEFAULT_EXPLORE_LAYOUT;
  }
}

export function saveEvalExploreLayout(layout: EvalExploreLayout): void {
  try {
    localStorage.setItem(EXPLORE_STORAGE_KEY, JSON.stringify(layout));
  } catch {
    // degrade silently
  }
}

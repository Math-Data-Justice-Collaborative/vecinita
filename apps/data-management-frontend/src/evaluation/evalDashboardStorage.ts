const STORAGE_KEY = "vecinita.eval.dashboard.v1";

export type EvalChartType = "line" | "area";

export interface EvalDashboardLayout {
  collapsedPanels: Record<string, boolean>;
  selectedMetrics: string[];
  chartType: EvalChartType;
  showThresholds: boolean;
}

const DEFAULT_LAYOUT: EvalDashboardLayout = {
  collapsedPanels: {},
  selectedMetrics: [
    "retrieval_relevance",
    "faithfulness",
    "answer_relevancy",
  ],
  chartType: "line",
  showThresholds: true,
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
      chartType: parsed.chartType === "area" ? "area" : "line",
      showThresholds: parsed.showThresholds ?? true,
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

import type { EvalRunDetailApi } from "@/api/admin";

import type {
  EvalExploreLayout,
  EvalPivotAxis,
  EvalPivotValue,
} from "./evalDashboardStorage";

export interface EvalExploreRow {
  run_id: string;
  run_date: string;
  case_id: string;
  locale: string;
  metric: string;
  pass_fail: string;
  score: number | null;
}

const BUILTIN_METRICS = [
  "retrieval",
  "faithfulness",
  "answer_relevancy",
  "latency_ms",
] as const;

export function flattenRunsForExplore(
  details: EvalRunDetailApi[],
): EvalExploreRow[] {
  const rows: EvalExploreRow[] = [];
  for (const detail of details) {
    const runDate = detail.run_id.slice(0, 8);
    for (const item of detail.items) {
      rows.push({
        run_id: detail.run_id,
        run_date: runDate,
        case_id: item.case_id,
        locale: item.locale,
        metric: "retrieval",
        pass_fail: item.metrics.retrieval_pass ? "pass" : "fail",
        score: item.metrics.retrieval_pass ? 1 : 0,
      });
      rows.push({
        run_id: detail.run_id,
        run_date: runDate,
        case_id: item.case_id,
        locale: item.locale,
        metric: "faithfulness",
        pass_fail:
          item.metrics.faithfulness !== null &&
          item.metrics.faithfulness !== undefined &&
          item.metrics.faithfulness >= 0.6
            ? "pass"
            : "fail",
        score: item.metrics.faithfulness ?? null,
      });
      rows.push({
        run_id: detail.run_id,
        run_date: runDate,
        case_id: item.case_id,
        locale: item.locale,
        metric: "answer_relevancy",
        pass_fail:
          item.metrics.answer_relevancy !== null &&
          item.metrics.answer_relevancy !== undefined &&
          item.metrics.answer_relevancy >= 0.6
            ? "pass"
            : "fail",
        score: item.metrics.answer_relevancy ?? null,
      });
      rows.push({
        run_id: detail.run_id,
        run_date: runDate,
        case_id: item.case_id,
        locale: item.locale,
        metric: "latency_ms",
        pass_fail:
          item.metrics.latency_ms <= 30_000 ? "pass" : "fail",
        score: item.metrics.latency_ms,
      });
      const custom = item.metrics.custom_scores;
      if (custom) {
        for (const [slug, value] of Object.entries(custom)) {
          rows.push({
            run_id: detail.run_id,
            run_date: runDate,
            case_id: item.case_id,
            locale: item.locale,
            metric: slug,
            pass_fail: value >= 0.6 ? "pass" : "fail",
            score: value,
          });
        }
      }
    }
  }
  return rows.slice(0, 500);
}

function axisValue(row: EvalExploreRow, axis: EvalPivotAxis): string {
  if (axis === "locale") return row.locale;
  if (axis === "case_id") return row.case_id;
  if (axis === "metric") return row.metric;
  if (axis === "pass_fail") return row.pass_fail;
  return row.run_date;
}

export interface PivotCell {
  value: number | null;
  count: number;
}

export function buildPivotTable(
  rows: EvalExploreRow[],
  layout: EvalExploreLayout,
): { rowKeys: string[]; colKeys: string[]; cells: Map<string, PivotCell> } {
  const rowKeys = [...new Set(rows.map((r) => axisValue(r, layout.rowAxis)))].sort();
  const colKeys = [...new Set(rows.map((r) => axisValue(r, layout.columnAxis)))].sort();
  const cells = new Map<string, PivotCell>();

  for (const rowKey of rowKeys) {
    for (const colKey of colKeys) {
      const matching = rows.filter(
        (r) =>
          axisValue(r, layout.rowAxis) === rowKey &&
          axisValue(r, layout.columnAxis) === colKey &&
          r.score !== null,
      );
      const key = `${rowKey}::${colKey}`;
      if (matching.length === 0) {
        cells.set(key, { value: null, count: 0 });
        continue;
      }
      if (layout.valueMeasure === "count") {
        cells.set(key, { value: matching.length, count: matching.length });
      } else if (layout.valueMeasure === "pass_rate") {
        const passes = matching.filter((r) => r.pass_fail === "pass").length;
        cells.set(key, {
          value: passes / matching.length,
          count: matching.length,
        });
      } else {
        const scores = matching
          .map((r) => r.score)
          .filter((s): s is number => s !== null);
        const avg =
          scores.length > 0
            ? scores.reduce((a, b) => a + b, 0) / scores.length
            : null;
        cells.set(key, { value: avg, count: matching.length });
      }
    }
  }

  return { rowKeys, colKeys, cells };
}

export function metricLabel(metric: string): string {
  if (metric === "retrieval") return "Retrieval";
  if (metric === "faithfulness") return "Faithfulness";
  if (metric === "answer_relevancy") return "Answer relevancy";
  if (metric === "latency_ms") return "Latency (ms)";
  return metric;
}

export const PIVOT_AXES: EvalPivotAxis[] = [
  "locale",
  "case_id",
  "metric",
  "pass_fail",
  "run_date",
];

export const PIVOT_VALUES: EvalPivotValue[] = [
  "avg_score",
  "count",
  "pass_rate",
];

export const BUILTIN_METRIC_IDS = BUILTIN_METRICS;

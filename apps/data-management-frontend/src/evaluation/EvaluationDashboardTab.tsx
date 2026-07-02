import { useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  type EvalTimeseriesResponseApi,
  fetchEvalTimeseries,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";

import { EvalMetricChart } from "./EvalMetricChart";
import {
  filterEvalTimeseriesPoints,
  xAxisGranularity,
  type EvalTimeRangePreset,
} from "./evalTimeRange";
import {
  type EvalDashboardLayout,
  loadEvalDashboardLayout,
  saveEvalDashboardLayout,
} from "./evalDashboardStorage";

const TIME_RANGE_PRESETS: EvalTimeRangePreset[] = [
  "1D",
  "7D",
  "10D",
  "1M",
  "1Y",
  "custom",
];

function nextChartType(current: EvalDashboardLayout["chartType"]) {
  if (current === "line") return "area";
  if (current === "area") return "scatter";
  return "line";
}

function chartTypeLabelKey(
  chartType: EvalDashboardLayout["chartType"],
):
  | "admin.evaluation.dashboard.chartLine"
  | "admin.evaluation.dashboard.chartArea"
  | "admin.evaluation.dashboard.chartScatter" {
  if (chartType === "area") return "admin.evaluation.dashboard.chartArea";
  if (chartType === "scatter") return "admin.evaluation.dashboard.chartScatter";
  return "admin.evaluation.dashboard.chartLine";
}

function metricLabel(
  metricId: string,
  tr: ReturnType<typeof useAdminT>,
): string {
  if (metricId === "retrieval_relevance") {
    return tr("admin.evaluation.metric.retrieval");
  }
  if (metricId === "faithfulness") {
    return tr("admin.evaluation.metric.faithfulness");
  }
  if (metricId === "answer_relevancy") {
    return tr("admin.evaluation.metric.answerRelevancy");
  }
  if (metricId === "latency_p95_ms") {
    return tr("admin.evaluation.metric.latencyP95");
  }
  return metricId;
}

export function EvaluationDashboardTab() {
  const tr = useAdminT();
  const [data, setData] = useState<EvalTimeseriesResponseApi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [layout, setLayout] = useState<EvalDashboardLayout>(() =>
    loadEvalDashboardLayout(),
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const series = await fetchEvalTimeseries(client);
      setData(series);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.dashboard.loadFailed"),
      );
    } finally {
      setLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    void load();
  }, [load]);

  const updateLayout = useCallback((next: EvalDashboardLayout) => {
    setLayout(next);
    saveEvalDashboardLayout(next);
  }, []);

  const toggleMetric = useCallback(
    (metricId: string) => {
      const selected = layout.selectedMetrics.includes(metricId)
        ? layout.selectedMetrics.filter((m) => m !== metricId)
        : [...layout.selectedMetrics, metricId];
      updateLayout({ ...layout, selectedMetrics: selected });
    },
    [layout, updateLayout],
  );

  const togglePanel = useCallback(
    (metricId: string) => {
      updateLayout({
        ...layout,
        collapsedPanels: {
          ...layout.collapsedPanels,
          [metricId]: !layout.collapsedPanels[metricId],
        },
      });
    },
    [layout, updateLayout],
  );

  if (loading) {
    return (
      <div data-testid="evaluation-dashboard-tab">
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="evaluation-dashboard-tab">
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      </div>
    );
  }

  const available = data?.available_metrics ?? [];
  const allPoints = data?.points ?? [];
  const filteredPoints = filterEvalTimeseriesPoints(
    allPoints,
    layout.timeRangePreset,
    layout.customRangeStart,
    layout.customRangeEnd,
  );
  const granularity = xAxisGranularity(layout.timeRangePreset);
  const customRangeEmpty =
    layout.timeRangePreset === "custom" &&
    layout.customRangeStart &&
    layout.customRangeEnd &&
    filteredPoints.length === 0 &&
    allPoints.length > 0;

  return (
    <div className="space-y-4" data-testid="evaluation-dashboard-tab">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">
          {tr("admin.evaluation.dashboard.timeRange")}
        </span>
        {TIME_RANGE_PRESETS.map((preset) => (
          <Button
            key={preset}
            type="button"
            size="sm"
            variant={
              layout.timeRangePreset === preset ? "default" : "outline"
            }
            onClick={() => {
              updateLayout({ ...layout, timeRangePreset: preset });
            }}
            data-testid={`eval-time-preset-${preset}`}
          >
            {preset === "custom"
              ? tr("admin.evaluation.dashboard.timeCustom")
              : preset}
          </Button>
        ))}
        {layout.timeRangePreset === "custom" ? (
          <>
            <input
              type="date"
              className="rounded-md border px-2 py-1 text-sm"
              value={layout.customRangeStart ?? ""}
              onChange={(event) => {
                updateLayout({
                  ...layout,
                  customRangeStart: event.target.value || null,
                });
              }}
              data-testid="eval-custom-range-start"
            />
            <input
              type="date"
              className="rounded-md border px-2 py-1 text-sm"
              value={layout.customRangeEnd ?? ""}
              onChange={(event) => {
                updateLayout({
                  ...layout,
                  customRangeEnd: event.target.value || null,
                });
              }}
              data-testid="eval-custom-range-end"
            />
          </>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">
          {tr("admin.evaluation.dashboard.metrics")}
        </span>
        {available.map((metricId) => (
          <Button
            key={metricId}
            type="button"
            size="sm"
            variant={
              layout.selectedMetrics.includes(metricId) ? "default" : "outline"
            }
            onClick={() => {
              toggleMetric(metricId);
            }}
            data-testid={`eval-metric-toggle-${metricId}`}
          >
            {metricLabel(metricId, tr)}
          </Button>
        ))}
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => {
            updateLayout({
              ...layout,
              chartType: nextChartType(layout.chartType),
            });
          }}
          data-testid="eval-chart-type-toggle"
        >
          {tr(chartTypeLabelKey(layout.chartType))}
        </Button>
        <Button
          type="button"
          size="sm"
          variant={layout.showThresholds ? "default" : "outline"}
          onClick={() => {
            updateLayout({
              ...layout,
              showThresholds: !layout.showThresholds,
            });
          }}
        >
          {tr("admin.evaluation.dashboard.thresholds")}
        </Button>
      </div>

      {customRangeEmpty ? (
        <p
          className="text-muted-foreground"
          data-testid="eval-custom-range-empty"
        >
          {tr("admin.evaluation.dashboard.customRangeEmpty")}
        </p>
      ) : null}

      {!customRangeEmpty && filteredPoints.length === 0 ? (
        <p className="text-muted-foreground">
          {tr("admin.evaluation.dashboard.noData")}
        </p>
      ) : null}

      {!customRangeEmpty &&
        layout.selectedMetrics.map((metricId) => {
        const collapsed = layout.collapsedPanels[metricId] ?? false;
        return (
          <Card key={metricId} data-testid={`eval-panel-${metricId}`}>
            <CardHeader className="flex flex-row items-center justify-between py-3">
              <CardTitle className="text-base">
                {metricLabel(metricId, tr)}
              </CardTitle>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-expanded={!collapsed}
                onClick={() => {
                  togglePanel(metricId);
                }}
                data-testid={`eval-panel-toggle-${metricId}`}
              >
                {collapsed ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronUp className="h-4 w-4" />
                )}
              </Button>
            </CardHeader>
            <CardContent className={cn(collapsed && "hidden")}>
              <EvalMetricChart
                points={filteredPoints}
                metricId={metricId}
                metricLabel={metricLabel(metricId, tr)}
                chartType={layout.chartType}
                showThreshold={layout.showThresholds}
                xAxisGranularity={granularity}
              />
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

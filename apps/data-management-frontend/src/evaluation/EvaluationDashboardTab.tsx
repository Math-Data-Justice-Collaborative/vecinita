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
  type EvalDashboardLayout,
  loadEvalDashboardLayout,
  saveEvalDashboardLayout,
} from "./evalDashboardStorage";

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
  const points = data?.points ?? [];

  return (
    <div className="space-y-4" data-testid="evaluation-dashboard-tab">
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
              chartType: layout.chartType === "line" ? "area" : "line",
            });
          }}
          data-testid="eval-chart-type-toggle"
        >
          {layout.chartType === "line"
            ? tr("admin.evaluation.dashboard.chartLine")
            : tr("admin.evaluation.dashboard.chartArea")}
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

      {points.length === 0 ? (
        <p className="text-muted-foreground">
          {tr("admin.evaluation.dashboard.noData")}
        </p>
      ) : null}

      {layout.selectedMetrics.map((metricId) => {
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
                points={points}
                metricId={metricId}
                metricLabel={metricLabel(metricId, tr)}
                chartType={layout.chartType}
                showThreshold={layout.showThresholds}
              />
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

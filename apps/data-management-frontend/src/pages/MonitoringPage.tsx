/**
 * F84 Monitoring — privacy-safe ingest/chat/embed rates (UJ-088).
 * [Corpus: feature-list.md §F84] [Spec: docs/adr/ADR-055-operational-monitoring-grafana-loki.md]
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw } from "lucide-react";
import { ActionIcon } from "vecinita-frontend-ui";
import type { StringMessageKey } from "vecinita-frontend-i18n";

import {
  type MetricsSummary,
  type MetricsTimeseries,
  type MetricsWindow,
  type MetricsWorkloadStats,
  fetchMetricsSummary,
  fetchMetricsTimeseries,
} from "@/api/admin";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";

const WINDOWS: MetricsWindow[] = ["1h", "24h", "7d", "30d"];

const WORKLOADS = ["ingest", "chat", "embed"] as const;

const WORKLOAD_TITLE: Record<(typeof WORKLOADS)[number], StringMessageKey> = {
  ingest: "admin.monitoring.workload.ingest",
  chat: "admin.monitoring.workload.chat",
  embed: "admin.monitoring.workload.embed",
};

const WINDOW_LABEL: Record<MetricsWindow, StringMessageKey> = {
  "1h": "admin.monitoring.window.1h",
  "24h": "admin.monitoring.window.24h",
  "7d": "admin.monitoring.window.7d",
  "30d": "admin.monitoring.window.30d",
};

function formatSuccessPercent(rate: number): string {
  return `${String(Math.round(rate * 100))}%`;
}

function workloadStats(
  summary: MetricsSummary,
  key: (typeof WORKLOADS)[number],
): MetricsWorkloadStats {
  return summary.workloads[key];
}

export function MonitoringPage() {
  const tr = useAdminT();
  const [window, setWindow] = useState<MetricsWindow>("24h");
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [timeseries, setTimeseries] = useState<MetricsTimeseries | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isActive: () => boolean, selected: MetricsWindow) => {
      setLoading(true);
      setError(null);
      try {
        const client = requireCorpusConfig();
        const [summaryData, seriesData] = await Promise.all([
          fetchMetricsSummary(client, selected),
          fetchMetricsTimeseries(client, "ingest_success_rate", selected),
        ]);
        /* v8 ignore next -- unmount race */
        if (!isActive()) {
          return;
        }
        setSummary(summaryData);
        setTimeseries(seriesData);
      } catch (err) {
        /* v8 ignore next -- unmount race */
        if (!isActive()) {
          return;
        }
        setError(
          err instanceof Error
            ? err.message
            : tr("admin.monitoring.loadFailed"),
        );
      } finally {
        /* v8 ignore next -- unmount race */
        if (isActive()) {
          setLoading(false);
        }
      }
    },
    [tr],
  );

  useEffect(() => {
    let active = true;
    void load(() => active, window);
    return () => {
      active = false;
    };
  }, [load, window]);

  if (!summary) {
    return (
      <div className="space-y-6" data-testid="monitoring-page">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.monitoring.title")}
          </h2>
          {error == null ? (
            <p className="text-muted-foreground">
              {tr("admin.monitoring.subtitle")}
            </p>
          ) : null}
        </div>
        {error != null ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : (
          <p className="text-muted-foreground">{tr("shared.loading")}</p>
        )}
      </div>
    );
  }

  /* v8 ignore next -- timeseries is set atomically with summary */
  if (timeseries == null) {
    return null;
  }

  const buckets = timeseries.buckets;

  return (
    <div className="space-y-6" data-testid="monitoring-page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.monitoring.title")}
          </h2>
          <p className="text-muted-foreground">
            {tr("admin.monitoring.subtitle")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">
              {tr("admin.monitoring.windowLabel")}
            </span>
            <select
              data-testid="monitoring-window"
              aria-label={tr("admin.monitoring.windowLabel")}
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              value={window}
              onChange={(event) => {
                setWindow(event.target.value as MetricsWindow);
              }}
            >
              {WINDOWS.map((w) => (
                <option key={w} value={w}>
                  {tr(WINDOW_LABEL[w])}
                </option>
              ))}
            </select>
          </label>
          <Button
            variant="outline"
            size="sm"
            data-testid="monitoring-refresh"
            onClick={() => {
              void load(() => true, window);
            }}
            disabled={loading}
            aria-label={tr("admin.monitoring.refreshAria")}
          >
            <ActionIcon
              motion="spin"
              pending={loading}
              className="mr-2 inline-flex"
            >
              <RefreshCw className="h-4 w-4" />
            </ActionIcon>
            {tr("shared.refresh")}
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link to="/jobs" data-testid="monitoring-view-jobs">
              {tr("admin.monitoring.viewJobs")}
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {WORKLOADS.map((key) => {
          const stats = workloadStats(summary, key);
          return (
            <Card key={key} data-testid={`monitoring-card-${key}`}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">
                  {tr(WORKLOAD_TITLE[key])}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <p className="text-3xl font-bold tracking-tight">
                  {formatSuccessPercent(stats.success_rate)}
                </p>
                <p className="text-sm text-muted-foreground">
                  {tr("admin.monitoring.successRate")}
                </p>
                <p className="text-sm">
                  {tr("admin.monitoring.total")}: {stats.total}
                </p>
                <p className="text-sm">
                  {tr("admin.monitoring.failed")}: {stats.failed}
                </p>
                {key === "chat" && stats.no_context != null ? (
                  <p className="text-sm text-muted-foreground">
                    {tr("admin.monitoring.noContext")}: {stats.no_context}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {tr("admin.monitoring.chartTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            data-testid="monitoring-timeseries"
            role="img"
            aria-label={tr("admin.monitoring.chartTitle")}
            className="space-y-2"
          >
            {buckets.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                {tr("admin.monitoring.chartEmpty")}
              </p>
            ) : (
              buckets.map((bucket) => (
                <div key={bucket.t} className="flex items-center gap-3 text-sm">
                  <span className="w-36 shrink-0 truncate text-muted-foreground">
                    {bucket.t}
                  </span>
                  <div className="h-2 flex-1 overflow-hidden rounded bg-muted">
                    <div
                      className="h-full rounded bg-primary"
                      style={{
                        width: `${String(Math.round(bucket.success_rate * 100))}%`,
                      }}
                    />
                  </div>
                  <span className="w-12 shrink-0 text-right tabular-nums">
                    {formatSuccessPercent(bucket.success_rate)}
                  </span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card data-testid="monitoring-errors">
        <CardHeader>
          <CardTitle className="text-base">
            {tr("admin.monitoring.errorsTitle")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {summary.top_error_codes.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {tr("admin.monitoring.errorsEmpty")}
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{tr("admin.monitoring.errorWorkload")}</TableHead>
                  <TableHead>{tr("admin.monitoring.errorCode")}</TableHead>
                  <TableHead className="text-right">
                    {tr("admin.monitoring.errorCount")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summary.top_error_codes.map((row) => (
                  <TableRow key={`${row.workload}-${row.error_code}`}>
                    <TableCell>{row.workload}</TableCell>
                    <TableCell>{row.error_code}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {row.count}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

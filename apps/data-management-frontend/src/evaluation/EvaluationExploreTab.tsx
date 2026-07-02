import { useCallback, useEffect, useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  type EvalRunDetailApi,
  type EvalRunListItemApi,
  fetchEvalRunDetail,
  fetchEvalRuns,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";

import {
  type EvalExploreLayout,
  type EvalPivotAxis,
  type EvalPivotValue,
  DEFAULT_EXPLORE_LAYOUT,
  loadEvalExploreLayout,
  saveEvalExploreLayout,
} from "./evalDashboardStorage";
import {
  PIVOT_AXES,
  PIVOT_VALUES,
  buildPivotTable,
  flattenRunsForExplore,
} from "./evalPivot";

function formatCellValue(
  value: number | null,
  measure: EvalPivotValue,
): string {
  if (value === null) return "—";
  if (measure === "count") return String(Math.round(value));
  if (measure === "pass_rate") return `${String(Math.round(value * 100))}%`;
  if (value <= 1) return value.toFixed(2);
  return String(Math.round(value));
}

function axisLabel(
  axis: EvalPivotAxis,
  tr: ReturnType<typeof useAdminT>,
): string {
  if (axis === "locale") return tr("admin.evaluation.explore.axis.locale");
  if (axis === "case_id") return tr("admin.evaluation.explore.axis.case_id");
  if (axis === "metric") return tr("admin.evaluation.explore.axis.metric");
  if (axis === "pass_fail")
    return tr("admin.evaluation.explore.axis.pass_fail");
  return tr("admin.evaluation.explore.axis.run_date");
}

function valueLabel(
  measure: EvalPivotValue,
  tr: ReturnType<typeof useAdminT>,
): string {
  if (measure === "avg_score")
    return tr("admin.evaluation.explore.value.avg_score");
  if (measure === "count") return tr("admin.evaluation.explore.value.count");
  return tr("admin.evaluation.explore.value.pass_rate");
}

export function EvaluationExploreTab() {
  const tr = useAdminT();
  const [layout, setLayout] = useState<EvalExploreLayout>(() =>
    loadEvalExploreLayout(),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [details, setDetails] = useState<EvalRunDetailApi[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const list = await fetchEvalRuns(client);
      const completed = list.items.filter(
        (item: EvalRunListItemApi) => item.status === "completed",
      );
      const loaded = await Promise.all(
        completed
          .slice(0, 20)
          .map((item) => fetchEvalRunDetail(client, item.run_id)),
      );
      setDetails(loaded);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : tr("admin.evaluation.explore.loadFailed"),
      );
    } finally {
      setLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    void load();
  }, [load]);

  const updateLayout = useCallback((next: EvalExploreLayout) => {
    setLayout(next);
    saveEvalExploreLayout(next);
  }, []);

  const flatRows = useMemo(() => flattenRunsForExplore(details), [details]);
  const pivot = useMemo(
    () => buildPivotTable(flatRows, layout),
    [flatRows, layout],
  );

  const exportCsv = useCallback(() => {
    const header = ["", ...pivot.colKeys].join(",");
    const lines = pivot.rowKeys.map((rowKey) => {
      const cells = pivot.colKeys.map((colKey) => {
        const cell = pivot.cells.get(`${rowKey}::${colKey}`);
        return formatCellValue(cell?.value ?? null, layout.valueMeasure);
      });
      return [rowKey, ...cells].join(",");
    });
    const csv = [header, ...lines].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "eval-explore.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }, [layout.valueMeasure, pivot]);

  if (loading) {
    return (
      <div data-testid="evaluation-explore-tab">
        <p className="text-muted-foreground">{tr("shared.loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="evaluation-explore-tab">
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="evaluation-explore-tab">
      <div className="flex flex-wrap gap-4">
        <label className="flex flex-col gap-1 text-sm">
          <span>{tr("admin.evaluation.explore.rowAxis")}</span>
          <select
            className="rounded-md border bg-background px-2 py-1"
            value={layout.rowAxis}
            onChange={(event) => {
              updateLayout({
                ...layout,
                rowAxis: event.target.value as EvalPivotAxis,
              });
            }}
            data-testid="eval-pivot-row-axis"
          >
            {PIVOT_AXES.map((axis) => (
              <option key={axis} value={axis}>
                {axisLabel(axis, tr)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span>{tr("admin.evaluation.explore.colAxis")}</span>
          <select
            className="rounded-md border bg-background px-2 py-1"
            value={layout.columnAxis}
            onChange={(event) => {
              updateLayout({
                ...layout,
                columnAxis: event.target.value as EvalPivotAxis,
              });
            }}
            data-testid="eval-pivot-col-axis"
          >
            {PIVOT_AXES.map((axis) => (
              <option key={axis} value={axis}>
                {axisLabel(axis, tr)}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span>{tr("admin.evaluation.explore.valueAxis")}</span>
          <select
            className="rounded-md border bg-background px-2 py-1"
            value={layout.valueMeasure}
            onChange={(event) => {
              updateLayout({
                ...layout,
                valueMeasure: event.target.value as EvalPivotValue,
              });
            }}
            data-testid="eval-pivot-value-axis"
          >
            {PIVOT_VALUES.map((value) => (
              <option key={value} value={value}>
                {valueLabel(value, tr)}
              </option>
            ))}
          </select>
        </label>
        <Button
          type="button"
          variant="outline"
          className="self-end"
          onClick={() => {
            exportCsv();
          }}
          data-testid="eval-explore-export"
        >
          {tr("admin.evaluation.explore.exportCsv")}
        </Button>
        <Button
          type="button"
          variant="ghost"
          className="self-end"
          onClick={() => {
            updateLayout(DEFAULT_EXPLORE_LAYOUT);
          }}
        >
          {tr("admin.evaluation.explore.reset")}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.evaluation.explore.title")}</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {flatRows.length === 0 ? (
            <p className="text-muted-foreground">
              {tr("admin.evaluation.explore.noData")}
            </p>
          ) : (
            <Table data-testid="eval-pivot-table">
              <TableHeader>
                <TableRow>
                  <TableHead>{axisLabel(layout.rowAxis, tr)}</TableHead>
                  {pivot.colKeys.map((col) => (
                    <TableHead key={col}>{col}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {pivot.rowKeys.map((rowKey) => (
                  <TableRow key={rowKey}>
                    <TableCell className="font-medium">{rowKey}</TableCell>
                    {pivot.colKeys.map((colKey) => {
                      const cell = pivot.cells.get(`${rowKey}::${colKey}`);
                      return (
                        <TableCell key={colKey}>
                          {formatCellValue(
                            cell?.value ?? null,
                            layout.valueMeasure,
                          )}
                        </TableCell>
                      );
                    })}
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

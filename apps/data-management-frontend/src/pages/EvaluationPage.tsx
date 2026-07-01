import { useCallback, useEffect, useState } from "react";
import { FlaskConical, RefreshCw } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  type EvalRunDetailApi,
  type EvalRunListItemApi,
  fetchEvalRunDetail,
  fetchEvalRuns,
  triggerEvalRun,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";

const DISPLAY_MIN = 0.7;

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${String(Math.round(value * 100))}%`;
}

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(2);
}

function metricClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return "";
  return value < DISPLAY_MIN ? "text-destructive font-semibold" : "";
}

function statusLabelKey(
  status: EvalRunListItemApi["status"],
): "admin.evaluation.status.pending" | "admin.evaluation.status.running" | "admin.evaluation.status.completed" | "admin.evaluation.status.failed" {
  if (status === "pending") return "admin.evaluation.status.pending";
  if (status === "running") return "admin.evaluation.status.running";
  if (status === "failed") return "admin.evaluation.status.failed";
  return "admin.evaluation.status.completed";
}

export function EvaluationPage() {
  const tr = useAdminT();
  const [runs, setRuns] = useState<EvalRunListItemApi[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvalRunDetailApi | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async (isActive: () => boolean) => {
    setLoading(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const data = await fetchEvalRuns(client);
      if (!isActive()) return;
      setRuns(data.items);
      if (data.items[0]) {
        const detail = await fetchEvalRunDetail(client, data.items[0].run_id);
        if (!isActive()) return;
        setSelectedRun(detail);
      } else {
        setSelectedRun(null);
      }
    } catch (err) {
      if (!isActive()) return;
      setError(
        err instanceof Error ? err.message : tr("admin.evaluation.loadFailed"),
      );
    } finally {
      if (isActive()) setLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    let active = true;
    void loadHistory(() => active);
    return () => {
      active = false;
    };
  }, [loadHistory]);

  const pollRun = useCallback(
    async (runId: string) => {
      const client = requireCorpusConfig();
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const detail = await fetchEvalRunDetail(client, runId);
        setSelectedRun(detail);
        if (detail.status === "completed" || detail.status === "failed") {
          break;
        }
        await new Promise((resolve) => {
          setTimeout(resolve, 250);
        });
      }
      await loadHistory(() => true);
    },
    [loadHistory],
  );

  const handleRun = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      const client = requireCorpusConfig();
      const created = await triggerEvalRun(client, "fixture");
      await pollRun(created.run_id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.evaluation.loadFailed"),
      );
    } finally {
      setRunning(false);
    }
  }, [pollRun, tr]);

  const handleSelectRun = useCallback(async (runId: string) => {
    const client = requireCorpusConfig();
    const detail = await fetchEvalRunDetail(client, runId);
    setSelectedRun(detail);
  }, []);

  const summary = selectedRun?.metrics_summary;

  return (
    <div className="space-y-6" data-testid="evaluation-page">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.evaluation.title")}
          </h2>
          <p className="text-muted-foreground">
            {tr("admin.evaluation.subtitle")}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              void loadHistory(() => true);
            }}
            disabled={loading || running}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {tr("shared.refresh")}
          </Button>
          <Button
            type="button"
            onClick={() => {
              void handleRun();
            }}
            disabled={running}
            data-testid="evaluation-run-button"
          >
            <FlaskConical className="mr-2 h-4 w-4" />
            {running ? tr("admin.evaluation.running") : tr("admin.evaluation.run")}
          </Button>
        </div>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {summary ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {tr("admin.evaluation.metric.retrieval")}
              </CardTitle>
            </CardHeader>
            <CardContent
              className={cn(metricClass(summary.retrieval_relevance ?? null))}
            >
              {formatPercent(summary.retrieval_relevance)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {tr("admin.evaluation.metric.faithfulness")}
              </CardTitle>
            </CardHeader>
            <CardContent className={cn(metricClass(summary.faithfulness ?? null))}>
              {formatScore(summary.faithfulness)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {tr("admin.evaluation.metric.answerRelevancy")}
              </CardTitle>
            </CardHeader>
            <CardContent
              className={cn(metricClass(summary.answer_relevancy ?? null))}
            >
              {formatScore(summary.answer_relevancy)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                {tr("admin.evaluation.metric.latencyP95")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summary.latency_p95_ms ?? "—"} ms
            </CardContent>
          </Card>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.evaluation.history")}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && runs.length === 0 ? (
            <p className="text-muted-foreground">{tr("shared.loading")}</p>
          ) : null}
          {!loading && runs.length === 0 ? (
            <p className="text-muted-foreground">
              {tr("admin.evaluation.noRuns")}
            </p>
          ) : null}
          <ul className="space-y-2" data-testid="evaluation-history">
            {runs.map((run) => (
              <li key={run.run_id}>
                <button
                  type="button"
                  className={cn(
                    "flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm hover:bg-accent",
                    selectedRun?.run_id === run.run_id && "bg-accent",
                  )}
                  onClick={() => {
                    void handleSelectRun(run.run_id);
                  }}
                >
                  <span className="font-mono text-xs">{run.run_id}</span>
                  <Badge variant="outline">{tr(statusLabelKey(run.status))}</Badge>
                </button>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {selectedRun ? (
        <Card>
          <CardHeader>
            <CardTitle>{tr("admin.evaluation.drilldown")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table
                className="w-full text-sm"
                data-testid="evaluation-drilldown"
              >
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4">{tr("admin.evaluation.col.question")}</th>
                    <th className="py-2 pr-4">{tr("admin.evaluation.col.retrieval")}</th>
                    <th className="py-2 pr-4">
                      {tr("admin.evaluation.col.faithfulness")}
                    </th>
                    <th className="py-2">{tr("admin.evaluation.col.answerRelevancy")}</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedRun.items.map((item) => (
                    <tr
                      key={`${item.case_id}-${item.locale}`}
                      className="border-b align-top"
                    >
                      <td className="py-2 pr-4">{item.question}</td>
                      <td className="py-2 pr-4">
                        {item.metrics.retrieval_pass
                          ? tr("admin.evaluation.pass")
                          : tr("admin.evaluation.fail")}
                      </td>
                      <td className="py-2 pr-4">
                        {formatScore(item.metrics.faithfulness ?? null)}
                      </td>
                      <td className="py-2">
                        {formatScore(item.metrics.answer_relevancy ?? null)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

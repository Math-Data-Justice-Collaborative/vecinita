import { useCallback, useEffect, useState } from "react";
import { FlaskConical, RefreshCw } from "lucide-react";
import { useSearchParams } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  type EvalRunDetailApi,
  type EvalRunListItemApi,
  fetchEvalRunDetail,
  fetchEvalRuns,
} from "@/api/admin";
import { requireCorpusConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";
import { EvaluationCompareView } from "@/evaluation/EvaluationCompareView";
import { EvaluationCriteriaTab } from "@/evaluation/EvaluationCriteriaTab";
import { EvaluationDashboardTab } from "@/evaluation/EvaluationDashboardTab";
import { EvaluationDrilldownTable } from "@/evaluation/EvaluationDrilldownTable";
import { EvaluationExploreTab } from "@/evaluation/EvaluationExploreTab";
import { EvaluationPlaygroundTab } from "@/evaluation/EvaluationPlaygroundTab";

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
):
  | "admin.evaluation.status.pending"
  | "admin.evaluation.status.running"
  | "admin.evaluation.status.completed"
  | "admin.evaluation.status.failed" {
  if (status === "pending") return "admin.evaluation.status.pending";
  if (status === "running") return "admin.evaluation.status.running";
  if (status === "failed") return "admin.evaluation.status.failed";
  return "admin.evaluation.status.completed";
}

export function EvaluationPage() {
  const tr = useAdminT();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get("tab") ?? "runs";
  const [runs, setRuns] = useState<EvalRunListItemApi[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvalRunDetailApi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareRunAId, setCompareRunAId] = useState<string>("");
  const [compareRunBId, setCompareRunBId] = useState<string>("");
  const [compareRunA, setCompareRunA] = useState<EvalRunDetailApi | null>(null);
  const [compareRunB, setCompareRunB] = useState<EvalRunDetailApi | null>(null);

  const loadHistory = useCallback(
    async (isActive: () => boolean) => {
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
          err instanceof Error
            ? err.message
            : tr("admin.evaluation.loadFailed"),
        );
      } finally {
        if (isActive()) setLoading(false);
      }
    },
    [tr],
  );

  const handleSelectRun = useCallback(async (runId: string) => {
    const client = requireCorpusConfig();
    const detail = await fetchEvalRunDetail(client, runId);
    setSelectedRun(detail);
  }, []);

  useEffect(() => {
    let active = true;
    void loadHistory(() => active);
    return () => {
      active = false;
    };
  }, [loadHistory]);

  const runFromQuery = searchParams.get("run");

  useEffect(() => {
    if (!runFromQuery || loading) return;
    const exists = runs.some((run) => run.run_id === runFromQuery);
    if (!exists) return;
    if (selectedRun?.run_id === runFromQuery) return;
    void handleSelectRun(runFromQuery);
  }, [runFromQuery, runs, loading, selectedRun?.run_id, handleSelectRun]);

  const pollRun = useCallback(
    async (runId: string) => {
      const client = requireCorpusConfig();
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const detail = await fetchEvalRunDetail(client, runId);
        setSelectedRun(detail);
        setRuns((prev) =>
          prev.map((run) =>
            run.run_id === runId
              ? {
                  ...run,
                  status: detail.status,
                  metrics_summary: detail.metrics_summary,
                  error_message: detail.error_message ?? null,
                }
              : run,
          ),
        );
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

  const handlePlaygroundRunCreated = useCallback(
    (runId: string) => {
      const optimisticRun: EvalRunListItemApi = {
        run_id: runId,
        status: "pending",
        metrics_summary: {},
      };
      setRuns((prev) => [
        optimisticRun,
        ...prev.filter((run) => run.run_id !== runId),
      ]);
      setSelectedRun({
        run_id: runId,
        status: "pending",
        metrics_summary: {},
        items: [],
      });
      void pollRun(runId);
    },
    [pollRun],
  );

  const handleOpenPlayground = useCallback(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("tab", "playground");
      return next;
    });
  }, [setSearchParams]);

  useEffect(() => {
    if (!compareOpen || !compareRunAId || !compareRunBId) {
      setCompareRunA(null);
      setCompareRunB(null);
      return;
    }
    let active = true;
    const client = requireCorpusConfig();
    void Promise.all([
      fetchEvalRunDetail(client, compareRunAId),
      fetchEvalRunDetail(client, compareRunBId),
    ])
      .then(([runA, runB]) => {
        if (!active) return;
        setCompareRunA(runA);
        setCompareRunB(runB);
      })
      .catch(() => {
        if (!active) return;
        setCompareRunA(null);
        setCompareRunB(null);
      });
    return () => {
      active = false;
    };
  }, [compareOpen, compareRunAId, compareRunBId]);

  const summary = selectedRun?.metrics_summary;
  const judgesLikelySkipped =
    selectedRun?.status === "completed" &&
    summary?.faithfulness === null &&
    (summary.retrieval_relevance ?? 0) === 0;

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
            disabled={loading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {tr("shared.refresh")}
          </Button>
          <Button
            type="button"
            onClick={handleOpenPlayground}
            data-testid="evaluation-run-button"
          >
            <FlaskConical className="mr-2 h-4 w-4" />
            {tr("admin.evaluation.run")}
          </Button>
        </div>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {selectedRun?.status === "failed" && selectedRun.error_message ? (
        <p
          role="alert"
          className="text-sm text-destructive"
          data-testid="evaluation-run-error"
        >
          {tr("admin.evaluation.runFailed")}: {selectedRun.error_message}
        </p>
      ) : null}

      <Tabs
        value={activeTab}
        onValueChange={(value) => {
          setSearchParams({ tab: value });
        }}
        data-testid="evaluation-tabs"
      >
        <TabsList>
          <TabsTrigger value="runs" data-testid="eval-tab-runs">
            {tr("admin.evaluation.tab.runs")}
          </TabsTrigger>
          <TabsTrigger value="dashboard" data-testid="eval-tab-dashboard">
            {tr("admin.evaluation.tab.dashboard")}
          </TabsTrigger>
          <TabsTrigger value="explore" data-testid="eval-tab-explore">
            {tr("admin.evaluation.tab.explore")}
          </TabsTrigger>
          <TabsTrigger value="criteria" data-testid="eval-tab-criteria">
            {tr("admin.evaluation.tab.criteria")}
          </TabsTrigger>
          <TabsTrigger value="playground" data-testid="eval-tab-playground">
            {tr("admin.evaluation.tab.playground")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="runs" className="space-y-6" forceMount>
          {summary ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">
                    {tr("admin.evaluation.metric.retrieval")}
                  </CardTitle>
                </CardHeader>
                <CardContent
                  className={cn(
                    metricClass(summary.retrieval_relevance ?? null),
                  )}
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
                <CardContent
                  className={cn(metricClass(summary.faithfulness ?? null))}
                >
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
                <CardContent>{summary.latency_p95_ms ?? "—"} ms</CardContent>
              </Card>
            </div>
          ) : null}

          <Card>
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
              <CardTitle>{tr("admin.evaluation.history")}</CardTitle>
              <Button
                type="button"
                variant="outline"
                size="sm"
                data-testid="eval-compare-toggle"
                onClick={() => {
                  setCompareOpen((open) => !open);
                }}
              >
                {tr("admin.evaluation.compare.toggle")}
              </Button>
            </CardHeader>
            <CardContent>
              {compareOpen ? (
                <div
                  className="mb-4 grid gap-3 sm:grid-cols-2"
                  data-testid="eval-compare-selectors"
                >
                  <div className="space-y-2">
                    <Label htmlFor="eval-compare-run-a-select">
                      {tr("admin.evaluation.compare.runA")}
                    </Label>
                    <select
                      id="eval-compare-run-a-select"
                      data-testid="eval-compare-run-a-select"
                      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                      value={compareRunAId}
                      onChange={(event) => {
                        setCompareRunAId(event.target.value);
                      }}
                    >
                      <option value="">—</option>
                      {runs.map((run) => (
                        <option key={run.run_id} value={run.run_id}>
                          {run.run_id}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="eval-compare-run-b-select">
                      {tr("admin.evaluation.compare.runB")}
                    </Label>
                    <select
                      id="eval-compare-run-b-select"
                      data-testid="eval-compare-run-b-select"
                      className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                      value={compareRunBId}
                      onChange={(event) => {
                        setCompareRunBId(event.target.value);
                      }}
                    >
                      <option value="">—</option>
                      {runs.map((run) => (
                        <option key={run.run_id} value={run.run_id}>
                          {run.run_id}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ) : null}
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
                      <Badge variant="outline">
                        {tr(statusLabelKey(run.status))}
                      </Badge>
                    </button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {compareOpen && compareRunA && compareRunB ? (
            <Card>
              <CardHeader>
                <CardTitle>{tr("admin.evaluation.compare.toggle")}</CardTitle>
              </CardHeader>
              <CardContent>
                <EvaluationCompareView runA={compareRunA} runB={compareRunB} />
              </CardContent>
            </Card>
          ) : null}

          {selectedRun ? (
            <Card>
              <CardHeader>
                <CardTitle>{tr("admin.evaluation.drilldown")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {judgesLikelySkipped ? (
                  <p
                    className="text-sm text-muted-foreground"
                    data-testid="evaluation-judges-skipped-hint"
                  >
                    {tr("admin.evaluation.drilldown.judgesSkipped")}
                  </p>
                ) : null}
                <EvaluationDrilldownTable items={selectedRun.items} />
              </CardContent>
            </Card>
          ) : null}
        </TabsContent>

        <TabsContent value="dashboard">
          <EvaluationDashboardTab />
        </TabsContent>

        <TabsContent value="explore">
          <EvaluationExploreTab />
        </TabsContent>

        <TabsContent value="criteria">
          <EvaluationCriteriaTab />
        </TabsContent>

        <TabsContent value="playground">
          <EvaluationPlaygroundTab onRunCreated={handlePlaygroundRunCreated} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

import { type EvalRunDetailApi } from "@/api/admin";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";

const DISPLAY_MIN = 0.7;

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(2);
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${String(Math.round(value * 100))}%`;
}

function formatDelta(delta: number): string {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(2)}`;
}

function metricRegression(
  runAValue: number | null | undefined,
  runBValue: number | null | undefined,
): boolean {
  if (runAValue === null || runAValue === undefined) return false;
  if (runBValue === null || runBValue === undefined) return false;
  return runBValue < runAValue || runBValue < DISPLAY_MIN;
}

export function EvaluationCompareView({
  runA,
  runB,
}: {
  runA: EvalRunDetailApi;
  runB: EvalRunDetailApi;
}) {
  const tr = useAdminT();

  const faithfulnessA = runA.metrics_summary.faithfulness ?? null;
  const faithfulnessB = runB.metrics_summary.faithfulness ?? null;
  const faithfulnessDelta =
    faithfulnessA !== null && faithfulnessB !== null
      ? faithfulnessB - faithfulnessA
      : null;

  const retrievalA = runA.metrics_summary.retrieval_relevance ?? null;
  const retrievalB = runB.metrics_summary.retrieval_relevance ?? null;

  const compareRows = runB.items.map((itemB) => ({
    caseId: itemB.case_id,
    itemA: runA.items.find((item) => item.case_id === itemB.case_id) ?? null,
    itemB,
  }));

  return (
    <div className="space-y-6" data-testid="evaluation-compare">
      <div className="grid gap-4 md:grid-cols-2">
        <p
          className="font-mono text-xs text-muted-foreground"
          data-testid="eval-compare-run-a-label"
        >
          {runA.run_id}
        </p>
        <p
          className="font-mono text-xs text-muted-foreground"
          data-testid="eval-compare-run-b-label"
        >
          {runB.run_id}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div
          className="rounded-md border p-3 text-sm"
          data-testid="eval-compare-metric-faithfulness"
        >
          <p className="font-medium">
            {tr("admin.evaluation.metric.faithfulness")}
          </p>
          <p>
            {formatScore(faithfulnessA)} → {formatScore(faithfulnessB)}
            {faithfulnessDelta !== null ? (
              <span
                className={cn(
                  "ml-2",
                  faithfulnessDelta < 0 ? "text-destructive font-semibold" : "",
                )}
              >
                {formatDelta(faithfulnessDelta)}
              </span>
            ) : null}
          </p>
        </div>
        <div
          className="rounded-md border p-3 text-sm"
          data-testid="eval-compare-metric-retrieval"
        >
          <p className="font-medium">
            {tr("admin.evaluation.metric.retrieval")}
          </p>
          <p>
            {formatPercent(retrievalA)} → {formatPercent(retrievalB)}
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {compareRows.map(({ caseId, itemA, itemB }) => {
          const faithA = itemA?.metrics.faithfulness ?? null;
          const faithB = itemB.metrics.faithfulness ?? null;
          const showRegression = metricRegression(faithA, faithB);

          return (
            <div
              key={caseId}
              className="rounded-md border p-4"
              data-testid={`eval-compare-row-${caseId}`}
            >
              <p className="font-medium">{itemB.question}</p>
              <div className="mt-2 grid gap-3 md:grid-cols-2 text-sm">
                <div>
                  <p className="text-muted-foreground">
                    {tr("admin.evaluation.playground.recentRun")} A
                  </p>
                  <p>{itemA?.answer ?? "—"}</p>
                  {faithA !== null ? (
                    <p className="font-mono">{formatScore(faithA)}</p>
                  ) : null}
                </div>
                <div>
                  <p className="text-muted-foreground">
                    {tr("admin.evaluation.playground.recentRun")} B
                  </p>
                  <p>{itemB.answer ?? "—"}</p>
                  {faithB !== null ? (
                    <p
                      className={cn(
                        "font-mono",
                        showRegression ? "text-destructive font-semibold" : "",
                      )}
                    >
                      {formatScore(faithB)}
                    </p>
                  ) : null}
                </div>
              </div>
              {showRegression ? (
                <p
                  className="mt-2 text-sm text-destructive font-semibold"
                  data-testid={`eval-compare-regression-${caseId}`}
                >
                  {tr("admin.evaluation.compare.regression")}
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

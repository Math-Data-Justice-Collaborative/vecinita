import { useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { type EvalRunDetailApi } from "@/api/admin";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";

import {
  type EvalDrilldownColumnId,
  DRILLDOWN_COLUMNS,
  loadEvalDrilldownLayout,
  saveEvalDrilldownLayout,
  toggleDrilldownColumn,
} from "./evalDrilldownStorage";

const DISPLAY_MIN = 0.7;

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(2);
}

function metricClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return "";
  return value < DISPLAY_MIN ? "text-destructive font-semibold" : "";
}

function columnLabelKey(
  columnId: EvalDrilldownColumnId,
):
  | "admin.evaluation.col.question"
  | "admin.evaluation.col.answer"
  | "admin.evaluation.col.locale"
  | "admin.evaluation.col.caseId"
  | "admin.evaluation.col.retrieval"
  | "admin.evaluation.col.faithfulness"
  | "admin.evaluation.col.answerRelevancy"
  | "admin.evaluation.col.retrievedUrls"
  | "admin.evaluation.col.expectedDoc"
  | "admin.evaluation.col.latencyMs" {
  if (columnId === "answer") return "admin.evaluation.col.answer";
  if (columnId === "locale") return "admin.evaluation.col.locale";
  if (columnId === "case_id") return "admin.evaluation.col.caseId";
  if (columnId === "retrieval") return "admin.evaluation.col.retrieval";
  if (columnId === "faithfulness") return "admin.evaluation.col.faithfulness";
  if (columnId === "answer_relevancy") {
    return "admin.evaluation.col.answerRelevancy";
  }
  if (columnId === "retrieved_urls")
    return "admin.evaluation.col.retrievedUrls";
  if (columnId === "expected_doc_url")
    return "admin.evaluation.col.expectedDoc";
  if (columnId === "latency_ms") return "admin.evaluation.col.latencyMs";
  return "admin.evaluation.col.question";
}

function renderCell(
  columnId: EvalDrilldownColumnId,
  item: EvalRunDetailApi["items"][number],
  tr: ReturnType<typeof useAdminT>,
): string {
  if (columnId === "question") return item.question;
  if (columnId === "answer") return item.answer ?? "—";
  if (columnId === "locale") return item.locale;
  if (columnId === "case_id") return item.case_id;
  if (columnId === "retrieval") {
    return item.metrics.retrieval_pass
      ? tr("admin.evaluation.pass")
      : tr("admin.evaluation.fail");
  }
  if (columnId === "faithfulness") {
    return formatScore(item.metrics.faithfulness ?? null);
  }
  if (columnId === "answer_relevancy") {
    return formatScore(item.metrics.answer_relevancy ?? null);
  }
  if (columnId === "retrieved_urls") {
    return item.retrieved_urls.length > 0
      ? item.retrieved_urls.join("\n")
      : "—";
  }
  if (columnId === "expected_doc_url") {
    return item.expected_doc_url ?? "—";
  }
  return `${String(item.metrics.latency_ms)} ms`;
}

function cellClassName(
  columnId: EvalDrilldownColumnId,
  item: EvalRunDetailApi["items"][number],
): string {
  if (columnId === "faithfulness") {
    return metricClass(item.metrics.faithfulness ?? null);
  }
  if (columnId === "answer_relevancy") {
    return metricClass(item.metrics.answer_relevancy ?? null);
  }
  if (columnId === "retrieval" && !item.metrics.retrieval_pass) {
    return "text-destructive font-semibold";
  }
  return "";
}

interface EvaluationDrilldownTableProps {
  items: EvalRunDetailApi["items"];
}

export function EvaluationDrilldownTable({
  items,
}: EvaluationDrilldownTableProps) {
  const tr = useAdminT();
  const [layout, setLayout] = useState(() => loadEvalDrilldownLayout());
  const [showColumnPicker, setShowColumnPicker] = useState(false);

  const persistLayout = useCallback((next: typeof layout) => {
    setLayout(next);
    saveEvalDrilldownLayout(next);
  }, []);

  const visibleColumns = DRILLDOWN_COLUMNS.filter((col) =>
    layout.visibleColumns.includes(col),
  );

  return (
    <div className="space-y-3" data-testid="evaluation-drilldown">
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            setShowColumnPicker((open) => !open);
          }}
          data-testid="eval-drilldown-columns-toggle"
        >
          {tr("admin.evaluation.drilldown.columns")}
        </Button>
        <label className="flex items-center gap-2 text-sm">
          <Checkbox
            checked={layout.wrapCells}
            onCheckedChange={(checked) => {
              persistLayout({
                ...layout,
                wrapCells: checked === true,
              });
            }}
            data-testid="eval-drilldown-wrap-toggle"
          />
          {tr("admin.evaluation.drilldown.wrap")}
        </label>
      </div>

      {showColumnPicker ? (
        <div
          className="flex flex-wrap gap-3 rounded-md border p-3"
          data-testid="eval-drilldown-column-picker"
        >
          {DRILLDOWN_COLUMNS.map((columnId) => (
            <label key={columnId} className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={layout.visibleColumns.includes(columnId)}
                onCheckedChange={() => {
                  persistLayout(toggleDrilldownColumn(layout, columnId));
                }}
                data-testid={`eval-drilldown-col-${columnId}`}
              />
              {tr(columnLabelKey(columnId))}
            </label>
          ))}
        </div>
      ) : null}

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              {visibleColumns.map((columnId) => (
                <TableHead key={columnId} className="whitespace-nowrap">
                  {tr(columnLabelKey(columnId))}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={`${item.case_id}-${item.locale}`}>
                {visibleColumns.map((columnId) => (
                  <TableCell
                    key={columnId}
                    className={cn(
                      "align-top",
                      layout.wrapCells
                        ? "whitespace-pre-wrap break-words max-w-md"
                        : "whitespace-nowrap",
                      cellClassName(columnId, item),
                    )}
                    data-testid={
                      columnId === "answer"
                        ? `eval-answer-${item.case_id}-${item.locale}`
                        : undefined
                    }
                  >
                    {renderCell(columnId, item, tr)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

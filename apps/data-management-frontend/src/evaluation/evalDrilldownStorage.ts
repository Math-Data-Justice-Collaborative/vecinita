const STORAGE_KEY = "vecinita.eval.drilldown.v1";

export type EvalDrilldownColumnId =
  | "question"
  | "answer"
  | "locale"
  | "case_id"
  | "retrieval"
  | "faithfulness"
  | "answer_relevancy"
  | "retrieved_urls"
  | "expected_doc_url"
  | "latency_ms";

export interface EvalDrilldownLayout {
  visibleColumns: EvalDrilldownColumnId[];
  wrapCells: boolean;
}

export const DRILLDOWN_COLUMNS: EvalDrilldownColumnId[] = [
  "question",
  "answer",
  "locale",
  "case_id",
  "retrieval",
  "faithfulness",
  "answer_relevancy",
  "retrieved_urls",
  "expected_doc_url",
  "latency_ms",
];

const DEFAULT_VISIBLE: EvalDrilldownColumnId[] = [
  "question",
  "answer",
  "retrieval",
  "faithfulness",
  "answer_relevancy",
];

const DEFAULT_LAYOUT: EvalDrilldownLayout = {
  visibleColumns: DEFAULT_VISIBLE,
  wrapCells: true,
};

function isColumnId(value: string): value is EvalDrilldownColumnId {
  return (DRILLDOWN_COLUMNS as string[]).includes(value);
}

export function loadEvalDrilldownLayout(): EvalDrilldownLayout {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_LAYOUT;
    const parsed = JSON.parse(raw) as Partial<EvalDrilldownLayout>;
    const visible =
      parsed.visibleColumns?.filter((col): col is EvalDrilldownColumnId =>
        isColumnId(col),
      ) ?? DEFAULT_VISIBLE;
    return {
      visibleColumns: visible.length > 0 ? visible : DEFAULT_VISIBLE,
      wrapCells: parsed.wrapCells ?? true,
    };
  } catch {
    return DEFAULT_LAYOUT;
  }
}

export function saveEvalDrilldownLayout(layout: EvalDrilldownLayout): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
  } catch {
    // degrade silently per ADR-004 localStorage policy
  }
}

export function toggleDrilldownColumn(
  layout: EvalDrilldownLayout,
  columnId: EvalDrilldownColumnId,
): EvalDrilldownLayout {
  const visible = layout.visibleColumns.includes(columnId)
    ? layout.visibleColumns.filter((col) => col !== columnId)
    : [...layout.visibleColumns, columnId];
  return {
    ...layout,
    visibleColumns: visible.length > 0 ? visible : [columnId],
  };
}

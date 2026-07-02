import { describe, expect, it } from "vitest";

import type { EvalRunDetailApi } from "@/api/admin";

import {
  buildPivotTable,
  flattenRunsForExplore,
  metricLabel,
} from "./evalPivot";

function makeDetail(
  overrides: Partial<EvalRunDetailApi> & { run_id: string },
): EvalRunDetailApi {
  return {
    status: "completed",
    metrics_summary: {},
    items: [
      {
        case_id: "case-a",
        locale: "en",
        question: "Q?",
        retrieved_urls: [],
        metrics: {
          retrieval_pass: true,
          faithfulness: 0.8,
          answer_relevancy: 0.7,
          latency_ms: 1200,
        },
      },
    ],
    ...overrides,
  };
}

describe("flattenRunsForExplore", () => {
  it("expands builtin metrics and custom scores per item", () => {
    const rows = flattenRunsForExplore([
      makeDetail({
        run_id: "20260701-0000-0000-0000-000000000099",
        items: [
          {
            case_id: "case-a",
            locale: "es",
            question: "Q?",
            retrieved_urls: [],
            metrics: {
              retrieval_pass: false,
              faithfulness: null,
              answer_relevancy: 0.5,
              latency_ms: 35_000,
              custom_scores: { "tone-friendly": 0.9 },
            },
          },
        ],
      }),
    ]);

    expect(rows).toHaveLength(5);
    expect(rows.find((r) => r.metric === "retrieval")?.pass_fail).toBe("fail");
    expect(rows.find((r) => r.metric === "faithfulness")?.pass_fail).toBe(
      "fail",
    );
    expect(rows.find((r) => r.metric === "answer_relevancy")?.pass_fail).toBe(
      "fail",
    );
    expect(rows.find((r) => r.metric === "latency_ms")?.pass_fail).toBe("fail");
    expect(rows.find((r) => r.metric === "tone-friendly")).toEqual(
      expect.objectContaining({ pass_fail: "pass", score: 0.9 }),
    );
  });

  it("caps flattened rows at 500", () => {
    const items = Array.from({ length: 130 }, (_, index) => ({
      case_id: `case-${String(index)}`,
      locale: "en",
      question: "Q?",
      retrieved_urls: [],
      metrics: {
        retrieval_pass: true,
        faithfulness: 0.8,
        answer_relevancy: 0.8,
        latency_ms: 1000,
      },
    }));
    const rows = flattenRunsForExplore([
      makeDetail({ run_id: "20260701-0000-0000-0000-000000000099", items }),
    ]);
    expect(rows).toHaveLength(500);
  });
});

describe("buildPivotTable", () => {
  const rows = flattenRunsForExplore([
    makeDetail({ run_id: "20260701-0000-0000-0000-000000000099" }),
    makeDetail({
      run_id: "20260702-0000-0000-0000-000000000088",
      items: [
        {
          case_id: "case-b",
          locale: "es",
          question: "Q2?",
          retrieved_urls: [],
          metrics: {
            retrieval_pass: false,
            faithfulness: 0.4,
            answer_relevancy: 0.9,
            latency_ms: 500,
          },
        },
      ],
    }),
  ]);

  it("aggregates avg_score by locale and metric", () => {
    const pivot = buildPivotTable(rows, {
      rowAxis: "locale",
      columnAxis: "metric",
      valueMeasure: "avg_score",
    });
    expect(pivot.rowKeys).toContain("en");
    expect(pivot.colKeys).toContain("faithfulness");
    const cell = pivot.cells.get("en::faithfulness");
    expect(cell?.count).toBeGreaterThan(0);
    expect(cell?.value).not.toBeNull();
  });

  it("aggregates count and pass_rate measures", () => {
    const countPivot = buildPivotTable(rows, {
      rowAxis: "locale",
      columnAxis: "pass_fail",
      valueMeasure: "count",
    });
    const countCell = countPivot.cells.get("en::pass");
    expect(countCell?.value).toBeGreaterThan(0);

    const ratePivot = buildPivotTable(rows, {
      rowAxis: "case_id",
      columnAxis: "metric",
      valueMeasure: "pass_rate",
    });
    const rateCell = ratePivot.cells.get("case-a::retrieval");
    expect(rateCell?.value).toBe(1);
  });

  it("returns null cells when no scores match axis pair", () => {
    const pivot = buildPivotTable(
      [
        {
          run_id: "r1",
          run_date: "20260701",
          case_id: "only",
          locale: "en",
          metric: "faithfulness",
          pass_fail: "pass",
          score: null,
        },
      ],
      {
        rowAxis: "run_date",
        columnAxis: "locale",
        valueMeasure: "avg_score",
      },
    );
    expect(pivot.cells.get("20260701::en")).toEqual({ value: null, count: 0 });
  });

  it("supports pass_fail and run_date row axes", () => {
    const pivot = buildPivotTable(rows, {
      rowAxis: "pass_fail",
      columnAxis: "run_date",
      valueMeasure: "avg_score",
    });
    expect(pivot.rowKeys.length).toBeGreaterThan(0);
    expect(pivot.colKeys.every((key) => key.startsWith("202607"))).toBe(true);
  });

  it("aggregates faithfulness pass at threshold boundary", () => {
    const rows = flattenRunsForExplore([
      makeDetail({
        run_id: "20260701-0000-0000-0000-000000000099",
        items: [
          {
            case_id: "boundary",
            locale: "en",
            question: "Q?",
            retrieved_urls: [],
            metrics: {
              retrieval_pass: true,
              faithfulness: 0.6,
              answer_relevancy: 0.6,
              latency_ms: 30_000,
            },
          },
        ],
      }),
    ]);
    expect(rows.find((r) => r.metric === "faithfulness")?.pass_fail).toBe(
      "pass",
    );
    expect(rows.find((r) => r.metric === "latency_ms")?.pass_fail).toBe("pass");
  });

  it("uses null answer relevancy scores and failing custom rubric scores", () => {
    const rows = flattenRunsForExplore([
      makeDetail({
        run_id: "20260701-0000-0000-0000-000000000099",
        items: [
          {
            case_id: "sparse",
            locale: "en",
            question: "Q?",
            retrieved_urls: [],
            metrics: {
              retrieval_pass: true,
              faithfulness: 0.8,
              latency_ms: 1000,
              custom_scores: { "tone-harsh": 0.4 },
            },
          },
        ],
      }),
    ]);
    expect(rows.find((r) => r.metric === "answer_relevancy")?.score).toBeNull();
    expect(rows.find((r) => r.metric === "tone-harsh")?.pass_fail).toBe("fail");
  });
});

describe("metricLabel", () => {
  it("maps builtin metric ids and passes through custom slugs", () => {
    expect(metricLabel("retrieval")).toBe("Retrieval");
    expect(metricLabel("faithfulness")).toBe("Faithfulness");
    expect(metricLabel("answer_relevancy")).toBe("Answer relevancy");
    expect(metricLabel("latency_ms")).toBe("Latency (ms)");
    expect(metricLabel("custom-slug")).toBe("custom-slug");
  });
});

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { EvalMetricChart } from "./EvalMetricChart";

vi.mock("recharts", async () => {
  const React = await import("react");

  function invokeTooltip(
    props: {
      formatter?: (value: number) => string;
      labelFormatter?: (
        label: string,
        payload: { payload?: { run_id?: string } }[],
      ) => string;
    },
    metricId: string,
    metricLabel: string,
  ): void {
    if (props.formatter) {
      if (metricId === "retrieval_relevance") {
        expect(props.formatter(0.812)).toBe("81%");
      } else if (metricId === "latency_p95_ms") {
        expect(props.formatter(4200)).toBe("4200 ms");
      } else {
        expect(props.formatter(0.812)).toBe("0.81");
      }
    }
    if (props.labelFormatter) {
      expect(
        props.labelFormatter("", [{ payload: { run_id: "run-1" } }]),
      ).toBe("run-1");
      expect(props.labelFormatter("", [])).toBe(metricLabel);
    }
  }

  const Chart = ({
    children,
    testId,
  }: {
    children: React.ReactNode;
    testId: string;
  }) => React.createElement("div", { "data-testid": testId }, children);

  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
      React.createElement("div", null, children),
    LineChart: ({ children }: { children: React.ReactNode }) =>
      Chart({ children, testId: "line-chart" }),
    AreaChart: ({ children }: { children: React.ReactNode }) =>
      Chart({ children, testId: "area-chart" }),
    Line: () => null,
    Area: () => null,
    CartesianGrid: () => null,
    XAxis: () => null,
    YAxis: () => null,
    ReferenceLine: () =>
      React.createElement("div", { "data-testid": "reference-line" }),
    Tooltip: (props: {
      formatter?: (value: number) => string;
      labelFormatter?: (
        label: string,
        payload: { payload?: { run_id?: string } }[],
      ) => string;
    }) => {
      invokeTooltip(
        props,
        tooltipMetricId,
        tooltipMetricLabel,
      );
      return null;
    },
  };
});

let tooltipMetricId = "faithfulness";
let tooltipMetricLabel = "Faithfulness";

const POINTS = [
  {
    run_id: "run-1",
    completed_at: "2026-07-01T12:00:00Z",
    metrics_summary: {
      retrieval_relevance: 0.9,
      faithfulness: 0.8,
      answer_relevancy: 0.7,
      latency_p95_ms: 4200,
      custom_scores: { "tone-friendly": 0.85 },
    },
  },
];

describe("EvalMetricChart", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders line chart with threshold for score metrics", () => {
    tooltipMetricId = "faithfulness";
    tooltipMetricLabel = "Faithfulness";
    render(
      <EvalMetricChart
        points={POINTS}
        metricId="faithfulness"
        metricLabel="Faithfulness"
        chartType="line"
        showThreshold
      />,
    );
    expect(screen.getByTestId("eval-chart-faithfulness")).toBeInTheDocument();
    expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    expect(screen.getByTestId("reference-line")).toBeInTheDocument();
  });

  it("renders area chart without threshold for latency", () => {
    tooltipMetricId = "latency_p95_ms";
    tooltipMetricLabel = "Latency";
    render(
      <EvalMetricChart
        points={POINTS}
        metricId="latency_p95_ms"
        metricLabel="Latency"
        chartType="area"
        showThreshold={false}
      />,
    );
    expect(screen.getByTestId("area-chart")).toBeInTheDocument();
    expect(screen.queryByTestId("reference-line")).not.toBeInTheDocument();
  });

  it("handles null metric values in points", () => {
    tooltipMetricId = "faithfulness";
    tooltipMetricLabel = "Faithfulness";
    render(
      <EvalMetricChart
        points={[
          {
            run_id: "run-null",
            completed_at: "2026-07-01T12:00:00Z",
            metrics_summary: {},
          },
        ]}
        metricId="faithfulness"
        metricLabel="Faithfulness"
        chartType="line"
        showThreshold={false}
      />,
    );
    expect(screen.getByTestId("eval-chart-faithfulness")).toBeInTheDocument();
  });

  it("renders answer relevancy line chart values", () => {
    tooltipMetricId = "answer_relevancy";
    tooltipMetricLabel = "Answer relevancy";
    render(
      <EvalMetricChart
        points={POINTS}
        metricId="answer_relevancy"
        metricLabel="Answer relevancy"
        chartType="line"
        showThreshold
      />,
    );
    expect(screen.getByTestId("eval-chart-answer_relevancy")).toBeInTheDocument();
  });

  it("reads retrieval and custom score values from points", () => {
    tooltipMetricId = "retrieval_relevance";
    tooltipMetricLabel = "Retrieval";
    render(
      <EvalMetricChart
        points={POINTS}
        metricId="retrieval_relevance"
        metricLabel="Retrieval"
        chartType="line"
        showThreshold
      />,
    );
    expect(screen.getByTestId("eval-chart-retrieval_relevance")).toBeInTheDocument();

    cleanup();
    tooltipMetricId = "tone-friendly";
    tooltipMetricLabel = "Tone";
    render(
      <EvalMetricChart
        points={POINTS}
        metricId="tone-friendly"
        metricLabel="Tone"
        chartType="line"
        showThreshold={false}
      />,
    );
    expect(screen.getByTestId("eval-chart-tone-friendly")).toBeInTheDocument();
  });

  it("uses null fallbacks for missing summary fields and latency line domain", () => {
    const sparsePoint = [
      {
        run_id: "run-sparse",
        completed_at: "2026-07-01T12:00:00Z",
        metrics_summary: {},
      },
    ];

    tooltipMetricId = "retrieval_relevance";
    tooltipMetricLabel = "Retrieval";
    render(
      <EvalMetricChart
        points={sparsePoint}
        metricId="retrieval_relevance"
        metricLabel="Retrieval"
        chartType="line"
        showThreshold={false}
      />,
    );
    cleanup();

    tooltipMetricId = "answer_relevancy";
    tooltipMetricLabel = "Answer relevancy";
    render(
      <EvalMetricChart
        points={sparsePoint}
        metricId="answer_relevancy"
        metricLabel="Answer relevancy"
        chartType="line"
        showThreshold={false}
      />,
    );
    cleanup();

    tooltipMetricId = "latency_p95_ms";
    tooltipMetricLabel = "Latency";
    render(
      <EvalMetricChart
        points={sparsePoint}
        metricId="latency_p95_ms"
        metricLabel="Latency"
        chartType="line"
        showThreshold={false}
      />,
    );
    cleanup();

    tooltipMetricId = "missing-custom";
    tooltipMetricLabel = "Custom";
    render(
      <EvalMetricChart
        points={sparsePoint}
        metricId="missing-custom"
        metricLabel="Custom"
        chartType="line"
        showThreshold={false}
      />,
    );
    expect(screen.getByTestId("eval-chart-missing-custom")).toBeInTheDocument();
  });
});

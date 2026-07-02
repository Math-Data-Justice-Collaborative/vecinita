import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { EvalTimeseriesPointApi } from "@/api/admin";
import type { EvalChartType } from "./evalDashboardStorage";

const THRESHOLD = 0.7;

function metricValue(
  point: EvalTimeseriesPointApi,
  metricId: string,
): number | null {
  const summary = point.metrics_summary;
  if (metricId === "retrieval_relevance") {
    return summary.retrieval_relevance ?? null;
  }
  if (metricId === "faithfulness") {
    return summary.faithfulness ?? null;
  }
  if (metricId === "answer_relevancy") {
    return summary.answer_relevancy ?? null;
  }
  if (metricId === "latency_p95_ms") {
    return summary.latency_p95_ms ?? null;
  }
  return summary.custom_scores?.[metricId] ?? null;
}

export interface EvalMetricChartProps {
  points: EvalTimeseriesPointApi[];
  metricId: string;
  metricLabel: string;
  chartType: EvalChartType;
  showThreshold: boolean;
}

function ChartTooltipValue({
  value,
  metricId,
}: {
  value: number;
  metricId: string;
}): string {
  if (metricId === "retrieval_relevance") {
    return `${String(Math.round(value * 100))}%`;
  }
  if (metricId === "latency_p95_ms") {
    return `${String(value)} ms`;
  }
  return value.toFixed(2);
}

export function EvalMetricChart({
  points,
  metricId,
  metricLabel,
  chartType,
  showThreshold,
}: EvalMetricChartProps) {
  const data = points.map((point) => ({
    label: new Date(point.completed_at).toLocaleDateString(),
    value: metricValue(point, metricId),
    run_id: point.run_id,
  }));

  const thresholdLine =
    showThreshold && metricId !== "latency_p95_ms" ? (
      <ReferenceLine
        y={THRESHOLD}
        stroke="hsl(var(--destructive))"
        strokeDasharray="4 4"
        label={{ value: "0.70", position: "insideTopRight", fontSize: 10 }}
      />
    ) : null;

  if (chartType === "area") {
    return (
      <div className="h-64 w-full" data-testid={`eval-chart-${metricId}`}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
            <Tooltip
              formatter={(value: number) =>
                ChartTooltipValue({ value, metricId })
              }
              labelFormatter={(_, payload) => {
                const entry = payload[0]?.payload as
                  | { run_id?: string }
                  | undefined;
                return entry?.run_id ?? metricLabel;
              }}
            />
            {thresholdLine}
            <Area
              type="monotone"
              dataKey="value"
              name={metricLabel}
              stroke="hsl(var(--primary))"
              fill="hsl(var(--primary))"
              fillOpacity={0.15}
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="h-64 w-full" data-testid={`eval-chart-${metricId}`}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
          <YAxis
            tick={{ fontSize: 11 }}
            domain={metricId === "latency_p95_ms" ? ["auto", "auto"] : [0, 1]}
          />
          <Tooltip
            formatter={(value: number) =>
              ChartTooltipValue({ value, metricId })
            }
            labelFormatter={(_, payload) => {
              const entry = payload[0]?.payload as
                | { run_id?: string }
                | undefined;
              return entry?.run_id ?? metricLabel;
            }}
          />
          {thresholdLine}
          <Line
            type="monotone"
            dataKey="value"
            name={metricLabel}
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            dot={{ r: 3 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

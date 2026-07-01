import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderAppRoutesReady } from "./renderAppHelpers";
import { fetchInputUrl } from "./fetch-mock";

vi.mock("recharts", async () => {
  const React = await import("react");
  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
      React.createElement("div", { "data-testid": "mock-recharts" }, children),
    LineChart: ({ children }: { children: React.ReactNode }) =>
      React.createElement("div", { "data-testid": "mock-line-chart" }, children),
    AreaChart: ({ children }: { children: React.ReactNode }) =>
      React.createElement("div", { "data-testid": "mock-area-chart" }, children),
    Line: () => null,
    Area: () => null,
    CartesianGrid: () => null,
    XAxis: () => null,
    YAxis: () => null,
    Tooltip: () => null,
    ReferenceLine: () => null,
  };
});

const TIMESERIES_BODY = {
  points: [
    {
      run_id: "00000000-0000-0000-0000-000000000099",
      completed_at: "2026-07-01T12:01:00Z",
      metrics_summary: {
        retrieval_relevance: 0.91,
        faithfulness: 0.72,
        answer_relevancy: 0.68,
        latency_p95_ms: 4200,
      },
    },
    {
      run_id: "00000000-0000-0000-0000-000000000088",
      completed_at: "2026-07-02T12:01:00Z",
      metrics_summary: {
        retrieval_relevance: 0.85,
        faithfulness: 0.7,
        answer_relevancy: 0.65,
        latency_p95_ms: 3900,
      },
    },
  ],
  available_metrics: [
    "retrieval_relevance",
    "faithfulness",
    "answer_relevancy",
    "latency_p95_ms",
  ],
};

const CRITERIA_BODY = {
  items: [
    {
      criterion_id: "00000000-0000-0000-0000-000000000077",
      slug: "tone-friendly",
      label: "Friendly tone",
      rubric: "Supportive tone",
      scorer_type: "llm_rubric",
      enabled: true,
      created_at: "2026-07-01T12:00:00Z",
      updated_at: "2026-07-01T12:00:00Z",
    },
  ],
};

function dashboardEvalFetch(
  url: string,
  init?: RequestInit,
): Response | { ok: boolean; json: () => Promise<unknown> } {
  const method = (init?.method ?? "GET").toUpperCase();
  if (url.includes("/internal/v1/eval/runs/timeseries")) {
    return { ok: true, json: async () => TIMESERIES_BODY };
  }
  if (url.includes("/internal/v1/eval/criteria") && method === "GET") {
    return { ok: true, json: async () => CRITERIA_BODY };
  }
  if (url.includes("/internal/v1/eval/criteria") && method === "POST") {
    return {
      ok: true,
      json: async () => ({
        criterion_id: "00000000-0000-0000-0000-000000000066",
        slug: "new-criterion",
        label: "New",
        rubric: "Rubric",
        scorer_type: "llm_rubric",
        enabled: true,
        created_at: "2026-07-01T12:00:00Z",
        updated_at: "2026-07-01T12:00:00Z",
      }),
    };
  }
  if (url.includes("/internal/v1/eval/runs/")) {
    return {
      ok: true,
      json: async () => ({
        run_id: "00000000-0000-0000-0000-000000000099",
        status: "completed",
        metrics_summary: TIMESERIES_BODY.points[0].metrics_summary,
        items: [
          {
            case_id: "community-food-pantry",
            locale: "en",
            question: "When are food pantry hours updated?",
            metrics: {
              retrieval_pass: true,
              faithfulness: 0.85,
              answer_relevancy: 0.8,
              latency_ms: 3100,
            },
          },
        ],
      }),
    };
  }
  if (url.includes("/internal/v1/eval/runs")) {
    return {
      ok: true,
      json: async () => ({
        items: [
          {
            run_id: "00000000-0000-0000-0000-000000000099",
            status: "completed",
            metrics_summary: TIMESERIES_BODY.points[0].metrics_summary,
          },
        ],
        page: 1,
        page_size: 20,
        total_count: 1,
      }),
    };
  }
  if (url.includes("/internal/v1/stats")) {
    return {
      ok: true,
      json: async () => ({
        total_documents: 0,
        total_chunks: 0,
        tag_distribution: [],
        language_breakdown: {},
        recent_activity: [],
        top_served: [],
      }),
    };
  }
  if (url.includes("/internal/v1/documents")) {
    return { ok: true, json: async () => [] };
  }
  return { ok: true, json: async () => ({}) };
}

describe("Evaluation dashboard tabs", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
        const url = fetchInputUrl(input);
        return Promise.resolve(dashboardEvalFetch(url, init));
      }),
    );
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("renders time-series dashboard charts (TC-117, UJ-041)", async () => {
    await renderAppRoutesReady("/evaluation?tab=dashboard");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-dashboard-tab")).toBeInTheDocument();
    });
    expect(screen.getByTestId("eval-chart-retrieval_relevance")).toBeInTheDocument();
  });

  it("persists collapsible panel layout (TC-119)", async () => {
    await renderAppRoutesReady("/evaluation?tab=dashboard");
    await waitFor(() => {
      expect(screen.getByTestId("eval-panel-toggle-faithfulness")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-panel-toggle-faithfulness"));
    const stored = localStorage.getItem("vecinita.eval.dashboard.v1");
    expect(stored).toContain("faithfulness");
  });

  it("renders pivot explore table with axis selectors (TC-118, UJ-042)", async () => {
    await renderAppRoutesReady("/evaluation?tab=explore");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-explore-tab")).toBeInTheDocument();
    });
    expect(screen.getByTestId("eval-pivot-table")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("eval-pivot-row-axis"), {
      target: { value: "case_id" },
    });
    const stored = localStorage.getItem("vecinita.eval.explore.v1");
    expect(stored).toContain("case_id");
  });

  it("shows criteria manager UI (TC-121, UJ-043)", async () => {
    await renderAppRoutesReady("/evaluation?tab=criteria");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-criteria-tab")).toBeInTheDocument();
    });
    expect(screen.getByTestId("eval-criterion-tone-friendly")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("eval-criterion-slug"), {
      target: { value: "new-criterion" },
    });
    fireEvent.change(screen.getByTestId("eval-criterion-label"), {
      target: { value: "New criterion" },
    });
    fireEvent.change(screen.getByTestId("eval-criterion-rubric"), {
      target: { value: "Must cite sources" },
    });
    fireEvent.click(screen.getByTestId("eval-criterion-create"));
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalled();
    });
  });
});

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import {
  createEvalCriterion,
  fetchEvalCriteria,
  fetchEvalRunDetail,
  fetchEvalRuns,
  fetchEvalTimeseries,
  updateEvalCriterion,
} from "@/api/admin";
import { EvaluationCriteriaTab } from "@/evaluation/EvaluationCriteriaTab";
import { EvaluationDashboardTab } from "@/evaluation/EvaluationDashboardTab";
import { EvaluationExploreTab } from "@/evaluation/EvaluationExploreTab";

vi.mock("@/api/admin");
vi.mock("@/config", () => ({
  requireCorpusConfig: () => ({
    baseUrl: "http://localhost:8002",
    apiKey: "test-corpus-key",
  }),
}));

vi.mock("recharts", async () => {
  const React = await import("react");
  return {
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) =>
      React.createElement("div", null, children),
    LineChart: ({ children }: { children: React.ReactNode }) =>
      React.createElement(
        "div",
        { "data-testid": "mock-line-chart" },
        children,
      ),
    AreaChart: ({ children }: { children: React.ReactNode }) =>
      React.createElement(
        "div",
        { "data-testid": "mock-area-chart" },
        children,
      ),
    ScatterChart: ({ children }: { children: React.ReactNode }) =>
      React.createElement(
        "div",
        { "data-testid": "mock-scatter-chart" },
        children,
      ),
    Line: () => null,
    Area: () => null,
    Scatter: () => null,
    CartesianGrid: () => null,
    XAxis: () => null,
    YAxis: () => null,
    Tooltip: () => null,
    ReferenceLine: () => null,
  };
});

function renderTab(ui: ReactElement) {
  return render(
    <LocaleProvider>
      <MemoryRouter>{ui}</MemoryRouter>
    </LocaleProvider>,
  );
}

const CRITERION = {
  criterion_id: "00000000-0000-0000-0000-000000000077",
  slug: "tone-friendly",
  label: "Friendly tone",
  rubric: "Supportive tone",
  scorer_type: "llm_rubric" as const,
  enabled: false,
  created_at: "2026-07-01T12:00:00Z",
  updated_at: "2026-07-01T12:00:00Z",
};

describe("evaluation tab branch coverage", () => {
  beforeEach(() => {
    vi.mocked(fetchEvalTimeseries).mockResolvedValue({
      points: [],
      available_metrics: ["custom-metric"],
    });
    vi.mocked(fetchEvalRuns).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total_count: 0,
    });
    vi.mocked(fetchEvalRunDetail).mockResolvedValue({
      run_id: "20260701-0000-0000-0000-000000000099",
      status: "completed",
      metrics_summary: {},
      items: [],
    });
    vi.mocked(fetchEvalCriteria).mockResolvedValue({ items: [CRITERION] });
    vi.mocked(createEvalCriterion).mockResolvedValue({
      ...CRITERION,
      enabled: true,
    });
    vi.mocked(updateEvalCriterion).mockResolvedValue({
      ...CRITERION,
      enabled: true,
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("EvaluationDashboardTab shows loading, empty data, and custom metric labels", async () => {
    let resolveTimeseries: (
      value: Awaited<ReturnType<typeof fetchEvalTimeseries>>,
    ) => void = () => undefined;
    vi.mocked(fetchEvalTimeseries).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTimeseries = resolve;
        }),
    );

    renderTab(<EvaluationDashboardTab />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    resolveTimeseries({
      points: [],
      available_metrics: ["custom-metric"],
    });
    await waitFor(() => {
      expect(
        screen.getByText(/No completed runs yet for charts/i),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("button", { name: "custom-metric" }),
    ).toBeInTheDocument();
  });

  it("EvaluationDashboardTab surfaces non-Error fetch failures", async () => {
    vi.mocked(fetchEvalTimeseries).mockRejectedValue("boom");
    renderTab(<EvaluationDashboardTab />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("EvaluationExploreTab shows loading, empty pivot, and value format branches", async () => {
    vi.mocked(fetchEvalRuns).mockResolvedValue({
      items: [
        {
          run_id: "20260701-0000-0000-0000-000000000099",
          status: "completed",
          metrics_summary: {},
        },
      ],
      page: 1,
      page_size: 20,
      total_count: 1,
    });
    vi.mocked(fetchEvalRunDetail).mockResolvedValue({
      run_id: "20260701-0000-0000-0000-000000000099",
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
            latency_ms: 4200,
          },
        },
      ],
    });

    renderTab(<EvaluationExploreTab />);
    await waitFor(() => {
      expect(screen.getByTestId("eval-pivot-table")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId("eval-pivot-value-axis"), {
      target: { value: "count" },
    });
    expect(screen.getByTestId("eval-pivot-table")).toHaveTextContent("1");

    fireEvent.change(screen.getByTestId("eval-pivot-value-axis"), {
      target: { value: "pass_rate" },
    });
    expect(screen.getByTestId("eval-pivot-table")).toHaveTextContent("%");

    vi.mocked(fetchEvalRuns).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total_count: 0,
    });
    cleanup();
    renderTab(<EvaluationExploreTab />);
    await waitFor(() => {
      expect(
        screen.getByText(/No completed runs to explore/i),
      ).toBeInTheDocument();
    });
  });

  it("EvaluationExploreTab surfaces non-Error fetch failures", async () => {
    vi.mocked(fetchEvalRuns).mockRejectedValue("explore-fail");
    renderTab(<EvaluationExploreTab />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("EvaluationExploreTab shows loading state before pivot data renders", async () => {
    let resolveRuns: (
      value: Awaited<ReturnType<typeof fetchEvalRuns>>,
    ) => void = () => undefined;
    vi.mocked(fetchEvalRuns).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRuns = resolve;
        }),
    );

    renderTab(<EvaluationExploreTab />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    resolveRuns({
      items: [
        {
          run_id: "20260701-0000-0000-0000-000000000099",
          status: "completed",
          metrics_summary: {},
        },
      ],
      page: 1,
      page_size: 20,
      total_count: 1,
    });
    vi.mocked(fetchEvalRunDetail).mockResolvedValue({
      run_id: "20260701-0000-0000-0000-000000000099",
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
            latency_ms: 4200,
          },
        },
      ],
    });

    await waitFor(() => {
      expect(screen.getByTestId("eval-pivot-table")).toBeInTheDocument();
    });
  });

  it("EvaluationCriteriaTab shows loading state", async () => {
    let resolveCriteria: (
      value: Awaited<ReturnType<typeof fetchEvalCriteria>>,
    ) => void = () => undefined;
    vi.mocked(fetchEvalCriteria).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveCriteria = resolve;
        }),
    );
    renderTab(<EvaluationCriteriaTab />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    resolveCriteria({ items: [] });
    await waitFor(() => {
      expect(screen.getByText(/No custom criteria yet/i)).toBeInTheDocument();
    });
  });

  it("EvaluationCriteriaTab handles create validation and create errors", async () => {
    renderTab(<EvaluationCriteriaTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-criterion-tone-friendly"),
      ).toBeInTheDocument();
    });

    expect(screen.getByTestId("eval-criterion-create")).toBeDisabled();

    vi.mocked(createEvalCriterion).mockRejectedValue(
      new Error("create failed"),
    );
    fireEvent.change(screen.getByTestId("eval-criterion-slug"), {
      target: { value: "new-one" },
    });
    fireEvent.change(screen.getByTestId("eval-criterion-label"), {
      target: { value: "New one" },
    });
    fireEvent.change(screen.getByTestId("eval-criterion-rubric"), {
      target: { value: "Rubric text" },
    });
    fireEvent.click(screen.getByTestId("eval-criterion-create"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("create failed");
    });
  });

  it("EvaluationCriteriaTab toggles enabled state and surfaces toggle errors", async () => {
    vi.mocked(fetchEvalCriteria).mockResolvedValue({
      items: [{ ...CRITERION, enabled: true }],
    });
    renderTab(<EvaluationCriteriaTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-criterion-tone-friendly"),
      ).toBeInTheDocument();
    });

    vi.mocked(updateEvalCriterion).mockRejectedValue(
      new Error("toggle failed"),
    );
    fireEvent.click(screen.getByRole("button", { name: /^disable$/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("toggle failed");
    });
  });

  it("EvaluationCriteriaTab enables a disabled criterion", async () => {
    renderTab(<EvaluationCriteriaTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-criterion-tone-friendly"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /^enable$/i }));
    await waitFor(() => {
      expect(updateEvalCriterion).toHaveBeenCalled();
    });
  });

  it("EvaluationCriteriaTab surfaces non-Error create failures", async () => {
    vi.mocked(createEvalCriterion).mockRejectedValue("save failed");
    renderTab(<EvaluationCriteriaTab />);
    await waitFor(() => {
      expect(screen.getByTestId("eval-criterion-slug")).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-criterion-slug"), {
      target: { value: "slug" },
    });
    fireEvent.change(screen.getByTestId("eval-criterion-label"), {
      target: { value: "Label" },
    });
    fireEvent.change(screen.getByTestId("eval-criterion-rubric"), {
      target: { value: "Rubric" },
    });
    fireEvent.click(screen.getByTestId("eval-criterion-create"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to save criterion/i,
      );
    });
  });

  it("EvaluationCriteriaTab surfaces non-Error load failures", async () => {
    vi.mocked(fetchEvalCriteria).mockRejectedValue("criteria-fail");
    renderTab(<EvaluationCriteriaTab />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("EvaluationCriteriaTab surfaces non-Error toggle failures", async () => {
    renderTab(<EvaluationCriteriaTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-criterion-tone-friendly"),
      ).toBeInTheDocument();
    });
    vi.mocked(updateEvalCriterion).mockRejectedValue("toggle failed");
    fireEvent.click(screen.getByRole("button", { name: /^enable$/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to save criterion/i,
      );
    });
  });

  it("EvaluationDashboardTab tolerates missing timeseries fields and toggles area to line", async () => {
    vi.mocked(fetchEvalTimeseries).mockResolvedValue({
      points: undefined as unknown as [],
      available_metrics: undefined as unknown as string[],
    });
    localStorage.setItem(
      "vecinita.eval.dashboard.v1",
      JSON.stringify({
        collapsedPanels: {},
        selectedMetrics: ["faithfulness"],
        chartType: "area",
        showThresholds: true,
      }),
    );
    renderTab(<EvaluationDashboardTab />);
    await waitFor(() => {
      expect(screen.getByTestId("eval-chart-type-toggle")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-chart-type-toggle"));
    expect(screen.getByTestId("evaluation-dashboard-tab")).toBeInTheDocument();
  });
});

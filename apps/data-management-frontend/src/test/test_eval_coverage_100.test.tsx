import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider } from "vecinita-frontend-ui";

import { type EvalRunDetailApi } from "@/api/admin";
import { AuthProvider } from "@/auth/AuthContext";
import { EvaluationCompareView } from "@/evaluation/EvaluationCompareView";
import { EvaluationPlaygroundTab } from "@/evaluation/EvaluationPlaygroundTab";

import { fetchInputUrl } from "./fetch-mock";
import { renderAppRoutesReady } from "./renderAppHelpers";

const RUN_A_ID = "00000000-0000-0000-0000-0000000000aa";
const RUN_B_ID = "00000000-0000-0000-0000-0000000000bb";

const LIST_TWO_RUNS = {
  items: [
    {
      run_id: RUN_A_ID,
      status: "completed",
      metrics_summary: {
        retrieval_relevance: 0.91,
        faithfulness: 0.85,
        answer_relevancy: 0.8,
        latency_p95_ms: 3200,
      },
    },
    {
      run_id: RUN_B_ID,
      status: "completed",
      metrics_summary: {
        retrieval_relevance: 0.88,
        faithfulness: 0.55,
        answer_relevancy: 0.72,
        latency_p95_ms: 4100,
      },
    },
  ],
  page: 1,
  page_size: 20,
  total_count: 2,
};

function detailBody(runId: string): EvalRunDetailApi {
  return {
    run_id: runId,
    status: "completed",
    metrics_summary:
      runId === RUN_A_ID
        ? LIST_TWO_RUNS.items[0].metrics_summary
        : LIST_TWO_RUNS.items[1].metrics_summary,
    items: [
      {
        case_id: "community-food-pantry",
        locale: "en",
        question: "When are food pantry hours updated?",
        retrieved_urls: [],
        answer: runId === RUN_A_ID ? "Answer A" : "Answer B",
        metrics: {
          retrieval_pass: true,
          faithfulness: runId === RUN_A_ID ? 0.85 : 0.55,
          answer_relevancy: 0.8,
          latency_ms: 1000,
        },
      },
    ],
  };
}

function defaultEvalFetch(
  url: string,
): Response | { ok: boolean; json: () => Promise<unknown> } {
  if (url.includes("/internal/v1/eval/criteria")) {
    return { ok: true, json: async () => ({ items: [] }) };
  }
  if (url.includes("/internal/v1/eval/config-presets")) {
    return { ok: true, json: async () => ({ items: [] }) };
  }
  if (url.includes("/internal/v1/models/ollama")) {
    return {
      ok: true,
      json: async () => ({
        items: [{ model_id: "qwen2.5:1.5b-instruct", available: true }],
      }),
    };
  }
  if (url.includes("/internal/v1/eval/runs/timeseries")) {
    return {
      ok: true,
      json: async () => ({ points: [], available_metrics: [] }),
    };
  }
  if (url.includes(`/internal/v1/eval/runs/${RUN_A_ID}`)) {
    return { ok: true, json: async () => detailBody(RUN_A_ID) };
  }
  if (url.includes(`/internal/v1/eval/runs/${RUN_B_ID}`)) {
    return { ok: true, json: async () => detailBody(RUN_B_ID) };
  }
  if (url.includes("/internal/v1/eval/runs/")) {
    return { ok: true, json: async () => detailBody(RUN_A_ID) };
  }
  if (url.includes("/internal/v1/eval/runs")) {
    return { ok: true, json: async () => LIST_TWO_RUNS };
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

function renderWithProviders(ui: ReactElement) {
  const wrapper = ({ children }: { children: ReactNode }) => (
    <LocaleProvider>
      <AuthProvider>
        <MemoryRouter>{children}</MemoryRouter>
      </AuthProvider>
    </LocaleProvider>
  );
  return render(ui, { wrapper });
}

describe("eval coverage gaps", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("EvaluationPage renders compare view when two runs are selected", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-history")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-compare-toggle"));
    fireEvent.change(screen.getByTestId("eval-compare-run-a-select"), {
      target: { value: RUN_A_ID },
    });
    fireEvent.change(screen.getByTestId("eval-compare-run-b-select"), {
      target: { value: RUN_B_ID },
    });

    await waitFor(() => {
      expect(screen.getByTestId("evaluation-compare")).toBeInTheDocument();
    });
  });

  it("EvaluationPage clears compare data when compare fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (
          url.includes(`/internal/v1/eval/runs/${RUN_B_ID}`) ||
          url.includes(`/internal/v1/eval/runs/${RUN_A_ID}`)
        ) {
          return Promise.resolve({ ok: false, status: 500 });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );

    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-history")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("eval-compare-toggle"));
    fireEvent.change(screen.getByTestId("eval-compare-run-a-select"), {
      target: { value: RUN_A_ID },
    });
    fireEvent.change(screen.getByTestId("eval-compare-run-b-select"), {
      target: { value: RUN_B_ID },
    });

    await waitFor(() => {
      expect(
        screen.queryByTestId("evaluation-compare"),
      ).not.toBeInTheDocument();
    });
  });

  it("EvaluationPage selects run from ?run= search param", async () => {
    await renderAppRoutesReady(`/evaluation?run=${RUN_B_ID}`);
    await waitFor(() => {
      expect(screen.getByText("Answer B")).toBeInTheDocument();
    });
  });

  it("EvaluationCompareView handles null aggregate metrics and missing item A", () => {
    renderWithProviders(
      <EvaluationCompareView
        runA={{
          run_id: RUN_A_ID,
          status: "completed",
          metrics_summary: {
            faithfulness: null,
            retrieval_relevance: null,
          },
          items: [],
        }}
        runB={{
          run_id: RUN_B_ID,
          status: "completed",
          metrics_summary: {
            faithfulness: 0.9,
            retrieval_relevance: 0.95,
          },
          items: [
            {
              case_id: "only-b",
              locale: "en",
              question: "Only in B?",
              retrieved_urls: [],
              answer: "B answer",
              metrics: {
                retrieval_pass: true,
                faithfulness: 0.9,
                answer_relevancy: 0.88,
                latency_ms: 500,
              },
            },
          ],
        }}
      />,
    );

    expect(screen.getByTestId("evaluation-compare")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.getByText("B answer")).toBeInTheDocument();
  });

  it("EvaluationCompareView shows positive faithfulness delta without regression styling", () => {
    renderWithProviders(
      <EvaluationCompareView
        runA={{
          run_id: RUN_A_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.5, retrieval_relevance: 0.5 },
          items: [
            {
              case_id: "improved",
              locale: "en",
              question: "Improved?",
              retrieved_urls: [],
              answer: "A",
              metrics: {
                retrieval_pass: true,
                faithfulness: 0.5,
                answer_relevancy: 0.5,
                latency_ms: 100,
              },
            },
          ],
        }}
        runB={{
          run_id: RUN_B_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.9, retrieval_relevance: 0.95 },
          items: [
            {
              case_id: "improved",
              locale: "en",
              question: "Improved?",
              retrieved_urls: [],
              answer: "B",
              metrics: {
                retrieval_pass: true,
                faithfulness: 0.9,
                answer_relevancy: 0.88,
                latency_ms: 100,
              },
            },
          ],
        }}
      />,
    );

    expect(
      screen.getByTestId("eval-compare-metric-faithfulness"),
    ).toHaveTextContent("+0.40");
    expect(
      screen.queryByTestId("eval-compare-regression-improved"),
    ).not.toBeInTheDocument();
  });

  it("EvaluationPlaygroundTab surfaces preset and model load failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({ ok: false, status: 503 });
        }
        if (url.includes("/internal/v1/models/ollama")) {
          return Promise.reject(new Error("models offline"));
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );

    renderWithProviders(<EvaluationPlaygroundTab />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /503|models offline/i,
      );
    });
  });

  it("EvaluationPlaygroundTab falls back when model list is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ items: [] }),
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );

    renderWithProviders(<EvaluationPlaygroundTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-model-id"),
      ).toBeInTheDocument();
    });
  });

  it("EvaluationCompareView omits per-row scores when faithfulness is null", () => {
    renderWithProviders(
      <EvaluationCompareView
        runA={{
          run_id: RUN_A_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.8, retrieval_relevance: 0.9 },
          items: [
            {
              case_id: "null-faith",
              locale: "en",
              question: "Null faith?",
              retrieved_urls: [],
              answer: "A",
              metrics: {
                retrieval_pass: true,
                faithfulness: null,
                answer_relevancy: null,
                latency_ms: 100,
              },
            },
          ],
        }}
        runB={{
          run_id: RUN_B_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.9, retrieval_relevance: 0.95 },
          items: [
            {
              case_id: "null-faith",
              locale: "en",
              question: "Null faith?",
              retrieved_urls: [],
              answer: "B",
              metrics: {
                retrieval_pass: true,
                faithfulness: null,
                answer_relevancy: null,
                latency_ms: 100,
              },
            },
          ],
        }}
      />,
    );

    expect(
      screen.queryByTestId("eval-compare-regression-null-faith"),
    ).not.toBeInTheDocument();
  });

  it("EvaluationPlaygroundTab surfaces translated clone failure for non-Error rejections", async () => {
    const presetId = "00000000-0000-0000-0000-0000000000cc";
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (
            url.includes(
              `/internal/v1/eval/config-presets/${presetId}/clone`,
            ) &&
            method === "POST"
          ) {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("clone offline");
          }
          if (url.includes("/internal/v1/eval/config-presets")) {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                items: [
                  {
                    preset_id: presetId,
                    version: 1,
                    name: "shared preset",
                    config: {
                      top_k: 7,
                      min_retrieval_score: 0.2,
                      system_prompt: "Preset prompt",
                      max_tokens: 256,
                      temperature: 0.2,
                      corpus_profile: "staging",
                      criteria_ids: [],
                      judge_temperature: 0.2,
                      model_id: "qwen2.5:1.5b-instruct",
                    },
                    shared: true,
                    owner_id: "33333333-3333-3333-3333-333333333333",
                    created_at: "2026-07-01T10:00:00Z",
                    updated_at: "2026-07-01T10:00:00Z",
                  },
                ],
              }),
            });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );

    renderWithProviders(<EvaluationPlaygroundTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: presetId },
    });
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-clone"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-preset-clone"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to clone preset|clone offline/i,
      );
    });
  });

  it("EvaluationPage ignores unknown run query param", async () => {
    await renderAppRoutesReady(
      "/evaluation?run=00000000-0000-0000-0000-0000000000ff",
    );
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-history")).toBeInTheDocument();
    });
    expect(screen.queryByText("Answer B")).not.toBeInTheDocument();
  });

  it("EvaluationPage hides compare view when toggled closed", async () => {
    await renderAppRoutesReady("/evaluation");
    await waitFor(() => {
      expect(screen.getByTestId("eval-compare-toggle")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-compare-toggle"));
    fireEvent.change(screen.getByTestId("eval-compare-run-a-select"), {
      target: { value: RUN_A_ID },
    });
    fireEvent.change(screen.getByTestId("eval-compare-run-b-select"), {
      target: { value: RUN_B_ID },
    });
    await waitFor(() => {
      expect(screen.getByTestId("evaluation-compare")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-compare-toggle"));
    expect(screen.queryByTestId("evaluation-compare")).not.toBeInTheDocument();
  });

  it("EvaluationPlaygroundTab runs without onRunCreated callback", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            return Promise.resolve({
              ok: true,
              json: async () => ({
                run_id: RUN_B_ID,
                status: "pending",
                created_at: "2026-07-02T12:00:00Z",
              }),
            });
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );

    renderWithProviders(<EvaluationPlaygroundTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-run-button"),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(screen.getByTestId("eval-playground-last-run")).toHaveTextContent(
        RUN_B_ID,
      );
    });
  });

  it("EvaluationPlaygroundTab clears preset selection and switches corpus profile", async () => {
    const presetId = "00000000-0000-0000-0000-0000000000cc";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/eval/config-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              items: [
                {
                  preset_id: presetId,
                  version: 1,
                  name: "shared preset",
                  config: {
                    top_k: 7,
                    min_retrieval_score: 0.2,
                    system_prompt: "Preset prompt",
                    max_tokens: 256,
                    temperature: 0.2,
                    corpus_profile: "staging",
                    criteria_ids: [],
                    judge_temperature: 0.2,
                    model_id: "qwen2.5:1.5b-instruct",
                  },
                  shared: true,
                  owner_id: "33333333-3333-3333-3333-333333333333",
                  created_at: "2026-07-01T10:00:00Z",
                  updated_at: "2026-07-01T10:00:00Z",
                },
              ],
            }),
          });
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );

    renderWithProviders(<EvaluationPlaygroundTab />);
    await waitFor(() => {
      expect(
        screen.getByTestId("eval-playground-preset-select"),
      ).toBeInTheDocument();
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: presetId },
    });
    fireEvent.change(screen.getByTestId("eval-playground-preset-select"), {
      target: { value: "" },
    });
    fireEvent.change(
      document.getElementById("eval-playground-corpus-profile")!,
      {
        target: { value: "staging" },
      },
    );
    expect(
      document.getElementById("eval-playground-corpus-profile"),
    ).toHaveValue("staging");
  });

  it("EvaluationPlaygroundTab uses translated errors for non-Error rejections", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
          const url = fetchInputUrl(input);
          const method = (init?.method ?? "GET").toUpperCase();
          if (url.includes("/internal/v1/eval/runs") && method === "POST") {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("offline");
          }
          if (url.includes("/internal/v1/eval/config-presets")) {
            // eslint-disable-next-line @typescript-eslint/prefer-promise-reject-errors -- branch: non-Error catch fallback
            return Promise.reject("presets offline");
          }
          return Promise.resolve(defaultEvalFetch(url));
        }),
    );

    renderWithProviders(<EvaluationPlaygroundTab />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to load presets|presets offline/i,
      );
    });

    fireEvent.click(screen.getByTestId("eval-playground-run-button"));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /Failed to start playground run/i,
      );
    });
  });

  it("EvaluationCompareView shows zero delta without destructive styling", () => {
    renderWithProviders(
      <EvaluationCompareView
        runA={{
          run_id: RUN_A_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.8, retrieval_relevance: 0.9 },
          items: [],
        }}
        runB={{
          run_id: RUN_B_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.8, retrieval_relevance: 0.9 },
          items: [],
        }}
      />,
    );
    expect(
      screen.getByTestId("eval-compare-metric-faithfulness"),
    ).toHaveTextContent("0.00");
  });

  it("EvaluationCompareView skips regression when run B stays above threshold", () => {
    renderWithProviders(
      <EvaluationCompareView
        runA={{
          run_id: RUN_A_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.75, retrieval_relevance: 0.9 },
          items: [
            {
              case_id: "stable",
              locale: "en",
              question: "Stable?",
              retrieved_urls: [],
              answer: "A",
              metrics: {
                retrieval_pass: true,
                faithfulness: 0.75,
                answer_relevancy: 0.8,
                latency_ms: 100,
              },
            },
          ],
        }}
        runB={{
          run_id: RUN_B_ID,
          status: "completed",
          metrics_summary: { faithfulness: 0.78, retrieval_relevance: 0.9 },
          items: [
            {
              case_id: "stable",
              locale: "en",
              question: "Stable?",
              retrieved_urls: [],
              answer: "B",
              metrics: {
                retrieval_pass: true,
                faithfulness: 0.78,
                answer_relevancy: 0.82,
                latency_ms: 100,
              },
            },
          ],
        }}
      />,
    );
    expect(
      screen.queryByTestId("eval-compare-regression-stable"),
    ).not.toBeInTheDocument();
  });

  it("EvaluationPlaygroundTab ignores stale model load errors after unmount", async () => {
    let releaseModels: (() => void) | undefined;
    const modelsGate = new Promise<void>((resolve) => {
      releaseModels = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((input: RequestInfo | URL) => {
        const url = fetchInputUrl(input);
        if (url.includes("/internal/v1/models/ollama")) {
          return modelsGate.then(() =>
            Promise.resolve({
              ok: true,
              json: async () => ({
                items: [{ model_id: "qwen2.5:1.5b-instruct", available: true }],
              }),
            }),
          );
        }
        return Promise.resolve(defaultEvalFetch(url));
      }),
    );

    const view = renderWithProviders(<EvaluationPlaygroundTab />);
    view.unmount();
    releaseModels?.();
    await Promise.resolve();
  });
});
